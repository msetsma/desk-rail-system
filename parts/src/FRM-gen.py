"""Generate FRM part build scripts into parts/src/."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("C:/Users/2015m/DEV/CAD/desk")
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
SKEL = {"command": "parameters.import", "params": {"path": "C:/Users/2015m/DEV/CAD/desk/skeleton/params.json"}}
DXF4040 = "C:/Users/2015m/DEV/CAD/desk/profiles/misumi_hfs5_4040.dxf"
DXF2040 = "C:/Users/2015m/DEV/CAD/desk/profiles/misumi_hfs5_2040.dxf"
AL = "Al 6063-T5"
AL_COLOR = "#d4d8dd"


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def finish(body: str, material: str, color: str, pn: str, desc: str, source: str) -> list[dict]:
    return [
        c("material.assign", bodies=[body], material=material),
        c("appearance.assign", bodies=[body], color=color),
        c("document.metadata.set", values={
            "part_number": pn, "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {"Material": material, "ReleaseState": "WIP", "Source": source},
        }),
    ]


def profile(name: str, plane: object, dxf: str, at: list[float] | None = None) -> list[dict]:
    ins = {"path": dxf} if at is None else {"path": dxf, "at": at}
    return [c("sketch.create", plane=plane, name=name), c("sketch.insert_dxf", **ins), c("sketch.finish")]


def write(fname: str, cmds: list[dict]) -> None:
    out = ROOT / "parts/src" / f"{fname}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"commands": TEMPLATE + [SKEL] + cmds}, indent=1), encoding="utf-8")


SRC_DXF = "Misumi HFS5 profile DXF (profiles/), length from skeleton"

write("FRM-01_Upright_4040", profile("Profile_HFS5_4040", "XY", DXF4040) + [
    c("solid.extrude", distance="up_below + desk_t + up_above", body_name="Upright_4040", name="Extrude_Upright"),
] + finish("Upright_4040", AL, AL_COLOR, "FRM-01",
           "Upright, Misumi HFS5-4040, L = up_below + desk_t + up_above. Origin: bottom end face centre, +Z up along the bar",
           SRC_DXF))

write("FRM-02_Crossbar_2040", profile("Profile_HFS5_2040", "YZ", DXF2040) + [
    c("solid.extrude", distance="2*up_xc - rail_l", direction="symmetric", body_name="Crossbar_2040", name="Extrude_Crossbar"),
] + finish("Crossbar_2040", AL, AL_COLOR, "FRM-02",
           "Crossbar, Misumi HFS5-2040 (40 in Z, 20 in Y), L = 2*up_xc - rail_l (between upright inner faces). Origin: profile centre at mid-length, +X along the bar",
           SRC_DXF))

write("FRM-04_Stile_2040", profile("Profile_HFS5_2040", {"origin": [0, 0, 0], "x_dir": [0, 1, 0], "y_dir": [-1, 0, 0]}, DXF2040) + [
    c("solid.extrude", distance="bar2_z - bar1_z - rail_l", body_name="Stile_2040", name="Extrude_Stile"),
] + finish("Stile_2040", AL, AL_COLOR, "FRM-04",
           "Stile, Misumi HFS5-2040 (40 in X, 20 in Y), L = bar2_z - bar1_z - rail_l (between crossbars). Origin: bottom end face centre, +Z up along the bar",
           SRC_DXF))

write("FRM-05_Modesty_panel", [
    c("solid.box", length="desk_w - 2*pnl_side", width="pnl_t", height="pnl_drop + desk_t + pnl_above",
      corner=["-(desk_w - 2*pnl_side)/2", "0 mm", "0 mm"], name="Box_Panel", body_name="Modesty_Panel"),
] + finish("Modesty_Panel", "MDF", "#4f6d7a", "FRM-05",
           "Modesty / privacy panel, 1/4 in sheet, W = desk_w - 2*pnl_side, H = pnl_drop + desk_t + pnl_above. Origin: bottom edge centre of the front (-Y) face, +Y toward the room, +Z up",
           "Modelled from skeleton (legacy ModestyPanel); colour from legacy model"))


def side_rail(side: str) -> list[dict]:
    s = -1 if side == "L" else 1
    sgn = "-" if side == "L" else ""
    holes = []
    for leg in ("-leg_yc", "leg_yc"):
        for off in ("- ts_bolt_pitch/2", "+ ts_bolt_pitch/2", "- (ch_bar_gap + ch_bar_w)/2", "+ (ch_bar_gap + ch_bar_w)/2"):
            holes.append(f"ch_y_off + ({leg}) {off}")
    body = f"SideRail_{side}_4040"
    # R is built as the Y-mirrored L (drilled from -X, same boolean as L) then turned 180 deg about Z:
    # drilling R directly from +X hits a slow boolean retry on the DXF's ~1e-5 mm asymmetry.
    d1, d2 = ("up_y - rail_l/2", "-side_front") if side == "L" else ("-side_front", "up_y - rail_l/2")
    cmds = profile("Profile_HFS5_4040", "XZ", DXF4040, [-20.0, 20.0]) + [
        c("solid.extrude", distance=d1, distance2=d2, body_name=body, name="Extrude_SideRail"),
        c("sketch.create", plane="YZ", offset="-rail_l", name="Sketch_BoltHoles"),
    ] + [c("sketch.point", point=[y, "-ts_bolt_z"]) for y in holes] + [
        c("sketch.finish"),
        c("solid.hole", sketch="Sketch_BoltHoles", type="counterbore", diameter="sr_clear_d",
          cb_diameter="sr_access_d", cb_depth="rail_l - sr_seat_t", targets=[body], name="Hole_SideBolts"),
        c("browser.visibility", visible=False, items=["Sketch_BoltHoles"]),
    ]
    if side == "R":
        cmds.append(c("solid.move", bodies=[body], axis=[0, 0, 1], angle="180 deg", name="Rotate_to_R"))
    outer = "-X" if side == "L" else "+X"
    return cmds + finish(body, AL, AL_COLOR, f"FRM-03{side}",
                         f"Side rail {side}, Misumi HFS5-4040 drilled for 8 M6 through-bolts (D9): Ø sr_access_d access from the outer ({outer}) face to a sr_seat_t seat, Ø sr_clear_d through the inner wall; at ts_bolt_z below the top, Y = ch_y_off ± leg_yc ± ts_bolt_pitch/2 (leg screws) and ± (ch_bar_gap+ch_bar_w)/2 (channel bars). Ends: side_front .. up_y - rail_l/2. Origin: top edge of the inner (mating) face at the top-support centre station (Y=0), +Y toward wall, +Z up",
                         SRC_DXF + "; holes per D9")


write("FRM-03L_SideRail_L_4040", side_rail("L"))
write("FRM-03R_SideRail_R_4040", side_rail("R"))
