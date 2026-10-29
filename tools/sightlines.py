"""Sightline check: is anything between the Eye and each speaker (or monitor)?

    python tools/sightlines.py                 # the assembly's current parameter values
    python tools/sightlines.py --set lap_az=40 --set spk_bot=250   # what-if overrides (mm / deg)

Each object is an analytic box from the skeleton parameters (speaker cabinets, monitors, laptop + tray),
cast as a grid of rays from the Eye point. A target's front face (speaker baffle with
the drivers, monitor screen) is hidden where a ray hits another object before it; the report gives the
hidden share of that face. Boxes are envelopes
(slightly larger than the real parts), so "clear" means clear.

Overrides only change the named value, not the parameters derived from it: derived layout values are
re-computed here for the laptop and speaker placement (see `_derive`). Exits non-zero if a speaker is blocked.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Shape", "Window", "boxed", "laptop", "shapes", "overlap", "front_face", "window", "blockers", "main"]

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / "desk_rails.solidcraft"
EVAL = ROOT / "build" / "desk_rails_near_eval.json"
CLI = "solidcraft-cli"
ANGLES = ("spk_yaw", "spk_yaw_max", "spk_aim", "m3_yaw", "lap_az", "lap_yaw", "lap_lid", "lap_kb_tilt", "m1_tilt",
          "spk_tilt")
TARGETS = ("Speaker_L", "Speaker_R", "Monitor_Main", "Monitor_Side", "Laptop_Lid")

Point = tuple[float, float, float]
Matrix = tuple[Point, Point, Point]  # rows
IDENTITY: Matrix = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def rot_z(a: float) -> Matrix:
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def rot_x(a: float) -> Matrix:
    c, s = math.cos(a), math.sin(a)
    return ((1.0, 0.0, 0.0), (0.0, c, -s), (0.0, s, c))


def matmul(a: Matrix, b: Matrix) -> Matrix:
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))  # type: ignore[return-value]


def apply(m: Matrix, p: Point) -> Point:
    return tuple(sum(m[i][k] * p[k] for k in range(3)) for i in range(3))  # type: ignore[return-value]


def _add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _t(m: Matrix) -> Matrix:
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))  # type: ignore[return-value]


@dataclass(frozen=True)
class Shape:
    """A named oriented box: world origin + rotation (local -> world), local x/y/z extents (z above desktop)."""

    name: str
    origin: Point
    rot: Matrix
    xs: tuple[float, float]
    ys: tuple[float, float]
    zs: tuple[float, float]

    def corners(self) -> list[Point]:
        return [_add(self.origin, apply(self.rot, (x, y, z))) for x in self.xs for y in self.ys for z in self.zs]

    def axes(self) -> list[Point]:
        return [tuple(self.rot[i][j] for i in range(3)) for j in range(3)]  # type: ignore[misc]


def boxed(name: str, cx: float, cy: float, yaw: float, xs: tuple[float, float], ys: tuple[float, float],
          zs: tuple[float, float]) -> Shape:
    """Box yawed about Z at plan point (cx, cy); zs are heights above the desktop."""
    return Shape(name, (cx, cy, 0.0), rot_z(yaw), xs, ys, zs)


@dataclass(frozen=True)
class Window:
    """Angular box seen from the Eye (deg) and the nearest distance (mm)."""

    az: tuple[float, float]
    el: tuple[float, float]
    near: float


def _params(design: Path) -> dict[str, float]:
    if not EVAL.is_file() or EVAL.stat().st_mtime < design.stat().st_mtime:
        result = subprocess.run([CLI, "eval", str(design), "--json-out", str(EVAL)], capture_output=True, text=True,
                                check=False)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout).strip()[:400])
    rows = json.loads(EVAL.read_text(encoding="utf-8"))["params"]
    return {r["name"]: r["value"] for r in rows if isinstance(r.get("value"), (int, float))}


def _derive(v: dict[str, float]) -> dict[str, float]:
    """Re-derive the placement values that overrides feed (mirrors skeleton/params.json)."""
    v = dict(v)
    v["eye_y"] = v["desk_front"] - v["eye_back"]
    v["lap_x"] = v["m1_x"] + v["lap_dist"] * math.sin(v["lap_az"])
    v["lap_y"] = v["eye_y"] + v["lap_dist"] * math.cos(v["lap_az"])
    v["lap_yaw"] = v["lap_az"]
    v["lap_lid"] = math.pi / 2 + v["lap_kb_tilt"] + v["m1_tilt"]
    v["lap_hinge_z"] = -(v["lap_tray_t"] + v["lap_hinge_r"] - 0.1)
    v["spk_yaw"] = min(v["spk_aim"], v["spk_yaw_max"])
    return v


def laptop(v: Mapping[str, float]) -> list[Shape]:
    """Tray, base and lid (LAP-02/03 envelopes), tilted lap_kb_tilt about the hinge axis, yawed to the Eye."""
    hz = v["lap_hinge_z"]
    frame = matmul(rot_z(-v["lap_yaw"]), rot_x(v["lap_kb_tilt"]))
    pivot = (v["lap_x"], v["lap_y"], v["lap_tray_z"] + hz)

    def part(name: str, rot: Matrix, offset: Point, xs: tuple[float, float], ys: tuple[float, float],
             zs: tuple[float, float]) -> Shape:
        """Box in the untilted laptop frame (rot/offset place it there; z measured from the tray top)."""
        local = _add(offset, (0.0, 0.0, -hz))
        return Shape(name, _add(pivot, apply(frame, local)), matmul(frame, rot), xs, ys, zs)

    half_w, half_d, m = v["mbp_w"] / 2, v["mbp_d"] / 2, v["lap_tray_m"]
    lid = rot_x(-v["lap_lid"])  # lid built closed toward -Y from the hinge, opened about -X
    return [
        part("Laptop_Tray", IDENTITY, (0.0, 0.0, 0.0), (-half_w - m, half_w + m), (-half_d - 4.1, half_d + m),
             (-v["lap_tray_t"], v["lap_lip_h"])),
        part("Laptop_Base", IDENTITY, (0.0, 0.0, 0.0), (-half_w, half_w), (-half_d, half_d), (0.0, 10.5)),
        part("Laptop_Lid", lid, (0.0, half_d, 13.0), (-half_w, half_w), (-220.2, 0.0), (-2.8, 2.5)),
    ]


def shapes(v: Mapping[str, float]) -> list[Shape]:
    """Speaker cabinets, monitors and the laptop as boxes (heights above the desktop)."""
    spk_z = (v["spk_bot"], v["spk_bot"] + v["spk_h"])
    spk = ((-v["spk_w"] / 2, v["spk_w"] / 2), (-v["spk_d"], 0.0), spk_z)
    return [
        boxed("Speaker_L", -v["spk_px"], v["spk_py"], v["spk_yaw"], *spk),
        boxed("Speaker_R", v["spk_px"], v["spk_py"], -v["spk_yaw"], *spk),
        boxed("Monitor_Main", v["m1_x"], v["mon_front"] + v["m1_t"], 0.0, (-v["m1_w"] / 2, v["m1_w"] / 2),
              (-v["m1_t"], 0.0), (v["mon_clearance"], v["mon_clearance"] + v["m1_h"])),
        boxed("Monitor_Side", v["m3_x"], v["stile_front"] - v["m3_off"], v["m3_yaw"], (-v["m3_w"] / 2, v["m3_w"] / 2),
              (-v["m3_t"], 0.0), (v["m3_bot"], v["m3_bot"] + v["m3_h"])),
        *laptop(v),
        *frame(v),
    ]


def frame(v: Mapping[str, float]) -> list[Shape]:
    """Obstacles the laptop must clear (not sightline targets): desktop, mouse-pad zone, crossbars, uprights,
    main stile and the monitor's VESA adapter. Envelopes from the skeleton (frame front plane = stile_front)."""
    bar_x = (-(v["up_xc"] - v["rail_l"] / 2), v["up_xc"] - v["rail_l"] / 2)
    bar_y = (v["stile_front"], v["stile_front"] + v["rail_s"])
    up_z = (-v["up_below"], v["up_above"] + v["rail_l"])
    half_pad = v["pad_size"] / 2
    return [
        boxed("Desktop", 0.0, 0.0, 0.0, (-v["desk_w"] / 2, v["desk_w"] / 2), (v["desk_front"], v["desk_front"] + v["desk_d"]),
              (-v["desk_t"], 0.0)),
        boxed("MousePad_Zone", v["pad_x"], v["pad_y"], 0.0, (-half_pad, half_pad), (-half_pad, half_pad), (0.0, 45.0)),
        boxed("Crossbar_Low", 0.0, 0.0, 0.0, bar_x, bar_y, (v["bar1_z"] - v["rail_l"] / 2, v["bar1_z"] + v["rail_l"] / 2)),
        boxed("Crossbar_High", 0.0, 0.0, 0.0, bar_x, bar_y, (v["bar2_z"] - v["rail_l"] / 2, v["bar2_z"] + v["rail_l"] / 2)),
        boxed("Upright_L", -v["up_xc"], 0.0, 0.0, (-v["rail_l"] / 2, v["rail_l"] / 2),
              (v["stile_front"], v["stile_front"] + v["rail_l"]), up_z),
        boxed("Upright_R", v["up_xc"], 0.0, 0.0, (-v["rail_l"] / 2, v["rail_l"] / 2),
              (v["stile_front"], v["stile_front"] + v["rail_l"]), up_z),
        boxed("Stile_Main", v["m1_x"], 0.0, 0.0, (-v["rail_l"] / 2, v["rail_l"] / 2), bar_y,
              (v["bar1_z"] - v["rail_l"] / 2, v["bar2_z"] + v["rail_l"] / 2)),
        boxed("VESA_Main", v["m1_x"], 0.0, 0.0, (-v["vesa_adp"] / 2, v["vesa_adp"] / 2),
              (v["mon_front"] + v["m1_t"], v["stile_front"]),
              (v["mon_clearance"] + v["m1_h"] / 2 - v["vesa_adp"] / 2, v["mon_clearance"] + v["m1_h"] / 2 + v["vesa_adp"] / 2)),
    ]


def overlap(a: Shape, b: Shape) -> bool:
    """Separating-axis test for two oriented boxes."""
    axes = a.axes() + b.axes()
    for u in a.axes():
        for w in b.axes():
            cr = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
            if sum(c * c for c in cr) > 1e-12:
                axes.append(cr)
    ca, cb = a.corners(), b.corners()
    for ax in axes:
        pa = [sum(p[i] * ax[i] for i in range(3)) for p in ca]
        pb = [sum(p[i] * ax[i] for i in range(3)) for p in cb]
        if max(pa) <= min(pb) or max(pb) <= min(pa):
            return False
    return True


def front_face(shape: Shape) -> Shape:
    """The target's front face as a 1 mm slab: local -Y (drivers / screen side), or local -Z for the laptop lid
    (built closed, so its screen is the underside)."""
    if shape.name == "Laptop_Lid":
        return Shape(shape.name, shape.origin, shape.rot, shape.xs, shape.ys, (shape.zs[0], shape.zs[0] + 1.0))
    return Shape(shape.name, shape.origin, shape.rot, shape.xs, (shape.ys[0], shape.ys[0] + 1.0), shape.zs)


def window(shape: Shape, eye: Point) -> Window:
    az, el, dist = [], [], []
    for x, y, z in shape.corners():
        dx, dy, dz = x - eye[0], y - eye[1], z - eye[2]
        plan = math.hypot(dx, dy)
        az.append(math.degrees(math.atan2(dx, dy)))
        el.append(math.degrees(math.atan2(dz, plan)))
        dist.append(math.hypot(plan, dz))
    return Window((min(az), max(az)), (min(el), max(el)), min(dist))


def _hit(shape: Shape, eye: Point, d: Point) -> float | None:
    """Distance along the unit ray eye + t*d to the box (slab method in the box frame), or None."""
    inv = _t(shape.rot)
    o = apply(inv, tuple(eye[i] - shape.origin[i] for i in range(3)))  # type: ignore[arg-type]
    r = apply(inv, d)
    lo, hi = 0.0, math.inf
    for axis, (a, b) in enumerate((shape.xs, shape.ys, shape.zs)):
        if abs(r[axis]) < 1e-12:
            if not a <= o[axis] <= b:
                return None
            continue
        t1, t2 = sorted(((a - o[axis]) / r[axis], (b - o[axis]) / r[axis]))
        lo, hi = max(lo, t1), min(hi, t2)
    return lo if lo <= hi else None


def _rays(w: Window, n: int) -> list[Point]:
    out = []
    for i in range(n):
        for j in range(n):
            az = math.radians(w.az[0] + (w.az[1] - w.az[0]) * (i + 0.5) / n)
            el = math.radians(w.el[0] + (w.el[1] - w.el[0]) * (j + 0.5) / n)
            out.append((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    return out


def blockers(v: Mapping[str, float], n: int = 48) -> dict[str, list[tuple[str, float]]]:
    """Per target: each object that hides part of its front face, with the hidden share (%)."""
    eye = (v["m1_x"], v["eye_y"], v["eye_above_desk"])
    all_shapes = {s.name: s for s in shapes(v)}
    out: dict[str, list[tuple[str, float]]] = {}
    for name in TARGETS:
        target = front_face(all_shapes[name])
        hits = [(d, t) for d in _rays(window(target, eye), n) if (t := _hit(target, eye, d)) is not None]
        hidden = {}
        for other, shape in all_shapes.items():
            if other == name or (name.startswith("Laptop") and other.startswith("Laptop")):
                continue
            count = sum(1 for d, t in hits if (u := _hit(shape, eye, d)) is not None and u < t)
            if count:
                hidden[other] = 100.0 * count / len(hits)
        out[name] = sorted(hidden.items(), key=lambda item: -item[1])
    return out


def _overrides(items: Sequence[str]) -> dict[str, float]:
    out = {}
    for item in items:
        name, _, value = item.partition("=")
        number = float(value)
        out[name] = math.radians(number) if name in ANGLES else number
    return out


def main(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--design", type=Path, default=DESIGN)
    parser.add_argument("--set", action="append", default=[], help="override NAME=VALUE (mm, or deg for angles)")
    args = parser.parse_args(argv)
    v = _derive({**_params(args.design), **_overrides(args.set)})
    eye = (v["m1_x"], v["eye_y"], v["eye_above_desk"])
    for s in shapes(v):
        w = window(s, eye)
        log.info("%-13s az %6.1f..%6.1f  el %6.1f..%6.1f  near %5.0f mm", s.name, *w.az, *w.el, w.near)
    all_shapes = shapes(v)
    for lap in (s for s in all_shapes if s.name.startswith("Laptop")):
        for other in (s for s in all_shapes if not s.name.startswith("Laptop")):
            if overlap(lap, other):
                log.info("CLASH    %s | %s", lap.name, other.name)
    blocked = False
    for target, items in blockers(v).items():
        if not items:
            log.info("clear    %s", target)
        for other, share in items:
            log.info("HIDDEN   %-13s %5.1f %% behind %s", target, share, other)
            blocked |= target.startswith("Speaker")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
