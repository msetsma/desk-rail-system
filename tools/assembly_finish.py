"""Second pass on a built assembly (tools/build_assembly.py, tools/build_variant.py): materials,
appearance, properties, named views, visibility configurations and timeline folders.

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

import skeleton_values

__all__ = ["FinishError", "finish_assembly", "skeleton_views"]

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PARTS = ROOT / "parts"
BUILD = ROOT / "build"
CLI = "solidcraft-cli"
META_KEY = "com.setsma.desk"
_COPIED = ("material.assign", "appearance.assign")

# Camera: yaw 0 looks from the front (-Y), radians; target/distance in mm. Views centred on the frame
# keep fixed targets; detail views follow the skeleton (frame width, stile and mount positions), so a
# variant with a different desk size frames the same features.
View = tuple[str, list[float], float, float, float]
FIXED_VIEWS: tuple[View, ...] = (
    ("Overview", [0, 0, 800], 0.6, 0.45, 3200),
    ("Front", [0, 0, 900], 0.0, 0.1, 2900),
    ("Back", [0, 300, 900], 3.1416, 0.2, 2900),
    ("UnderDesk", [0, 0, 500], 0.4, -0.3, 1900),
    # Framed for the matching display rows below (Rails only, Desk only, Desk + rails).
    ("Rails", [0, 250, 1000], 0.6, 0.3, 2300),
    ("RailsBack", [0, 250, 1000], 2.6, 0.25, 2300),
    ("Desk", [0, 0, 450], 0.6, 0.4, 2500),
    ("DeskRails", [0, 100, 700], 0.6, 0.4, 2800),
)
SIDE_RAIL_VIEW_DZ = 55.0  # target above the frame top: middle of the side-rail to top-support joint
VIEW_ORDER = ("Overview", "Front", "Back", "SideRailJoint_R", "SideRailJoint_L", "SpeakerMount_R",
              "UnderDesk", "LaptopArm", "Rails", "RailsBack", "Desk", "DeskRails")


def skeleton_views(v: Mapping[str, float]) -> tuple[View, ...]:
    """All named views, detail targets computed from evaluated skeleton values `v` (mm)."""
    try:
        rail_z = v["frame_top"] + SIDE_RAIL_VIEW_DZ
        detail: tuple[View, ...] = (
            ("SideRailJoint_R", [v["frame_w"] / 2, 0, rail_z], -1.2, 0.35, 700),
            ("SideRailJoint_L", [-v["frame_w"] / 2, 0, rail_z], 1.2, 0.35, 700),
            # Between the upright front slot and the speaker swivel, at the mount height.
            ("SpeakerMount_R", [(v["up_xc"] + v["spk_px"]) / 2, v["up_y"] - v["rail_l"],
                                v["desk_h"] + v["spk_pz"]], -1.57, 0.15, 500),
            # LAP-01 base on the right stile front slot, arm reaching forward to the tray.
            ("LaptopArm", [v["stile_r_x"], v["stile_front"] - v["lap_reach"] / 2, v["lap_mount_z"]],
             -0.7, 0.35, 1000),
        )
    except KeyError as exc:
        raise FinishError(f"skeleton lacks {exc} needed for the named views") from exc
    by_name = {view[0]: view for view in (*FIXED_VIEWS, *detail)}
    return tuple(by_name[n] for n in VIEW_ORDER)


# Visibility sets as configuration rows (SolidCraft has no display states): link groups suppressed.
DISPLAY_ROWS: Mapping[str, tuple[str, ...]] = {
    "Full": (),
    "Frame only": ("DSK-01", "MON-", "SPK-", "PC-", "INP-", "LAP-", "CHR-"),
    "No desktop": ("DSK-01",),
    "Monitors + speakers": ("DSK-", "HW-", "PC-", "INP-", "LAP-", "CHR-", "FRM-05", "FRM-08"),
    "Rails only": ("DSK-", "FRM-05", "FRM-08", "MON-", "SPK-", "PC-", "INP-", "LAP-", "CHR-"),
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
            props = {k: str(meta[k]) for k in ("Material", "ReleaseState", "Source") if k in meta}
    if props:
        commands.append(_cmd("component.metadata.set", component=component, properties=props))
    return commands


def _view_commands(views: Sequence[View]) -> list[dict[str, object]]:
    return [_cmd("view.save", name=n, camera={"target": [round(c, 1) for c in t], "yaw": y, "pitch": p,
                                               "distance": d})
            for n, t, y, p, d in views]


def _config_commands(links: Sequence[str]) -> list[dict[str, object]]:
    commands = [_cmd("config.configure", features=list(links))]
    for row, prefixes in DISPLAY_ROWS.items():
        values = {f"suppress:{f}": f.startswith(prefixes) if prefixes else False for f in links}
        commands.append(_cmd("config.row", name=row, values=values))
    return [*commands, _cmd("config.activate", row="Full")]


def _folder(component: str) -> str:
    return f"{component.split('-')[0]} parts"


def _joint_names(design: Path, out: Path) -> list[str]:
    """Placement joint names in creation order (`joint.list`, ~2 s headless)."""
    script = out.with_suffix(".script.json")
    script.write_text(json.dumps({"commands": [_cmd("joint.list")]}), encoding="utf-8")
    _run(["run", str(script), "--in", str(design), "--results", "--quiet", "--json-out", str(out)])
    try:
        joints = json.loads(out.read_text(encoding="utf-8"))[0]["joints"]
        return [j["name"] for j in sorted(joints, key=lambda j: j["id"])]
    except (OSError, json.JSONDecodeError, LookupError, TypeError) as exc:
        raise FinishError(f"unexpected joint.list result in {out}: {exc}") from exc


def _group_commands(links: Sequence[str], joint_folders: Mapping[str, str]) -> list[dict[str, object]]:
    """One timeline folder per group prefix (DSK, FRM, HW, ...) holding its links and their placement
    joints, plus the skeleton sketch."""
    groups: dict[str, list[str]] = {"REF skeleton": ["SKL_Eye"]}
    joints: dict[str, list[str]] = {}
    for link in links:
        groups.setdefault(_folder(link), []).append(link)
    for joint, folder in joint_folders.items():
        joints.setdefault(folder, []).append(joint)
    return [_cmd("timeline.group", name=name, features=features, **({"joints": joints[name]} if name in joints else {}))
            for name, features in groups.items()]


def _joint_folders(names: Sequence[str], components: Sequence[str]) -> dict[str, str]:
    """{joint: folder}. build_script creates one placement joint per occurrence, in occurrence order,
    and `components` is one entry per occurrence in that order, so the two zip."""
    if len(names) != len(components):
        raise FinishError(f"{len(names)} joints for {len(components)} occurrences: can't match them")
    folders = {joint: _folder(comp) for joint, comp in zip(names, components)}
    stray = [j for j, f in folders.items() if j.startswith("J_HW-") != (f == _folder("HW-"))]
    if stray:
        raise FinishError(f"joint order doesn't match the occurrences (e.g. {stray[0]})")
    return folders


def finish_assembly(design: Path, components: Sequence[str], values: Mapping[str, float] | None = None) -> None:
    """Apply materials, appearance, properties, views, display rows and timeline groups in place.

    `components` holds one component name per occurrence, in build order (as build_script inserts them).

    `values` are the evaluated skeleton values of the design (for the view targets); default: the main
    skeleton. Variants pass their own.
    """
    try:
        views = skeleton_views(values if values is not None else skeleton_values.values())
    except skeleton_values.SkeletonError as exc:
        raise FinishError(f"cannot evaluate the skeleton for the views: {exc}") from exc
    # Scratch files are named after the design, so the main and variant builds can run in parallel.
    script_out, eval_out = BUILD / f"{design.stem}_finish.json", BUILD / f"{design.stem}_eval.json"
    BUILD.mkdir(exist_ok=True)
    _run(["eval", str(design), "--json-out", str(eval_out)])
    real = _real_bodies(eval_out)
    links = list(dict.fromkeys(components))
    commands = [c for comp in links for c in _part_commands(comp, real)]
    joint_folders = _joint_folders(_joint_names(design, BUILD / f"{design.stem}_joints.json"), components)
    commands += _view_commands(views) + _config_commands(links) + _group_commands(links, joint_folders)
    script_out.write_text(json.dumps({"commands": commands}, indent=1), encoding="utf-8")
    log.info("wrote %s (%d commands)", script_out.relative_to(ROOT), len(commands))
    _run(["run", str(script_out), "--in", str(design), "--save", str(design), "--quiet"])
