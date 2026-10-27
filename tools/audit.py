"""Structural + balance audit of the desk model.

Reads body bounding boxes from a solidcraft-cli build report (``--json-out``), assigns masses
(estimates below, edit MASS_INPUTS as real weights come in) and reports: mass budget, center of
mass vs the feet (tip margins), push force to tip at sit/stand height, leg load split, crossbar
sag and the load on the side-rail joints. Rule IDs refer to docs/EXTRUSION_GUIDE.md.

    python tools/check.py            # writes build/report.json, then runs this audit
    python tools/audit.py build/report.json
"""

from __future__ import annotations

import json
import math
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Mass", "load_bodies", "masses", "main"]

G = 9.81
E_ALU = 70_000.0  # N/mm^2
IN = 25.4

# Estimates (kg) as (low, nominal, high). Low frame/desktop = least stable case for tipping.
MASS_INPUTS: Mapping[str, tuple[float, float, float]] = {
    "frame": (48.0, 52.0, 70.0),       # DeskHaus ships Apex Pro 4 in 60 + 62 lb boxes -> ~52 kg net
    "desktop": (26.0, 28.0, 40.0),     # IKEA Karlby 186x3.8 package 28.9-29.7 kg; high = dense butcher block
    "Monitor_Main": (6.5, 6.5, 9.0),   # 32in 16:9, no stand (spec sheet TBD)
    "Monitor_Side": (4.5, 4.5, 7.0),   # 27in portrait, no stand
    "Speaker": (3.2, 3.2, 3.2),        # Klipsch R-40M, each (spec: 7 lb / 3.2 kg)
}
FRAME_MOVING_FRAC = 0.35       # share of frame mass that rides up (top supports, channels, inner stages)
PANEL_DENSITY = 600.0          # kg/m^3: plywood ~550-600, MDF ~750, acrylic ~1190
KG_PER_M = {"4040": 1.28, "2040": 0.88}  # Misumi HFS5 (guide section 2)
I_2040_STRONG = 5.13e4         # mm^4
PLATE_FILL, STEEL, ALU = 0.6, 7850.0, 2700.0
BRACKET_KG = {"brk_a": 0.05, "brk_a_small": 0.02}
STANDOFF_KG = 0.015            # standoff + T-nut + screw
VESA_ADAPTER_KG = 0.3          # printed adapter + screws, each monitor
FASTENERS_KG = 0.6             # T-nuts + bolts on the rail joints
SIT_STAND_IN = (22.5, 30.0, 48.5)
MODEL_DESK_H_IN = 30.0
BOLT_SPREAD_MM = 100.0         # assumed spacing of side-rail -> top-support bolts (D9, unmeasured)


@dataclass(frozen=True)
class Box:
    name: str
    lo: tuple[float, float, float]
    hi: tuple[float, float, float]

    @property
    def center(self) -> tuple[float, float, float]:
        return tuple((a + b) / 2 for a, b in zip(self.lo, self.hi))  # type: ignore[return-value]

    @property
    def size(self) -> tuple[float, float, float]:
        return tuple(b - a for a, b in zip(self.lo, self.hi))  # type: ignore[return-value]


@dataclass(frozen=True)
class Mass:
    name: str
    group: str        # frame / desktop / rails / monitors / panel / hardware
    kg: float
    x: float          # mm
    y: float
    moving: bool      # rides with the desktop


def _walk(node: object) -> Iterator[Mapping[str, object]]:
    if isinstance(node, Mapping):
        if "bbox" in node and "name" in node:
            yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def load_bodies(report: Path) -> dict[str, Box]:
    """First bbox per body name from a solidcraft-cli --json-out report."""
    bodies: dict[str, Box] = {}
    for b in _walk(json.loads(report.read_text())):
        name = str(b["name"])
        bb = b["bbox"]
        if name not in bodies and isinstance(bb, Mapping):
            bodies[name] = Box(name, tuple(bb["min"]), tuple(bb["max"]))  # type: ignore[arg-type]
    return bodies


def _extrusion_kg(box: Box) -> float:
    dims = sorted(box.size)
    profile = "4040" if dims[0] > 30 else "2040"
    return dims[2] / 1000 * KG_PER_M[profile]


def _part_kg(box: Box, case: int, panel_density: float) -> tuple[str, float] | None:
    n = box.name
    if n.startswith(("Upright_", "Crossbar_", "SideRail_", "Stile_")):
        return "rails", _extrusion_kg(box)
    if n in ("Monitor_Main", "Monitor_Side"):
        return "monitors", MASS_INPUTS[n][case] + VESA_ADAPTER_KG
    if n.startswith("Speaker_"):
        return "speakers", MASS_INPUTS["Speaker"][case]
    if n.startswith("SpkMount_"):
        sx, sy, sz = box.size
        return "speakers", sx * sy * sz * 1e-9 * ALU
    if n == "ModestyPanel":
        sx, sy, sz = box.size
        return "panel", sx * sy * sz * 1e-9 * panel_density
    if n.startswith("Plate_"):
        sx, sy, sz = box.size
        return "hardware", sx * sy * sz * 1e-9 * STEEL * PLATE_FILL
    if n.startswith("Bracket_Stile"):
        return "hardware", BRACKET_KG["brk_a_small"]
    if n.startswith("Bracket_"):
        return "hardware", BRACKET_KG["brk_a"]
    if n.startswith("Standoff_"):
        return "hardware", STANDOFF_KG
    return None


def masses(bodies: Mapping[str, Box], case: int, mount_case: int | None = None,
           panel_density: float = PANEL_DENSITY) -> list[Mass]:
    """Point masses. ``case`` (0 low, 1 nominal, 2 high) sets frame + desktop; ``mount_case`` sets
    the monitors (defaults to ``case``)."""
    mount = case if mount_case is None else mount_case
    desk = bodies["Desktop"].center
    frame_kg = MASS_INPUTS["frame"][case]
    out = [
        Mass("Desktop", "desktop", MASS_INPUTS["desktop"][case], desk[0], desk[1], True),
        Mass("Frame (moving part)", "frame", frame_kg * FRAME_MOVING_FRAC, 0.0, 0.0, True),
        Mass("Frame (base part)", "frame", frame_kg * (1 - FRAME_MOVING_FRAC), 0.0, 0.0, False),
    ]
    rail_ys: list[float] = []
    for box in bodies.values():
        part = _part_kg(box, mount, panel_density)
        if part is None:
            continue
        group, kg = part
        cx, cy, _ = box.center
        if box.name.startswith("Monitor_"):  # slab + rear bulge together
            back = bodies.get(f"{box.name}_Back")
            if back is not None:
                cy = (cy + back.center[1]) / 2
        out.append(Mass(box.name.removesuffix("_HFS5").removesuffix("_8020").removesuffix("_VSLOT"),
                        group, kg, cx, cy, True))
        if group == "rails" and not box.name.startswith("SideRail_"):
            rail_ys.append(cy)
    fy = sum(rail_ys) / len(rail_ys)
    out.append(Mass("Fasteners", "hardware", FASTENERS_KG, 0.0, fy, True))
    return out


def com(ms: Sequence[Mass]) -> tuple[float, float, float]:
    total = sum(m.kg for m in ms)
    return total, sum(m.kg * m.x for m in ms) / total, sum(m.kg * m.y for m in ms) / total


def _footprint(bodies: Mapping[str, Box]) -> tuple[float, float, float, float]:
    feet = [b for n, b in bodies.items() if n.startswith("Foot_")]
    return (min(b.lo[0] for b in feet), max(b.hi[0] for b in feet),
            min(b.lo[1] for b in feet), max(b.hi[1] for b in feet))


def _sag_mm(span: float, loads: Sequence[tuple[float, float]], w_n_per_mm: float) -> float:
    """Max deflection, simply supported 2040 (strong axis). loads = (N, distance from left end)."""
    best = 0.0
    for i in range(1, 200):
        x = span * i / 200
        d = w_n_per_mm * x * (span**3 - 2 * span * x**2 + x**3) / 24
        for p, a in loads:
            b = span - a
            if x <= a:
                d += p * b * x * (span**2 - b**2 - x**2) / (6 * span)
            else:
                d += p * a * (span - x) * (2 * span * x - x**2 - a**2) / (6 * span)
        best = max(best, d)
    return best / (E_ALU * I_2040_STRONG)


def _report_mass(ms: Sequence[Mass]) -> None:
    groups: dict[str, float] = {}
    for m in ms:
        groups[m.group] = groups.get(m.group, 0.0) + m.kg
    for g, kg in groups.items():
        print(f"  {g:<10} {kg:6.1f} kg")
    total, _, _ = com(ms)
    moving = sum(m.kg for m in ms if m.moving)
    print(f"  {'TOTAL':<10} {total:6.1f} kg   (riding on the lift: {moving:.1f} kg)")


def _report_balance(bodies: Mapping[str, Box], ms: Sequence[Mass], label: str) -> None:
    x0, x1, y0, y1 = _footprint(bodies)
    total, cx, cy = com(ms)
    w = total * G
    top_z = max(b.hi[2] for n, b in bodies.items() if n.startswith("Upright_"))
    print(f"\n[{label}] total {total:.1f} kg, COM x={cx:+.0f} mm, y={cy:+.0f} mm (+ = toward wall)")
    print(f"  feet: x {x0:.0f}..{x1:.0f}, y {y0:.0f}..{y1:.0f} mm")
    print(f"  margin to tip line: back {y1 - cy:.0f}, front {cy - y0:.0f}, "
          f"left {cx - x0:.0f}, right {x1 - cx:.0f} mm")
    for h_in in SIT_STAND_IN:
        h = top_z + (h_in - MODEL_DESK_H_IN) * IN
        back, front = w * (y1 - cy) / h, w * (cy - y0) / h
        side = w * min(cx - x0, x1 - cx) / h
        print(f"  desk {h_in:4.1f} in, push at upright top ({h / IN:4.1f} in): tips back at "
              f"{back:4.0f} N ({back / 4.448:3.0f} lbf), forward {front:4.0f} N, sideways {side:4.0f} N")


def _report_legs(bodies: Mapping[str, Box], ms: Sequence[Mass]) -> None:
    legs = [b.center[1] for n, b in bodies.items() if n.startswith("Leg_")]
    yb, yf = max(legs), min(legs)
    moving = [m for m in ms if m.moving]
    total, _, cy = com(moving)
    rear = (cy - yf) / (yb - yf)
    print(f"\nLift load: {total:.1f} kg moving, COM y={cy:+.0f} mm; legs at y={yf:+.0f}/{yb:+.0f}")
    print(f"  rear legs carry {rear:.0%} ({total * rear / 2:.1f} kg each), "
          f"front legs {1 - rear:.0%} ({total * (1 - rear) / 2:.1f} kg each)")


def _report_crossbars(bodies: Mapping[str, Box], ms: Sequence[Mass]) -> None:
    bar = bodies["Crossbar_Low_HFS5"] if "Crossbar_Low_HFS5" in bodies else next(
        b for n, b in bodies.items() if n.startswith("Crossbar_Low"))
    span, x_left = bar.size[0], bar.lo[0]
    loads: list[tuple[float, float]] = []
    for m in ms:
        if m.group == "monitors":
            loads.append((m.kg * G / 2, m.x - x_left))  # stile ties both bars: half each
        elif m.name.startswith("Standoff_Bar"):
            panel = next(p for p in ms if p.group == "panel")
            loads.append((panel.kg * G / 10, m.x - x_left))
    w = KG_PER_M["2040"] * G / 1000
    sag = _sag_mm(span, loads, w)
    print(f"\nCrossbar sag (each bar, pinned ends = upper bound): {sag:.2f} mm over {span:.0f} mm "
          f"(Misumi L/1000 = {span / 1000:.2f} mm); bolted ends land ~40-60% of this")


def _side_loads(ms: Sequence[Mass], x_r: float, x_l: float) -> dict[str, list[tuple[float, float]]]:
    """Split rail-system masses (not the side rails) onto the R/L uprights by the lever rule."""
    side: dict[str, list[tuple[float, float]]] = {"R": [], "L": []}
    for m in ms:
        if m.group not in ("rails", "monitors", "panel", "hardware", "speakers") or m.name.startswith(
                ("SideRail_", "Plate_SideRail", "Bracket_SideRail")):
            continue
        fr = min(max((m.x - x_l) / (x_r - x_l), 0.0), 1.0)
        side["R"].append((m.kg * G * fr, m.y))
        side["L"].append((m.kg * G * (1 - fr), m.y))
    return side


def _report_joints(bodies: Mapping[str, Box], ms: Sequence[Mass]) -> None:
    up = {s: bodies[n] for n in bodies for s in "RL" if n.startswith(f"Upright_{s}_")}
    ts_back = bodies["TopSupport_R"].hi[1]
    face = up["R"].lo[1]
    print(f"\nSide joints (static; bolt spread {BOLT_SPREAD_MM:.0f} mm assumed, last bolt at "
          f"top-support rear end y={ts_back:.0f}):")
    for s, loads in _side_loads(ms, up["R"].center[0], up["L"].center[0]).items():
        v = sum(f for f, _ in loads)
        m_tee = sum(f * (y - face) for f, y in loads) / 1000
        m_bolt = sum(f * (y - ts_back) for f, y in loads) / 1000
        pull = m_bolt / (BOLT_SPREAD_MM / 1000)
        print(f"  {s}: hangs {v:5.0f} N ({v / G:4.1f} kg); T-joint moment {m_tee:+5.1f} N*m; "
              f"at top-support bolts {m_bolt:5.1f} N*m -> ~{pull:4.0f} N bolt pull")


def _report_ergonomics(bodies: Mapping[str, Box]) -> None:
    """Screen top vs eye height and gaze angles (top edge at or a bit below eye level; center
    about 10-20 deg down)."""
    eye = bodies.get("Eye")
    if eye is None:
        return
    _, ey, ez = eye.center
    print("\nErgonomics (eye marker = eye_above_desk / eye_back; same relation sitting and standing):")
    for name in ("Monitor_Main", "Monitor_Side"):
        scr = bodies[name]
        top, mid = scr.hi[2], (scr.lo[2] + scr.hi[2]) / 2
        dist = scr.lo[1] - ey
        down = math.degrees(math.atan2(ez - mid, dist))
        verdict = "OK" if top <= ez + 25 else "HIGH: neck tilts up"
        print(f"  {name}: top {(top - ez) / IN:+.1f} in vs eye ({verdict}); center {down:+.0f} deg below eye; "
              f"distance {dist / IN:.0f} in")
    for name in ("Speaker_R", "Speaker_L"):
        if name in bodies:
            tw = bodies[name].hi[2] - 3 * IN  # tweeter ~3 in below the top
            print(f"  {name}: tweeter ~{(tw - ez) / IN:+.1f} in vs ear/eye height")


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    bodies = load_bodies(Path(argv[1]))
    nominal = masses(bodies, 1)
    print("Mass budget (nominal):")
    _report_mass(nominal)
    _report_balance(bodies, nominal, "NOMINAL")
    _report_balance(bodies, masses(bodies, 2, 2, 750.0), "ALL HEAVY (MDF panel)")
    _report_balance(bodies, masses(bodies, 0, 2, 1190.0),
                    "WORST: light frame+top, heavy monitors, acrylic panel")
    _report_legs(bodies, nominal)
    _report_crossbars(bodies, nominal)
    _report_joints(bodies, nominal)
    _report_ergonomics(bodies)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
