"""Structural + balance audit of the desk model.

Reads the placed bodies from a ``solidcraft-cli eval --json-out`` report of the linked assembly
(see tools/eval_bodies.py). Masses and centres of mass come from the model's real materials,
except for envelope models of purchased items (desk frame, monitors, speakers, PC), whose solid
envelopes would weigh far too much: those take the spec weights in SPEC_KG at the envelope's
centre of mass. Reports: mass budget, center of mass vs the feet (tip margins), push force to tip
at sit/stand height, leg load split, crossbar sag and the load on the side-rail joints.
Rule IDs refer to docs/EXTRUSION_GUIDE.md.

    python tools/check.py            # writes build/report.json, then runs this audit
    python tools/audit.py build/report.json
"""

from __future__ import annotations

import logging
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from eval_bodies import Body, ReportError, bbox, load_bodies, load_params

__all__ = ["Mass", "com", "main", "masses"]

log = logging.getLogger(__name__)

G = 9.81
E_ALU = 70_000.0  # N/mm^2
IN = 25.4

# Spec weights (kg) for envelope models, as (low, nominal, high). Low frame/desktop = least
# stable case for tipping. Matched by part body name prefix; one mass per placement.
FRAME_KG = (48.0, 52.0, 70.0)  # DeskHaus ships Apex Pro 4 in 60 + 62 lb boxes -> ~52 kg net
FRAME_BODIES = ("TopSupport_JC", "ChannelBar", "Leg", "Foot")
FRAME_MOVING = ("TopSupport_JC", "ChannelBar", "Leg")  # COG of the part that rides up
FRAME_BASE = ("Foot", "Leg")                             # COG of the part that stays down
FRAME_MOVING_FRAC = 0.35       # share of frame mass that rides up (top supports, channels, inner stages)


@dataclass(frozen=True)
class Spec:
    group: str
    prefix: str
    kg: tuple[float, float, float]
    extra_kg: float = 0.0
    per_placement: bool = True


VESA_ADAPTER_KG = 0.3          # printed adapter + screws, each monitor (not modelled)
SPEC_KG: tuple[Spec, ...] = (
    Spec("monitors", "Monitor_Main", (6.5, 6.5, 9.0), VESA_ADAPTER_KG),  # 32in 16:9, no stand (spec TBD)
    Spec("monitors", "Monitor_Side", (4.5, 4.5, 7.0), VESA_ADAPTER_KG),  # 27in portrait, no stand
    Spec("speakers", "R40M_", (3.2, 3.2, 3.2)),     # Klipsch R-40M, each (spec: 7 lb / 3.2 kg)
    # MEASURE: Fractal North case ~7.6 kg empty; built PC + slats + strap estimated.
    Spec("pc", "PC_", (7.6, 13.0, 18.0), per_placement=False),
)
# Desktop: model material mass (Karlby birch) scaled for the cases; high = dense butcher block.
DESKTOP_FACTOR = (0.93, 1.0, 1.43)
# Real-geometry bodies keep their model mass; prefix -> report group.
GROUPS: tuple[tuple[str, str], ...] = (
    ("Desktop", "desktop"), ("Modesty_Panel", "panel"),
    ("Upright_4040", "rails"), ("Crossbar_2040", "rails"), ("SideRail_", "rails"), ("Stile_2040", "rails"),
    ("SpkMount_", "speakers"), ("MousePad", "input"), ("Mouse_", "input"), ("Keyboard_", "input"),
    ("HPTTD5", "hardware"), ("HPTLD5", "hardware"), ("HBLFSN5", "hardware"),
    ("Standoff_M5x12", "hardware"), ("M6x20_SHCS", "hardware"),
)
FASTENERS_KG = 0.6             # T-nuts + plate/bracket bolts on the rail joints (not modelled)
I_2040_STRONG = 5.13e4         # mm^4
KG_PER_M_2040 = 0.88           # Misumi HFS5 (guide section 2)
PANEL_LOAD_SHARE = 0.1         # share of the panel weight on each bar standoff
SIT_STAND_IN = (22.5, 30.0, 48.5)
MODEL_DESK_H_IN = 30.0
BOLT_SPREAD_MM = 100.0         # assumed spacing of side-rail -> top-support bolts (D9, unmeasured)


@dataclass(frozen=True)
class Mass:
    name: str
    group: str        # frame / desktop / rails / monitors / speakers / panel / pc / input / hardware
    kg: float
    x: float          # mm
    y: float
    moving: bool      # rides with the desktop


def _starts(b: Body, prefixes: str | tuple[str, ...]) -> bool:
    return b.part_body.startswith(prefixes)


def _cog(bodies: Sequence[Body]) -> tuple[float, float]:
    total = sum(b.kg for b in bodies)
    return sum(b.kg * b.com[0] for b in bodies) / total, sum(b.kg * b.com[1] for b in bodies) / total


def _frame_masses(bodies: Sequence[Body], case: int) -> list[Mass]:
    kg = FRAME_KG[case]
    up = _cog([b for b in bodies if _starts(b, FRAME_MOVING)])
    down = _cog([b for b in bodies if _starts(b, FRAME_BASE)])
    return [Mass("Frame (moving part)", "frame", kg * FRAME_MOVING_FRAC, *up, True),
            Mass("Frame (base part)", "frame", kg * (1 - FRAME_MOVING_FRAC), *down, False)]


def _spec_masses(bodies: Sequence[Body], case: int, mount_case: int) -> list[Mass]:
    out: list[Mass] = []
    for spec in SPEC_KG:
        units: dict[str, list[Body]] = {}
        for b in bodies:
            if _starts(b, spec.prefix):
                units.setdefault(b.label if spec.per_placement else spec.prefix.rstrip("_"), []).append(b)
        level = mount_case if spec.group == "monitors" else case
        out += [Mass(name, spec.group, spec.kg[level] + spec.extra_kg, *_cog(parts), True)
                for name, parts in units.items()]
    return out


def _model_kg(b: Body, case: int, panel_density: float | None) -> float:
    if b.part_body == "Desktop":
        return b.kg * DESKTOP_FACTOR[case]
    if b.part_body == "Modesty_Panel" and panel_density is not None:
        return b.volume_mm3 * 1e-9 * panel_density
    return b.kg


def masses(bodies: Sequence[Body], case: int, mount_case: int | None = None,
           panel_density: float | None = None) -> list[Mass]:
    """Point masses. ``case`` (0 low, 1 nominal, 2 high) sets frame, desktop and PC; ``mount_case``
    sets the monitors (defaults to ``case``); ``panel_density`` (kg/m^3) overrides the panel material."""
    mount = case if mount_case is None else mount_case
    out = _frame_masses(bodies, case) + _spec_masses(bodies, case, mount)
    group_of = dict(GROUPS)
    for b in bodies:
        group = next((g for p, g in group_of.items() if _starts(b, p)), None)
        if group is None:
            if not _starts(b, FRAME_BODIES) and not any(_starts(b, s.prefix) for s in SPEC_KG):
                log.warning("audit: no mass rule for body %s, skipped", b.name)
            continue
        out.append(Mass(b.label, group, _model_kg(b, case, panel_density), b.com[0], b.com[1], True))
    rail_ys = [m.y for m in out if m.group == "rails" and not m.name.startswith("SideRail_")]
    out.append(Mass("Fasteners", "hardware", FASTENERS_KG, 0.0, sum(rail_ys) / len(rail_ys), True))
    return out


def com(ms: Sequence[Mass]) -> tuple[float, float, float]:
    total = sum(m.kg for m in ms)
    return total, sum(m.kg * m.x for m in ms) / total, sum(m.kg * m.y for m in ms) / total


def _select(bodies: Sequence[Body], prefix: str) -> list[Body]:
    found = [b for b in bodies if b.part_body.startswith(prefix)]
    if not found:
        raise ReportError(f"no {prefix!r} bodies in the report")
    return found


def _by_label(bodies: Sequence[Body], label: str) -> Body:
    try:
        return next(b for b in bodies if b.label == label)
    except StopIteration as exc:
        raise ReportError(f"no placement {label!r} in the report") from exc


def _footprint(bodies: Sequence[Body]) -> tuple[float, float, float, float]:
    lo, hi = bbox(_select(bodies, "Foot"))
    return lo[0], hi[0], lo[1], hi[1]


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
        log.info("  %-10s %6.1f kg", g, kg)
    total, _, _ = com(ms)
    moving = sum(m.kg for m in ms if m.moving)
    log.info("  %-10s %6.1f kg   (riding on the lift: %.1f kg)", "TOTAL", total, moving)


def _report_balance(bodies: Sequence[Body], ms: Sequence[Mass], label: str) -> None:
    x0, x1, y0, y1 = _footprint(bodies)
    total, cx, cy = com(ms)
    w = total * G
    top_z = bbox(_select(bodies, "Upright_4040"))[1][2]
    log.info("\n[%s] total %.1f kg, COM x=%+.0f mm, y=%+.0f mm (+ = toward wall)", label, total, cx, cy)
    log.info("  feet: x %.0f..%.0f, y %.0f..%.0f mm", x0, x1, y0, y1)
    log.info("  margin to tip line: back %.0f, front %.0f, left %.0f, right %.0f mm",
             y1 - cy, cy - y0, cx - x0, x1 - cx)
    for h_in in SIT_STAND_IN:
        h = top_z + (h_in - MODEL_DESK_H_IN) * IN
        back, front = w * (y1 - cy) / h, w * (cy - y0) / h
        side = w * min(cx - x0, x1 - cx) / h
        log.info("  desk %4.1f in, push at upright top (%4.1f in): tips back at %4.0f N (%3.0f lbf), "
                 "forward %4.0f N, sideways %4.0f N", h_in, h / IN, back, back / 4.448, front, side)


def _report_legs(bodies: Sequence[Body], ms: Sequence[Mass]) -> None:
    legs = [b.center[1] for b in _select(bodies, "Leg")]
    yb, yf = max(legs), min(legs)
    total, _, cy = com([m for m in ms if m.moving])
    rear = (cy - yf) / (yb - yf)
    log.info("\nLift load: %.1f kg moving, COM y=%+.0f mm; legs at y=%+.0f/%+.0f", total, cy, yf, yb)
    log.info("  rear legs carry %.0f%% (%.1f kg each), front legs %.0f%% (%.1f kg each)",
             rear * 100, total * rear / 2, (1 - rear) * 100, total * (1 - rear) / 2)


def _report_crossbars(bodies: Sequence[Body], ms: Sequence[Mass]) -> None:
    bar = _by_label(bodies, "Crossbar_Low")
    span, x_left = bar.size[0], bar.lo[0]
    panel = next(p for p in ms if p.group == "panel")
    loads: list[tuple[float, float]] = []
    for m in ms:
        if m.group == "monitors":
            loads.append((m.kg * G / 2, m.x - x_left))  # stile ties both bars: half each
        elif "standoff" in m.name and " bar " in m.name:
            loads.append((panel.kg * G * PANEL_LOAD_SHARE, m.x - x_left))
    sag = _sag_mm(span, loads, KG_PER_M_2040 * G / 1000)
    log.info("\nCrossbar sag (each bar, pinned ends = upper bound): %.2f mm over %.0f mm "
             "(Misumi L/1000 = %.2f mm); bolted ends land ~40-60%% of this", sag, span, span / 1000)


def _on_side_joint(name: str) -> bool:
    """The side-rail joint itself (rails, its plates, gussets and bolts), not hung from it."""
    return name.startswith("SideRail_") or "side rail" in name or "Side bolt" in name


def _side_loads(ms: Sequence[Mass], x_r: float, x_l: float) -> dict[str, list[tuple[float, float]]]:
    """Split rail-system masses (not the side-rail joint) onto the R/L uprights by the lever rule."""
    side: dict[str, list[tuple[float, float]]] = {"R": [], "L": []}
    for m in ms:
        if m.group not in ("rails", "monitors", "panel", "hardware", "speakers") or _on_side_joint(m.name):
            continue
        fr = min(max((m.x - x_l) / (x_r - x_l), 0.0), 1.0)
        side["R"].append((m.kg * G * fr, m.y))
        side["L"].append((m.kg * G * (1 - fr), m.y))
    return side


def _report_joints(bodies: Sequence[Body], ms: Sequence[Mass]) -> None:
    up = {s: _by_label(bodies, f"Upright_{s}") for s in "RL"}
    ts_back = _by_label(bodies, "TopSupport_R").hi[1]
    face = up["R"].lo[1]
    log.info("\nSide joints (static; bolt spread %.0f mm assumed, last bolt at top-support rear end y=%.0f):",
             BOLT_SPREAD_MM, ts_back)
    for s, loads in _side_loads(ms, up["R"].center[0], up["L"].center[0]).items():
        v = sum(f for f, _ in loads)
        m_tee = sum(f * (y - face) for f, y in loads) / 1000
        m_bolt = sum(f * (y - ts_back) for f, y in loads) / 1000
        pull = m_bolt / (BOLT_SPREAD_MM / 1000)
        log.info("  %s: hangs %5.0f N (%4.1f kg); T-joint moment %+5.1f N*m; at top-support bolts "
                 "%5.1f N*m -> ~%4.0f N bolt pull", s, v, v / G, m_tee, m_bolt, pull)


def _report_ergonomics(bodies: Sequence[Body], params: Mapping[str, float]) -> None:
    """Screen top vs eye height and gaze angles (top edge at or a bit below eye level; center
    about 10-20 deg down). Eye point = the SKL_Eye skeleton datum, from its parameters."""
    if not {"desk_h", "eye_above_desk", "desk_front", "eye_back"} <= params.keys():
        log.warning("ergonomics skipped: eye parameters missing")
        return
    ey = params["desk_front"] - params["eye_back"]
    ez = params["desk_h"] + params["eye_above_desk"]
    log.info("\nErgonomics (eye point = eye_above_desk / eye_back; same relation sitting and standing):")
    for name in ("Monitor_Main", "Monitor_Side"):
        lo, hi = bbox(_select(bodies, name))
        top, mid = hi[2], (lo[2] + hi[2]) / 2
        dist = lo[1] - ey
        down = math.degrees(math.atan2(ez - mid, dist))
        verdict = "OK" if top <= ez + 25 else "HIGH: neck tilts up"
        log.info("  %s: top %+.1f in vs eye (%s); center %+.0f deg below eye; distance %.0f in",
                 name, (top - ez) / IN, verdict, down, dist / IN)
    for name in ("Speaker_R", "Speaker_L"):
        parts = [b for b in bodies if b.label == name and b.part_body.startswith("R40M_")]
        if parts:
            tw = bbox(parts)[1][2] - 3 * IN  # tweeter ~3 in below the top
            log.info("  %s: tweeter ~%+.1f in vs ear/eye height", name, (tw - ez) / IN)


def _run(report: Path) -> None:
    bodies = load_bodies(report)
    nominal = masses(bodies, 1)
    log.info("Mass budget (nominal):")
    _report_mass(nominal)
    _report_balance(bodies, nominal, "NOMINAL (model materials)")
    _report_balance(bodies, masses(bodies, 2, 2), "ALL HEAVY")
    _report_balance(bodies, masses(bodies, 0, 2, 1190.0),
                    "WORST: light frame+top, heavy monitors, acrylic panel")
    _report_legs(bodies, nominal)
    _report_crossbars(bodies, nominal)
    _report_joints(bodies, nominal)
    _report_ergonomics(bodies, load_params(report))


def main(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(argv) != 2:
        log.error(__doc__)
        return 2
    try:
        _run(Path(argv[1]))
    except ReportError as exc:
        log.error("audit: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
