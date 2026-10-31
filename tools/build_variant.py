"""Build a layout variant as its own assembly file, leaving the main design and parts untouched.

    python tools/build_variant.py desk_62x32           # variants/desk_62x32/variant.json -> its "out" file

A variant is `variants/<name>/variant.json`: {"description", "out", "overrides": {param: expression},
"speakers": "hung" | "laid"}. The build:
1. writes `variants/<name>/params.json` (the shared skeleton with the overrides; for "laid" speakers also the
   solved stand placement and the laptop tray height, computed by tools/spk_laid.py),
2. rebuilds the skeleton-driven parts into `variants/<name>/parts/` (others link the main `parts/` files),
3. builds and finishes the assembly from the main occurrence list, with the speaker group swapped for the
   laid layout (SPK-01 on its side on SPK-05 stands, no upright mounts).

Generated scripts that hold skeleton-computed pick points keep the main skeleton's values; that is right only
while those inputs (ts_*, pad_*, m3_*, pc_*) aren't overridden, which is checked.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import math
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import build_assembly
import regen_parts
import sightlines
import skeleton_values
import spk_laid
from assembly_finish import FinishError, finish_assembly
from build_assembly import Occurrence

__all__ = ["Variant", "VariantError", "laid_occurrences", "load_variant", "main"]

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
VARIANTS = ROOT / "variants"
CLI = "solidcraft-cli"
STAND_GEN = ROOT / "parts" / "src" / "SPK-05_gen.py"
STAND_PART = "SPK-05_SpkWedge"
HUNG_SPEAKER = ("Speaker_L", "Speaker_R", "SpkFlange_L", "SpkFlange_R", "SpkBlock_L", "SpkBlock_R",
                "SpkSwivel_L", "SpkSwivel_R")
HUNG_MOUNT_PARTS = ("SPK-02", "SPK-03", "SPK-04")  # upright mounts, unused by laid speakers
PICK_POINT_INPUTS = ("ts_", "pad_", "m3_", "pc_", "slat_")  # read by generators through skeleton_values


class VariantError(Exception):
    """The variant is malformed or failed to build."""


@dataclass(frozen=True)
class Variant:
    name: str
    description: str
    out: Path
    overrides: Mapping[str, str]
    speakers: str

    @property
    def folder(self) -> Path:
        return VARIANTS / self.name


def load_variant(name: str) -> Variant:
    path = VARIANTS / name / "variant.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        variant = Variant(name, data["description"], ROOT / data["out"], data["overrides"], data.get("speakers", "hung"))
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise VariantError(f"bad variant file {path}: {exc}") from exc
    if variant.speakers not in ("hung", "laid"):
        raise VariantError(f"{name}: speakers must be 'hung' or 'laid', not {variant.speakers!r}")
    stale = [p for p in variant.overrides if p.startswith(PICK_POINT_INPUTS)]
    if stale:
        raise VariantError(f"{name}: overriding {stale} would leave generator pick points stale")
    return variant


def _row(name: str, expression: str, comment: str, unit: str = "mm") -> dict[str, object]:
    return {"name": name, "expression": expression, "comment": comment, "favorite": False, "unit": unit}


def _write_skeleton(path: Path, overrides: Mapping[str, str], extra: Sequence[Mapping[str, object]] = ()) -> None:
    rows = json.loads(regen_parts.SKELETON.read_text(encoding="utf-8"))
    names = {r["name"] for r in rows}
    unknown = set(overrides) - names
    if unknown:
        raise VariantError(f"unknown parameters: {sorted(unknown)}")
    rows = [{**r, "expression": overrides.get(r["name"], r["expression"])} for r in rows]
    path.write_text(json.dumps([*rows, *extra], indent=1), encoding="utf-8")


def _stand_constants() -> dict[str, float]:
    spec = importlib.util.spec_from_file_location("spk05_gen", STAND_GEN)
    if spec is None or spec.loader is None:
        raise VariantError(f"cannot load {STAND_GEN}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.STAND)


def _laid_rows(layout: spk_laid.LaidLayout) -> list[dict[str, object]]:
    src = "computed by tools/build_variant.py (spk_laid.solve); re-run the build after layout changes"
    return [
        _row("spk_st_w", f"{layout.st_w} mm", "Aperta300 stand width (SPK-05_gen.STAND)"),
        _row("spk_st_d", f"{layout.st_d} mm", "Aperta300 stand depth (SPK-05_gen.STAND)"),
        _row("spk_st_h", f"{layout.st_h} mm", "Aperta300 stand rear height (SPK-05_gen.STAND)"),
        _row("spk_st_tilt", f"{math.degrees(layout.tilt):.4f} deg", "Stand tilt, front up (SPK-05_gen.STAND)", "deg"),
        _row("spk_lay_x", f"{layout.x:.3f} mm", f"Laid speaker stand centre |X| (side monitor centre); {src}"),
        _row("spk_lay_y", f"{layout.y:.3f} mm", f"Laid speaker stand centre Y, back as far as the monitors allow; {src}"),
        _row("spk_lay_yaw", f"{math.degrees(layout.yaw):.4f} deg", f"Laid speaker toe-in toward the Eye; {src}", "deg"),
    ]


TRAY_STEP, TRAY_MAX = 5.0, 600.0  # mm


def _with_layout(v: Mapping[str, float], layout: spk_laid.LaidLayout, tray_z: float) -> dict[str, float]:
    return {**v, "lap_tray_z": tray_z, "spk_lay_x": layout.x, "spk_lay_y": layout.y, "spk_lay_yaw": layout.yaw,
            "spk_st_tilt": layout.tilt, "spk_st_w": layout.st_w, "spk_st_d": layout.st_d, "spk_st_h": layout.st_h}


def _laptop_hides(v: Mapping[str, float]) -> list[str]:
    """Targets (speakers, monitors) the laptop or its tray hides from the Eye (coarse 24x24 rays)."""
    return [t for t, items in sightlines.blockers(v, n=24).items()
            if not t.startswith("Laptop") and any(o.startswith("Laptop") for o, _ in items)]


def _solve_laid(variant: Variant, skeleton: Path) -> tuple[spk_laid.LaidLayout, float]:
    """Layout from the overridden skeleton, then the lowest laptop tray height that clears the right speaker
    and hides nothing from the Eye."""
    v = sightlines._derive(skeleton_values.values(skeleton))
    layout = spk_laid.solve(v, _stand_constants())
    tray_z = spk_laid.min_tray_z(v, layout, sightlines.laptop)
    while hidden := _laptop_hides(_with_layout(v, layout, tray_z)):
        tray_z += TRAY_STEP
        if tray_z > TRAY_MAX:
            raise VariantError(f"the laptop hides {hidden} at every tray height up to {TRAY_MAX} mm")
    return layout, tray_z


def write_skeleton(variant: Variant) -> Path:
    variant.folder.mkdir(parents=True, exist_ok=True)
    skeleton = variant.folder / "params.json"
    overrides = {**variant.overrides}
    if variant.speakers == "laid":
        overrides["spk_tilt"] = "0 deg"  # the stand tilts the speaker; SPK-01's own tilt is off
        _write_skeleton(skeleton, overrides)
        layout, tray_z = _solve_laid(variant, skeleton)
        overrides["lap_tray_z"] = f"{tray_z:.1f} mm"
        _write_skeleton(skeleton, overrides, _laid_rows(layout))
        log.info("laid speakers: stand centre x +/-%.1f, y %.1f, toe-in %.1f deg; laptop tray %.1f mm",
                 layout.x, layout.y, math.degrees(layout.yaw), tray_z)
    else:
        _write_skeleton(skeleton, overrides)
    return skeleton


def laid_occurrences(tilt: float) -> list[Occurrence]:
    """Speakers on their side (frame vectors from the tilt) on SPK-05 stands, both aimed by spk_lay_yaw."""
    spk = build_assembly.GROUPS[4][0]
    a, e, b = "spk_st_d/2", "(spk_mount_frac - 0.5)*spk_h", "spk_w/2*sin(spk_st_tilt)"
    psi = "spk_lay_yaw"
    stand_x = f"(spk_lay_x + {a}*sin({psi}))"
    stand_y = f"spk_lay_y + {a}*cos({psi})"
    spk_x = f"(spk_lay_x + {a}*sin({psi}) + {e}*cos({psi}) + {b}*sin({psi}))"
    spk_y = f"spk_lay_y + {a}*cos({psi}) - {e}*sin({psi}) + {b}*cos({psi})"
    spk_z = "desk_h + spk_st_h + spk_w/2*cos(spk_st_tilt)"
    out = []
    for side, tag, sign, yaw in ((spk_laid.LEFT, "L", "-", psi), (spk_laid.RIGHT, "R", "", f"-{psi}")):
        zl, xl = spk_laid.frame_vectors(side, tilt)
        out += [
            Occurrence(f"Speaker_{tag}", "SPK-01_R40M_Speaker", spk, f"{sign}{spk_x}", spk_y, spk_z, yaw,
                       tuple(zl), tuple(xl)),
            Occurrence(f"SpkStand_{tag}", STAND_PART, spk, f"{sign}{stand_x}", stand_y, "desk_h", yaw),
        ]
    return out


def occurrences(variant: Variant, values: Mapping[str, float]) -> list[Occurrence]:
    base = [*build_assembly.OCCURRENCES, *build_assembly.load_hw_occurrences()]
    if variant.speakers == "hung":
        return base
    return [o for o in base if o.label not in HUNG_SPEAKER] + laid_occurrences(values["spk_st_tilt"])


def regen(variant: Variant, skeleton: Path) -> dict[str, Path]:
    """Rebuild skeleton-driven parts privately; returns {part stem: frozen file} for every part."""
    sources = regen_parts.part_sources()
    regen_parts.refresh_generated(sources)
    unused = HUNG_MOUNT_PARTS if variant.speakers == "laid" else ()
    private = [s for s in sources if regen_parts._uses_skeleton(regen_parts._commands(s.script))
               and not s.stem.startswith(unused)]
    parts_dir = variant.folder / "parts"
    _, errors = regen_parts.regen_all(private, skeleton, parts_dir=parts_dir, hist=ROOT / "build" / variant.name,
                                      force=True)
    if errors:
        raise VariantError("part builds failed:\n  " + "\n  ".join(errors))
    shared = [s for s in sources if s not in private]
    stand = [s for s in shared if s.stem == STAND_PART]
    if stand and not (regen_parts.PARTS / stand[0].rel_out).is_file():
        regen_parts.regen_all(stand)  # new part: freeze it once in the main parts folder
    paths = {s.rel_out.with_suffix("").as_posix(): regen_parts.PARTS / s.rel_out for s in shared}
    paths.update({s.rel_out.with_suffix("").as_posix(): parts_dir / s.rel_out for s in private})
    log.info("%d parts rebuilt for %s, %d linked from parts/", len(private), variant.name, len(shared))
    return paths


def build(variant: Variant) -> None:
    skeleton = write_skeleton(variant)
    values = skeleton_values.values(skeleton)
    paths = regen(variant, skeleton)
    occs = occurrences(variant, values)
    script = build_assembly.build_script(occs, skeleton=skeleton, part_path=lambda part: paths[part])
    script_path = variant.folder / "assembly.json"
    script_path.write_text(json.dumps(script, indent=1), encoding="utf-8")
    result = subprocess.run([CLI, "run", str(script_path), "--save", str(variant.out), "--quiet"],
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise VariantError((result.stderr or result.stdout).strip()[:600])
    try:
        finish_assembly(variant.out, [build_assembly.component_name(o.part) for o in occs])
    except FinishError as exc:
        raise VariantError(f"finish pass failed: {exc}") from exc
    log.info("saved %s", variant.out.relative_to(ROOT))


def main(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("name", help="folder under variants/")
    parser.add_argument("--skeleton-only", action="store_true", help="write params.json and print the layout")
    args = parser.parse_args(argv)
    try:
        variant = load_variant(args.name)
        if args.skeleton_only:
            write_skeleton(variant)
        else:
            build(variant)
    except (VariantError, spk_laid.LayoutError, skeleton_values.SkeletonError, regen_parts.RegenError) as exc:
        log.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
