"""Second pass on the built assembly (compliance Phase 5): materials, appearance, properties,
named views and visibility configurations.

Linked parts don't carry their material or free properties into the assembly, and multi-lump
bodies come in split ("PC_FrontSlats (2)"), so the real body names are read from an eval of the
built file and each part's own material/appearance commands are replayed on them.
"""

from __future__ import annotations

import json
import logging
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

__all__ = ["FinishError", "finish_assembly"]

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PARTS = ROOT / "parts"
BUILD = ROOT / "build"
CLI = "solidcraft-cli"
META_KEY = "com.setsma.desk"
_COPIED = ("material.assign", "appearance.assign")

# Camera: yaw 0 looks from the front (-Y), radians; target/distance in mm.
VIEWS: tuple[tuple[str, list[float], float, float, float], ...] = (
    ("Overview", [0, 0, 800], 0.6, 0.45, 3200),
    ("Front", [0, 0, 900], 0.0, 0.1, 2900),
    ("Back", [0, 300, 900], 3.1416, 0.2, 2900),
    ("SideRailJoint_R", [900, 0, 690], -1.2, 0.35, 700),
    ("SideRailJoint_L", [-900, 0, 690], 1.2, 0.35, 700),
    ("SpeakerMount_R", [880, 320, 1190], -1.57, 0.15, 500),
    ("UnderDesk", [0, 0, 500], 0.4, -0.3, 1900),
    ("LaptopArm", [560, 150, 950], -0.7, 0.35, 1000),
    # Framed for the matching display rows below (Rails only, Desk only, Desk + rails).
    ("Rails", [0, 250, 1000], 0.6, 0.3, 2300),
    ("RailsBack", [0, 250, 1000], 2.6, 0.25, 2300),
    ("Desk", [0, 0, 450], 0.6, 0.4, 2500),
    ("DeskRails", [0, 100, 700], 0.6, 0.4, 2800),
)
# Visibility sets as configuration rows (SolidCraft has no display states): link groups suppressed.
DISPLAY_ROWS: Mapping[str, tuple[str, ...]] = {
    "Full": (),
    "Frame only": ("DSK-01", "MON-", "SPK-", "PC-", "INP-", "LAP-", "CHR-"),
    "No desktop": ("DSK-01",),
    "Monitors + speakers": ("DSK-", "HW-", "PC-", "INP-", "LAP-", "CHR-", "FRM-05"),
    "Rails only": ("DSK-", "FRM-05", "MON-", "SPK-", "PC-", "INP-", "LAP-", "CHR-"),
    "Desk only": ("FRM-", "HW-", "MON-", "SPK-", "PC-", "INP-", "LAP-", "CHR-"),
    "Desk + rails": ("MON-", "SPK-", "PC-", "INP-", "LAP-", "CHR-"),
    "No chair": ("CHR-",),
}


class FinishError(Exception):
    """The finishing pass could not be generated or applied."""


def _cmd(command: str, **params: object) -> dict[str, object]:
    return {"command": command, "params": params}


def _run(args: Sequence[str]) -> None:
    result = subprocess.run([CLI, *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise FinishError(result.stderr.strip() or result.stdout.strip())


def _part_source(component: str) -> Path:
    stem = component.replace(" ", "_")
    for folder in (PARTS / "src", PARTS / "lib" / "src"):
        if (folder / f"{stem}.json").is_file():
            return folder / f"{stem}.json"
    raise FinishError(f"no build script for component {component!r}")


def _read_commands(path: Path) -> list[dict[str, object]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))["commands"]
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise FinishError(f"cannot read {path}: {exc}") from exc


def _real_bodies(eval_json: Path) -> list[str]:
    """Body definitions in the assembly (extra placements carry an occurrence path suffix)."""
    bodies = json.loads(eval_json.read_text(encoding="utf-8"))["bodies"]
    return [b["name"] for b in bodies if "/" not in b["name"]]


def _expand(names: Iterable[str], real: Sequence[str]) -> list[str]:
    return [r for n in names for r in real if r == n or r.startswith(f"{n} (")]


def _part_commands(component: str, real: Sequence[str]) -> list[dict[str, object]]:
    commands, props = [], {}
    for c in _read_commands(_part_source(component)):
        params = c["params"]
        if c["command"] in _COPIED and params.get("bodies"):
            commands.append(_cmd(c["command"], **{**params, "bodies": _expand(params["bodies"], real)}))
        elif c["command"] == "document.metadata.set":
            meta = params.get("values", {}).get(META_KEY) or {}
            props = {k: str(meta[k]) for k in ("Material", "ReleaseState") if k in meta}
    if props:
        commands.append(_cmd("component.metadata.set", component=component, properties=props))
    return commands


def _view_commands() -> list[dict[str, object]]:
    return [_cmd("view.save", name=n, camera={"target": t, "yaw": y, "pitch": p, "distance": d})
            for n, t, y, p, d in VIEWS]


def _config_commands(links: Sequence[str]) -> list[dict[str, object]]:
    commands = [_cmd("config.configure", features=list(links))]
    for row, prefixes in DISPLAY_ROWS.items():
        values = {f"suppress:{f}": f.startswith(prefixes) if prefixes else False for f in links}
        commands.append(_cmd("config.row", name=row, values=values))
    return [*commands, _cmd("config.activate", row="Full")]


def _group_commands(links: Sequence[str]) -> list[dict[str, object]]:
    """One timeline folder per group prefix (DSK, FRM, HW, ...), plus the skeleton sketch."""
    groups: dict[str, list[str]] = {"REF skeleton": ["SKL_Eye"]}
    for link in links:
        groups.setdefault(f"{link.split('-')[0]} parts", []).append(link)
    return [_cmd("timeline.group", name=name, features=features) for name, features in groups.items()]


def finish_assembly(design: Path, components: Sequence[str]) -> None:
    """Apply materials, appearance, properties, views, display rows and timeline groups in place."""
    # Scratch files are named after the design, so the main and variant builds can run in parallel.
    script_out, eval_out = BUILD / f"{design.stem}_finish.json", BUILD / f"{design.stem}_eval.json"
    BUILD.mkdir(exist_ok=True)
    _run(["eval", str(design), "--json-out", str(eval_out)])
    real = _real_bodies(eval_out)
    links = list(dict.fromkeys(components))
    commands = [c for comp in links for c in _part_commands(comp, real)]
    commands += _view_commands() + _config_commands(links) + _group_commands(links)
    script_out.write_text(json.dumps({"commands": commands}, indent=1), encoding="utf-8")
    log.info("wrote %s (%d commands)", script_out.relative_to(ROOT), len(commands))
    _run(["run", str(script_out), "--in", str(design), "--save", str(design), "--quiet"])
