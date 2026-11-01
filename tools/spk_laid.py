"""Laid-down speaker layout (62x32 variant): R-40M on its side on an Aperta300 stand under each side screen.

The speaker lies on its side, tweeter end outboard, on a stand tilted front-up; stand and speaker turn
toward the Eye. Everything here is plain geometry on evaluated skeleton values (mm / rad):

- `solve(v)` places the stands as far back as the monitors allow (3D box test with a margin) and aims them.
- `frame_vectors(side, tilt)` gives the part-local directions that land on world +Z / +X for the
  placement joint (SolidCraft takes these as numbers, so they are computed, never typed).
- `speaker_shapes(v)` gives the boxes for tools/sightlines.py.

Speaker part frame (SPK-01): origin = rear face centre at spk_mount_frac*spk_h above the bottom, -Y front,
+Z up (tweeter end). Stand part frame (SPK-05): origin = rear bottom edge centre on the desktop, -Y front.
"""

from __future__ import annotations

import importlib.util
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from sightlines import (
    IDENTITY,
    Matrix,
    Point,
    Shape,
    _add,
    apply,
    matmul,
    overlap,
    rot_z,
    shapes,
)

__all__ = [
    "LEFT",
    "RIGHT",
    "LaidLayout",
    "LayoutError",
    "clear_window",
    "frame_matrix",
    "frame_vectors",
    "min_tray_z",
    "solve",
    "speaker_origin",
    "speaker_shapes",
    "stand_origin",
]

LEFT, RIGHT = -1, 1
MARGIN = 10.0  # mm clearance kept to the monitors, mouse pad and laptop
YAW_MAX = math.radians(35.0)


class LayoutError(Exception):
    """No placement satisfies the clearances."""


@dataclass(frozen=True)
class LaidLayout:
    """Stand centre |x| and y, toe-in yaw and stand tilt (rad); stand size (mm)."""

    x: float
    y: float
    yaw: float
    tilt: float
    st_w: float
    st_d: float
    st_h: float


def frame_matrix(side: int, tilt: float) -> Matrix:
    """Speaker local -> world before yaw: laid on its side (tweeter end outboard), then tilted front-up."""
    c, s = math.cos(tilt), math.sin(tilt)
    if side == LEFT:  # local +Z -> world -X, local +X -> world +Z
        return ((0.0, 0.0, -1.0), (s, c, 0.0), (c, -s, 0.0))
    return ((0.0, 0.0, 1.0), (-s, c, 0.0), (-c, -s, 0.0))


def frame_vectors(side: int, tilt: float) -> tuple[list[float], list[float]]:
    """(zl, xl): the part-local directions that land on world +Z and +X (rows of the frame matrix)."""
    m = frame_matrix(side, tilt)
    return [round(a, 9) for a in m[2]], [round(a, 9) for a in m[0]]


def _yaw(side: int, layout: LaidLayout) -> float:
    return -side * layout.yaw  # left turns +yaw (front toward +X), right mirrors


def stand_origin(side: int, layout: LaidLayout) -> Point:
    """World plan position of the stand origin (rear bottom edge centre), z = 0 on the desktop."""
    a, psi = layout.st_d / 2, layout.yaw
    return (side * (layout.x + a * math.sin(psi)), layout.y + a * math.cos(psi), 0.0)


def speaker_origin(side: int, layout: LaidLayout, v: Mapping[str, float]) -> Point:
    """World position of the speaker part origin (z above the desktop)."""
    e = (v["spk_mount_frac"] - 0.5) * v["spk_h"]  # origin sits this far from the box centre, toward the tweeter
    b = v["spk_w"] / 2 * math.sin(layout.tilt)
    local = (side * e, b, layout.st_h + v["spk_w"] / 2 * math.cos(layout.tilt))
    return _add(stand_origin(side, layout), apply(rot_z(_yaw(side, layout)), local))


LAP01_GEN = Path(__file__).resolve().parent.parent / "parts" / "src" / "LAP-01_gen.py"


def speaker_shapes(v: Mapping[str, float], layout: LaidLayout, pad: float = 0.0) -> list[Shape]:
    """Speaker cabinets (front = local -Y) and stands as boxes, optionally grown by `pad` mm."""
    out = []
    for side, tag in ((LEFT, "L"), (RIGHT, "R")):
        yaw = rot_z(_yaw(side, layout))
        rot = matmul(yaw, frame_matrix(side, layout.tilt))
        mf, h, w = v["spk_mount_frac"], v["spk_h"], v["spk_w"]
        out.append(Shape(f"Speaker_{tag}", speaker_origin(side, layout, v), rot, (-w / 2 - pad, w / 2 + pad),
                         (-v["spk_d"] - pad, pad), (-mf * h - pad, (1 - mf) * h + pad)))
        front_h = layout.st_h + layout.st_d * math.tan(layout.tilt)
        out.append(Shape(f"Stand_{tag}", stand_origin(side, layout), yaw, (-layout.st_w / 2 - pad, layout.st_w / 2 + pad),
                         (-layout.st_d - pad, pad), (0.0, front_h + pad)))
    return out


OBSTACLES = ("Monitor_Main", "Monitor_Side", "MousePad_Zone", "Crossbar_Low", "Upright_L", "Upright_R", "Stile_Main",
             "Stile_Side", "Stile_Right")


def _on_desk(v: Mapping[str, float], layout: LaidLayout) -> bool:
    """Both stands' footprints lie on the desktop."""
    for stand in (s for s in speaker_shapes(v, layout) if s.name.startswith("Stand")):
        for x, y, _ in stand.corners():
            if abs(x) > v["desk_w"] / 2 or not v["desk_front"] <= y <= v["desk_front"] + v["desk_d"]:
                return False
    return True


def _fits(v: Mapping[str, float], layout: LaidLayout) -> bool:
    obstacles = [s for s in shapes(v) if s.name in OBSTACLES]
    clear = not any(overlap(a, b) for a in speaker_shapes(v, layout, MARGIN) for b in obstacles)
    return clear and _on_desk(v, layout)


def clear_window(v: Mapping[str, float], base: LaidLayout, step: float = 1.0) -> tuple[float, float] | None:
    """Longest run of stand-centre depths (y) that fit at the base yaw, scanned in `step` mm, or None."""
    best: tuple[float, float] | None = None
    start: float | None = None
    y, end = v["desk_front"], v["desk_front"] + v["desk_d"]
    while y <= end + step:
        ok = y <= end and _fits(v, replace(base, y=y))
        if ok and start is None:
            start = y
        if not ok and start is not None:
            if best is None or y - step - start > best[1] - best[0]:
                best = (start, y - step)
            start = None
        y += step
    return best


def solve(v: Mapping[str, float], stand: Mapping[str, float], yaw_max: float = YAW_MAX,
          min_window: float = 10.0) -> LaidLayout:
    """Stands mirrored under the side screens (|x| = side monitor centre), at the middle of the clear depth
    window, turned as far toward the Eye as still leaves `min_window` mm of window (1 deg steps)."""
    base = LaidLayout(abs(v["m3_x"]), 0.0, 0.0, math.radians(stand["tilt_deg"]), stand["w"], stand["d"], stand["h"])
    for deg in range(int(math.degrees(yaw_max)), -1, -1):
        trial = replace(base, yaw=math.radians(deg))
        window = clear_window(v, trial)
        if window is None or window[1] - window[0] < min_window:
            continue
        y = (window[0] + window[1]) / 2
        aim = math.atan2(trial.x - v["m1_x"], y - v["eye_y"])
        if trial.yaw <= aim + 1e-9:  # never turn past the Eye
            return replace(trial, y=y)
    raise LayoutError("speakers don't fit between the monitors and the mouse pad at any toe-in")


def _lmnt_sizes() -> dict[str, float]:
    """The LAP-01 generator's fixed jig sizes (`lmnt_* = "<n> mm"`), so this envelope has one source (AGENTS §3)."""
    spec = importlib.util.spec_from_file_location("lap01_gen", LAP01_GEN)
    if spec is None or spec.loader is None:
        raise LayoutError(f"cannot load {LAP01_GEN}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {n: float(e.removesuffix(" mm")) for n, e, _ in module.PARAMS if re.fullmatch(r"[\d.]+ mm", e)}


def _arm(v: Mapping[str, float], tray_z: float) -> list[Shape]:
    """LAP-01 envelope (D19): riser in front of the right stile, an L arm (Y leg at the stile, X leg at the
    pivot depth) and the puck under the tray centre. World frame; mirrors LAP-01_gen.arm()."""
    s = _lmnt_sizes()
    puck_top = tray_z + v["lap_yoke_bot"]
    arm_bot = puck_top - s["lmnt_puck_h"] - s["lmnt_arm_t"]
    x0, y0 = v["stile_r_x"], v["stile_front"]
    plate_top = v["bar1_z"] + v["rail_l"] / 2 + s["lmnt_plate_bot"] + s["lmnt_plate_h"]
    riser_y = y0 - s["lmnt_t"] - s["lmnt_riser_d"] - 0.1
    half_w, half_a = s["lmnt_w"] / 2, s["lmnt_arm_w"] / 2
    xs = sorted((x0, v["lap_x"]))
    return [
        Shape("Laptop_ArmRiser", (0.0, 0.0, 0.0), IDENTITY, (x0 - half_w, x0 + half_w), (riser_y, y0),
              (arm_bot, plate_top)),
        Shape("Laptop_ArmY", (0.0, 0.0, 0.0), IDENTITY, (x0 - half_a, x0 + half_a), (v["lap_y"] - half_a, riser_y),
              (arm_bot, arm_bot + s["lmnt_arm_t"])),
        Shape("Laptop_ArmX", (0.0, 0.0, 0.0), IDENTITY, (xs[0] - half_a, xs[1] + half_a),
              (v["lap_y"] - half_a, v["lap_y"] + half_a), (arm_bot, arm_bot + s["lmnt_arm_t"])),
        Shape("Laptop_Puck", (0.0, 0.0, 0.0), IDENTITY, (v["lap_x"] - s["lmnt_puck_d"] / 2, v["lap_x"] + s["lmnt_puck_d"] / 2),
              (v["lap_y"] - s["lmnt_puck_d"] / 2, v["lap_y"] + s["lmnt_puck_d"] / 2), (puck_top - s["lmnt_puck_h"], puck_top)),
    ]


def min_tray_z(v: Mapping[str, float], layout: LaidLayout, laptop_shapes: object, step: float = 5.0) -> float:
    """Lowest laptop tray height (5 mm steps) at which tray, laptop and arm clear the right speaker and stand.

    `laptop_shapes(values) -> list[Shape]` is sightlines.laptop (passed in to keep this module pure)."""
    speaker = [s for s in speaker_shapes(v, layout, MARGIN) if s.name.endswith("_R")]
    z = v["lap_tray_z"]
    while z < 600.0:
        trial = {**v, "lap_tray_z": z}
        lap = [*laptop_shapes(trial), *_arm(trial, z)]  # type: ignore[operator]
        if not any(overlap(a, b) for a in lap for b in speaker):
            return z
        z += step
    raise LayoutError("no laptop tray height below 600 mm clears the right speaker")
