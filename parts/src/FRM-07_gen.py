"""Generate parts/src/FRM-07L_HangerPlate_L.json and FRM-07R_HangerPlate_R.json (D21 hanger plates).

A hang_t x hang_w x hang_len steel flat bar on each top-support flange, under the desktop, overhanging the
4040 side rail. The rail hangs from it by M5 countersunk screws into drop-in T-nuts in both top slots, and
4 M5 countersunk screws + nylocs tie it to the flange. All 14 holes are the same M5 countersunk through hole,
so one sketch of points + one solid.hole feature (AGENTS §3: no feature per instance).

Hole stations (Y, from the top-support centre) are checked here against the evaluated skeleton
(tools/skeleton_values.py) so a layout change that pushes a screw onto a channel bar, a leg housing or off
the rail fails the generator instead of building silently.

Local frame (same as FRM-03): origin = top-support outer web face / top edge (frame_top) at Y = 0;
+Y toward the wall, plate on Z = 0 .. hang_t. R: rail side toward +X; L is its mirror (rail toward -X).
The hole pattern is weighted to the rear, so a 180 deg turn does not reproduce the other side: two files.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import skeleton_values  # noqa: E402

__all__ = ["TNUT_Y", "FLANGE_Y", "build", "check_stations", "main"]

TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
SKEL = {"command": "parameters.import", "params": {"path": f"{ROOT.as_posix()}/skeleton/params.json"}}
MATERIAL = "Steel powder-coated"
COLOR = "#1a1a1a"  # matte black powder coat, local shop (V2, D23)

# T-nut screw pairs (one per top slot) along the rail, 3 of 5 in the rear half where the hanging load is
# (side-rail-recommended-changes, Change 1). Expressions so they follow the skeleton.
TNUT_Y: tuple[str, ...] = ("-200 mm", "-20 mm", "130 mm", "195 mm", "255 mm")
# Flange screws: +/-hang_scr_y2 and +/-hang_scr_y, clear of the stock desktop-screw slots at 0 and +/-ts_ds_y.
# Symmetric, so the shared DSK-02 file (L = yaw 180) drills the same holes.
FLANGE_Y: tuple[str, ...] = ("-hang_scr_y", "-hang_scr_y2", "hang_scr_y2", "hang_scr_y")
TNUT_X = ("rail_l/4", "3*rail_l/4")          # HFS5-4040 top-slot centres, 10 and 30 mm in from the outer face
FLANGE_X = "-(ts_t + (ts_w - ts_t)/2)"       # mid-flange, inboard of the web outer face
CS_DIAMETER = 11.4                            # ISO 10642 M5 head dk max 11.2 + 0.2 seat clearance
NUT_R = 4.7                                   # M5 nyloc across corners (8 AF) / 2, rounded up
EDGE_MIN = 3.0                                # min material from a countersink edge to a plate edge
SLOT_END_MIN = 15.0                           # T-nut screw at least this far in from the rail's front end


class StationError(ValueError):
    """A hole station hits the frame or leaves the part it must land on."""


def _y(expr: str, v: Mapping[str, float]) -> float:
    num = expr.replace(" mm", "")
    if num.lstrip("-").replace(".", "").isdigit():
        return float(num)
    sign = -1.0 if num.startswith("-") else 1.0
    return sign * v[num.lstrip("-")]


def check_stations(v: Mapping[str, float]) -> None:
    """Raise StationError if a screw station collides or leaves its seat (values from the skeleton)."""
    y_front, y_rear = v["ts_len"] / 2 - v["hang_len"], v["ts_len"] / 2
    edge = CS_DIAMETER / 2 + EDGE_MIN
    # Under the flange, from the front channel bar's outer edge to its inner edge, then the housing (DSK-03/04).
    blocked = (v["leg_yc"] - v["ch_bar_gap"] / 2 - v["ch_bar_w"], v["leg_yc"] + v["ch_bar_gap"] / 2 + v["ch_bar_w"])
    for e in TNUT_Y + FLANGE_Y:
        y = _y(e, v)
        if not (y_front + edge <= y <= y_rear - edge):
            raise StationError(f"hole at y={y:.1f} is within {edge} mm of the plate ends {y_front:.1f}..{y_rear:.1f}")
    for e in TNUT_Y:
        if _y(e, v) < v["side_front"] + SLOT_END_MIN:
            raise StationError(f"T-nut at {e} is off or too near the rail front end ({v['side_front']:.1f})")
    for e in FLANGE_Y:
        y = abs(_y(e, v))
        if blocked[0] - NUT_R < y < blocked[1] + NUT_R:
            raise StationError(f"flange nut at |y|={y:.1f} hits a channel bar / leg housing ({blocked[0]:.1f}..{blocked[1]:.1f})")
    # Flange-screw nuts vs the desktop wood-screw heads under the flange slots (offset in X by only ~6 mm, so
    # treat it as a Y clearance).
    for e in FLANGE_Y:
        y = _y(e, v)
        for sy in (-v["ts_ds_y"], 0.0, v["ts_ds_y"]):
            if abs(y - sy) < v["ts_ds_l"] / 2 + v["ds_head_r"] + NUT_R:
                raise StationError(f"flange screw at y={y:.1f} hits the desktop screw in the slot at y={sy:.1f}")
    flange_x = -(v["ts_t"] + (v["ts_w"] - v["ts_t"]) / 2)
    if v["rail_l"] - v["hang_w"] > flange_x - edge:
        raise StationError("hang_w doesn't reach far enough inboard past the flange screw line")
    if (v["ts_w"] - v["ts_t"]) / 2 < NUT_R:
        raise StationError("flange nut doesn't fit between the web and the flange edge")


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def _points(sign: str) -> list[dict]:
    pts = [[f"{sign}({x})", y] for y in TNUT_Y for x in TNUT_X] + [[f"{sign}({FLANGE_X})", y] for y in FLANGE_Y]
    return [c("sketch.point", point=p) for p in pts]


def _desk_slots(side: str, v: Mapping[str, float]) -> list[dict]:
    """Clearance slots over the stock desktop-screw slots (numbers only: computed from the skeleton, AGENTS §3)."""
    x = -v["ts_ds_x"] if side == "R" else v["ts_ds_x"]
    w, ln = v["ts_ds_w"] + v["hang_ds_clr"], v["ts_ds_l"] + v["hang_ds_clr"]
    half = (ln - w) / 2
    return [c("sketch.create", plane="XY", offset="hang_t + 0.1 mm", name="Sketch_HangerDeskSlots"),
            *[c("sketch.slot.center_to_center", p0=[x, y - half], p1=[x, y + half], width=w)
              for y in (-v["ts_ds_y"], 0.0, v["ts_ds_y"])],
            c("sketch.finish"),
            c("solid.extrude", sketch="Sketch_HangerDeskSlots", distance="hang_t + 0.2 mm", direction="negative",
              operation="cut", targets=[f"HangerPlate_{side}"], name="Cut_HangerDeskSlots"),
            c("browser.visibility", visible=False, items=["Sketch_HangerDeskSlots"])]


def plate(side: str) -> list[dict]:
    sign = "" if side == "R" else "-"
    body = f"HangerPlate_{side}"
    x0 = "rail_l - hang_w" if side == "R" else "-rail_l"
    return [
        c("solid.box", name="Box_HangerPlate", body_name=body, length="hang_w", width="hang_len", height="hang_t",
          corner=[x0, "ts_len/2 - hang_len", "0 mm"]),
        c("sketch.create", plane="XY", offset="hang_t", name="Sketch_HangerHoles"),
        *_points(sign),
        c("sketch.finish"),
        c("solid.hole", name="Hole_M5_Csk", sketch="Sketch_HangerHoles", clearance="M5", fit="normal",
          type="countersink", cs_diameter=CS_DIAMETER, cs_angle="90 deg", targets=[body]),
        c("browser.visibility", visible=False, items=["Sketch_HangerHoles"]),
    ]


def finish(side: str) -> list[dict]:
    body = f"HangerPlate_{side}"
    outer = "+X" if side == "R" else "-X"
    desc = (f"Hanger plate {side} (D21): steel flat bar hang_t x hang_w x hang_len, black powder-coated (local shop, D23), on the top-support "
            f"flange under the desktop, flush with the side rail's outer ({outer}) face, rear end flush with the "
            "flange's rear end. 14 x M5 countersunk (ISO 10642) through holes: 5 pairs over the rail's top slots "
            "(T-nuts) and 4 on the mid-flange line (flange screws + nylocs); 3 desktop-screw clearance slots over the "
            "flange's stock slots. Origin: top-support outer web face / "
            "top edge at Y = 0, +Y toward wall, +Z up")
    return [
        c("material.assign", bodies=[body], material=MATERIAL),
        c("appearance.assign", bodies=[body], color=COLOR),
        c("document.metadata.set", values={
            "part_number": f"FRM-07{side}", "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {"Material": MATERIAL, "ReleaseState": "WIP",
                                "Source": "side-rail-recommended-changes.pdf Change 1 (2026-11-01), dimensions "
                                          "checked against the skeleton"},
        }),
    ]


def build(side: str) -> list[dict]:
    return [*TEMPLATE, SKEL, *plate(side), *_desk_slots(side, skeleton_values.values()), *finish(side)]


def main(sides: Sequence[str] = ("L", "R")) -> None:
    check_stations(skeleton_values.values())
    for side in sides:
        out = ROOT / f"parts/src/FRM-07{side}_HangerPlate_{side}.json"
        out.write_text(json.dumps({"generated_by": "parts/src/FRM-07_gen.py", "commands": build(side)}, indent=1),
                       encoding="utf-8")


if __name__ == "__main__":
    main()
