"""Generate and build the desk assembly from linked part files (compliance Phase 4).

    python tools/build_assembly.py                 # writes build/assembly.json, builds build/desk_rails_new.solidcraft
    python tools/build_assembly.py --out X.solidcraft

Every part is inserted as a linked component under its group and placed with a planar joint
from the root origin whose x, y, yaw and z offset are skeleton-parameter expressions
(PROJECT.md "Standard placement"). Hardware placements come from skeleton/hw_placements.json.
The script is scaffolding: once the assembly is built, the design file is the source of truth.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from assembly_finish import FinishError, finish_assembly

__all__ = ["BuildError", "Occurrence", "OCCURRENCES", "build_script", "component_name", "main"]

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PARTS = ROOT / "parts"
SKELETON = ROOT / "skeleton" / "params.json"
HW_PLACEMENTS = ROOT / "skeleton" / "hw_placements.json"
TEMPLATE = PARTS / "_template.json"
SCRIPT_OUT = ROOT / "build" / "assembly.json"
DEFAULT_OUT = ROOT / "build" / "desk_rails_new.solidcraft"
CLI = "solidcraft-cli"
UP, EAST = [0, 0, 1], [1, 0, 0]

GROUPS = (
    ("DSK-00 Desk frame", "DeskHaus Apex Pro 4-leg frame and desktop"),
    ("FRM-00 Monitor rail frame", "Misumi HFS5 rail frame and modesty panel"),
    ("HW-00 Frame hardware", "Misumi plates, gussets, standoffs and screws"),
    ("MON-00 Monitors", "Main 32in and side 27in portrait monitors"),
    ("SPK-00 Speakers", "Klipsch R-40M speakers on swivel mounts"),
    ("PC-00 PC under-desk", "Fractal North case, slat front and strap"),
    ("INP-00 Input devices", "Mouse pad, mouse and split keyboard"),
    ("REF-00 Skeleton", "Layout datums (Eye point)"),
)


class BuildError(Exception):
    """The assembly script could not be generated or built."""


@dataclass(frozen=True)
class Occurrence:
    """One placed occurrence of a part file: label, file, group and world placement expressions."""

    label: str
    part: str
    group: str
    x: str
    y: str
    z: str
    yaw: str = "0 deg"
    zl: tuple[float, float, float] = (0, 0, 1)
    xl: tuple[float, float, float] = (1, 0, 0)


def _occ(label: str, part: str, group: str, x: str, y: str, z: str, yaw: str = "0 deg") -> Occurrence:
    # Fixed half turns go into the part frame (local -X lands on world +X); only parametric
    # yaws use the joint value.
    if yaw == "180 deg":
        return Occurrence(label, part, group, x, y, z, "0 deg", xl=(-1, 0, 0))
    return Occurrence(label, part, group, x, y, z, yaw)


_DSK, _FRM, _MON, _SPK, _PC, _INP = (g for g, _ in GROUPS[:2] + GROUPS[3:7])
_LEG_X = "(frame_w/2 - leg_inset)"
_CH = "(ch_bar_gap/2 + ch_bar_w/2)"

OCCURRENCES: tuple[Occurrence, ...] = (
    _occ("Desktop", "DSK-01_Desktop", _DSK, "0 mm", "desk_y_off", "frame_top"),
    _occ("TopSupport_R", "DSK-02_TopSupport", _DSK, "frame_w/2", "0 mm", "frame_top"),
    _occ("TopSupport_L", "DSK-02_TopSupport", _DSK, "-frame_w/2", "0 mm", "frame_top", "180 deg"),
    _occ("ChannelBar_BackOuter", "DSK-03_ChannelBar", _DSK, "0 mm", f"ch_y_off + leg_yc + {_CH}", "frame_top"),
    _occ("ChannelBar_BackInner", "DSK-03_ChannelBar", _DSK, "0 mm", f"ch_y_off + leg_yc - {_CH}", "frame_top"),
    _occ("ChannelBar_FrontOuter", "DSK-03_ChannelBar", _DSK, "0 mm", f"ch_y_off - leg_yc - {_CH}", "frame_top"),
    _occ("ChannelBar_FrontInner", "DSK-03_ChannelBar", _DSK, "0 mm", f"ch_y_off - leg_yc + {_CH}", "frame_top"),
    _occ("Leg_RB", "DSK-04_Leg", _DSK, _LEG_X, "ch_y_off + leg_yc", "frame_top"),
    _occ("Leg_RF", "DSK-04_Leg", _DSK, _LEG_X, "ch_y_off - leg_yc", "frame_top"),
    _occ("Leg_LB", "DSK-04_Leg", _DSK, f"-{_LEG_X}", "ch_y_off + leg_yc", "frame_top", "180 deg"),
    _occ("Leg_LF", "DSK-04_Leg", _DSK, f"-{_LEG_X}", "ch_y_off - leg_yc", "frame_top", "180 deg"),
    _occ("Foot_R", "DSK-05_Foot", _DSK, _LEG_X, "ch_y_off", "0 mm"),
    _occ("Foot_L", "DSK-05_Foot", _DSK, f"-{_LEG_X}", "ch_y_off", "0 mm", "180 deg"),
    _occ("Upright_L", "FRM-01_Upright_4040", _FRM, "-up_xc", "up_y", "frame_top - up_below"),
    _occ("Upright_R", "FRM-01_Upright_4040", _FRM, "up_xc", "up_y", "frame_top - up_below"),
    _occ("Crossbar_Low", "FRM-02_Crossbar_2040", _FRM, "0 mm", "stile_y", "desk_h + bar1_z"),
    _occ("Crossbar_High", "FRM-02_Crossbar_2040", _FRM, "0 mm", "stile_y", "desk_h + bar2_z"),
    _occ("SideRail_L", "FRM-03L_SideRail_L_4040", _FRM, "-frame_w/2", "0 mm", "frame_top"),
    _occ("SideRail_R", "FRM-03R_SideRail_R_4040", _FRM, "frame_w/2", "0 mm", "frame_top"),
    _occ("Stile_Main", "FRM-04_Stile_2040", _FRM, "m1_x", "stile_y", "desk_h + bar1_z + rail_l/2"),
    _occ("Stile_Side", "FRM-04_Stile_2040", _FRM, "m3_x", "stile_y", "desk_h + bar1_z + rail_l/2"),
    _occ("ModestyPanel", "FRM-05_Modesty_panel", _FRM, "0 mm", "stile_y + rail_s/2 + pnl_back_gap",
         "frame_top - pnl_drop"),
    _occ("Monitor_Main", "MON-01_Monitor_Main_32in", _MON, "m1_x", "stile_front - m1_off",
         "desk_h + mon_clearance + m1_h/2 + m1_vesa_dz"),
    _occ("Monitor_Side", "MON-02_Monitor_Side_27in", _MON, "m3_x", "stile_front - m3_off",
         "desk_h + m3_bot + m3_h/2", "m3_yaw"),
    _occ("Speaker_L", "SPK-01_R40M_Speaker", _SPK, "-spk_px", "spk_py", "desk_h + spk_pz", "spk_yaw"),
    _occ("Speaker_R", "SPK-01_R40M_Speaker", _SPK, "spk_px", "spk_py", "desk_h + spk_pz", "-spk_yaw"),
    _occ("SpkFlange_L", "SPK-02_SpkMount_Flange", _SPK, "-up_xc", "up_y - rail_l/2", "desk_h + spk_pz"),
    _occ("SpkFlange_R", "SPK-02_SpkMount_Flange", _SPK, "up_xc", "up_y - rail_l/2", "desk_h + spk_pz"),
    # 10 mm / 4 mm: fixed block geometry of the swivel mount (SPK-03 description)
    _occ("SpkBlock_L", "SPK-03_SpkMount_Block", _SPK, "-(up_xc + rail_l/2 + spk_px - 10 mm)/2",
         "up_y - rail_l/2 - 4 mm", "desk_h + spk_pz"),
    _occ("SpkBlock_R", "SPK-03_SpkMount_Block", _SPK, "(up_xc + rail_l/2 + spk_px - 10 mm)/2",
         "up_y - rail_l/2 - 4 mm", "desk_h + spk_pz"),
    # 8 mm: swivel ball centre behind the speaker back (fixed vendor geometry)
    _occ("SpkSwivel_L", "SPK-04_SpkMount_Swivel", _SPK, "-spk_px", "spk_py + 8 mm", "desk_h + spk_pz"),
    _occ("SpkSwivel_R", "SPK-04_SpkMount_Swivel", _SPK, "spk_px", "spk_py + 8 mm", "desk_h + spk_pz"),
    _occ("PC_Case", "PC-01_FractalNorth", _PC, "pc_x0 + pc_w/2", "0 mm", "pc_top"),
    _occ("PC_Slats", "PC-02_WalnutSlatFront", _PC, "pc_x0 + pc_w/2", "-pc_d/2 + slat_inset", "pc_top - pc_h/2"),
    _occ("PC_Strap", "PC-03_Strap", _PC, "pc_x0 + pc_w/2", "0 mm", "pc_top"),
    _occ("MousePad", "INP-01_MousePad", _INP, "pad_x", "pad_y", "desk_h"),
    _occ("Mouse", "INP-02_DeathAdderV3Pro", _INP, "pad_x", "pad_y", "desk_h + pad_t", "180 deg"),
    _occ("Keyboard_L", "INP-03_ErgoDoxEZ_Left", _INP, "m1_x - kb_gap/2 - kb_w", "desk_front + kb_front_gap", "desk_h"),
    _occ("Keyboard_R", "INP-04_ErgoDoxEZ_Right", _INP, "m1_x + kb_gap/2", "desk_front + kb_front_gap", "desk_h"),
)


def load_hw_occurrences(path: Path = HW_PLACEMENTS) -> list[Occurrence]:
    """Hardware occurrences solved from the legacy model (empty if the file isn't there yet)."""
    if not path.is_file():
        log.warning("no %s: building without hardware", path.relative_to(ROOT))
        return []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        return [
            Occurrence(r["name"], f"lib/{r['lib']}", GROUPS[2][0], r["x"], r["y"], r["z"],
                       r.get("yaw") or "0 deg", tuple(r["zl"]), tuple(r["xl"]))
            for r in rows
        ]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise BuildError(f"bad hardware placements in {path}: {exc}") from exc


def _cmd(command: str, **params: object) -> dict[str, object]:
    return {"command": command, "params": params}


def _template_commands() -> list[dict[str, object]]:
    try:
        return json.loads(TEMPLATE.read_text(encoding="utf-8"))["commands"]
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise BuildError(f"cannot read template {TEMPLATE}: {exc}") from exc


def component_name(part: str) -> str:
    stem = part.split("/")[-1]
    number, _, name = stem.partition("_")
    return f"{number} {name.replace('_', ' ')}"


def _skeleton_commands() -> list[dict[str, object]]:
    group = GROUPS[-1][0]
    return [
        _cmd("component.activate", component=group),
        _cmd("sketch.create", plane="XY", offset="desk_h + eye_above_desk", name="SKL_Eye"),
        _cmd("sketch.point", point=["m1_x", "desk_front - eye_back"]),
        _cmd("sketch.finish"),
        _cmd("component.activate", component=0),
    ]


def _placement_joint(occ: Occurrence, occurrence_name: str) -> dict[str, object]:
    return _cmd(
        "joint.create", type="planar", flip=True, name=f"J_{occ.label}",
        a={"occurrence": 0, "point": [0, 0, 0], "z": UP, "x": EAST},
        b={"occurrence": occurrence_name, "point": [0, 0, 0], "z": list(occ.zl), "x": list(occ.xl)},
        values=[occ.x, occ.y, occ.yaw], offset=occ.z,
        # Without an explicit angle SolidCraft adds a half turn when that turns b less.
        angle="0 deg",
    )


def build_script(occurrences: Sequence[Occurrence], parts_dir: Path = PARTS,
                 skeleton: Path = SKELETON) -> dict[str, object]:
    """The full command script: skeleton, groups, linked parts, placement joints."""
    commands = [*_template_commands(), _cmd("parameters.import", path=skeleton.as_posix())]
    commands += [_cmd("document.metadata.set", values={
        "part_number": "DESK-000", "description": "Desk rail system top-level assembly", "revision": "A"})]
    for i, (name, description) in enumerate(GROUPS):
        commands += [_cmd("component.create", name=name, parent=0, activate=False, grounded=i == 0),
                     _cmd("component.metadata.set", component=name, part_number=name.split()[0],
                          description=description, revision="A")]
    commands += _skeleton_commands()

    counts: dict[str, int] = {}
    joints = []
    for occ in occurrences:
        component = component_name(occ.part)
        reuse = component in counts
        counts[component] = counts.get(component, 0) + 1
        commands.append(_cmd("component.insert_design", path=(parts_dir / f"{occ.part}.solidcraft").as_posix(),
                             name=component, parent=occ.group, reuse=reuse))
        joints.append(_placement_joint(occ, f"{component}:{counts[component]}"))
    return {"commands": [*commands, *joints]}


def main(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    script = build_script([*OCCURRENCES, *load_hw_occurrences()])
    SCRIPT_OUT.write_text(json.dumps(script, indent=1), encoding="utf-8")
    log.info("wrote %s (%d commands)", SCRIPT_OUT.relative_to(ROOT), len(script["commands"]))
    result = subprocess.run([CLI, "run", str(SCRIPT_OUT), "--save", str(args.out), "--quiet"],
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        log.error("%s", result.stderr.strip() or result.stdout.strip())
        return 1
    log.info("saved %s", args.out)
    occurrences = [*OCCURRENCES, *load_hw_occurrences()]
    try:
        finish_assembly(args.out, [component_name(o.part) for o in occurrences])
    except FinishError as exc:
        log.error("finish pass failed: %s", exc)
        return 1
    log.info("finished %s", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
