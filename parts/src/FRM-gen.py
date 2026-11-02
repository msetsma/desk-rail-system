"""Generate FRM part build scripts into parts/src/."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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
    out.write_text(json.dumps({"generated_by": "parts/src/FRM-gen.py", "commands": TEMPLATE + [SKEL] + cmds}, indent=1),
                   encoding="utf-8")


SRC_DXF = "Misumi HFS5 profile DXF (profiles/), length from skeleton"

write("FRM-01_Upright_4040", profile("Profile_HFS5_4040", "XY", DXF4040) + [
    c("solid.extrude", distance="up_below + hang_t + desk_t + up_above", body_name="Upright_4040", name="Extrude_Upright"),
] + finish("Upright_4040", AL, AL_COLOR, "FRM-01",
           "Upright, Misumi HFS5-4040, L = up_below + hang_t + desk_t + up_above. Origin: bottom end face centre, +Z up along the bar",
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

FELT = "PET felt"
FELT_COLOR = "#3a3c3f"  # dark grey PET felt (Felt Right "Cast" estimate, refs/visual_black_felt; confirm from samples)
FELT_SRC = "Modelled from skeleton; 12 mm dark grey PET felt board (refs/visual_black_felt), colour estimated (MEASURE)"
PNL_W, PNL_H = "(desk_w - 2*pnl_side)", "(pnl_drop + desk_t + pnl_above)"
COS45 = "0.70710678"


def _pt(x: str, z: str) -> list[str]:
    """XZ-plane sketch point for world (x, z): the XZ sketch's v axis is world -Z (tested 2026-11-02)."""
    return [x, f"-({z})"]


def _corner_arc(sx: int) -> dict:
    """Top-corner arc of radius pnl_r on side sx (+1 right, -1 left), drawn through its 45 deg point."""
    cx, cz = f"{sx}*({PNL_W}/2 - pnl_r)", f"{PNL_H} - pnl_r"
    return c("sketch.arc.three_point", start=_pt(f"{sx}*{PNL_W}/2", cz), end=_pt(cx, PNL_H),
             through=_pt(f"{cx} + {sx}*pnl_r*{COS45}", f"{cz} + pnl_r*{COS45}"))


write("FRM-05_Modesty_panel", [
    c("sketch.create", plane="XZ", name="Panel_Outline"),
    c("sketch.line", points=[_pt(f"-{PNL_W}/2", f"{PNL_H} - pnl_r"), _pt(f"-{PNL_W}/2", "0 mm"),
                             _pt(f"{PNL_W}/2", "0 mm"), _pt(f"{PNL_W}/2", f"{PNL_H} - pnl_r")]),
    _corner_arc(1),
    c("sketch.line", points=[_pt(f"({PNL_W}/2 - pnl_r)", PNL_H), _pt(f"-({PNL_W}/2 - pnl_r)", PNL_H)]),
    _corner_arc(-1),
    c("sketch.finish"),
    c("solid.extrude", distance="pnl_t", body_name="Modesty_Panel", name="Extrude_Panel"),
] + finish("Modesty_Panel", FELT, FELT_COLOR, "FRM-05",
           "Privacy panel, 12 mm PET felt, W = desk_w - 2*pnl_side, H = pnl_drop + desk_t + pnl_above, top corners R pnl_r (V1). "
           "Origin: bottom edge centre of the front (-Y) face, +Y toward the room, +Z up",
           FELT_SRC))

write("FRM-08_SidePanel", [
    c("solid.box", length="pnl_t", width="rail_l + pnl_back_gap + pnl_t", height=f"{PNL_H} - pnl_r",
      corner=["0 mm", "-(rail_l + pnl_back_gap + pnl_t)/2", "0 mm"], name="Box_SidePanel", body_name="Side_Panel"),
] + finish("Side_Panel", FELT, FELT_COLOR, "FRM-08",
           "Side panel (corner return), 12 mm PET felt on the upright's outer face, on 12 mm standoffs clear of the HPTTD5 "
           "screw heads (7.3 mm). D = rail_l + pnl_back_gap + pnl_t (upright front face to the privacy panel's back face), "
           "H = privacy panel height - pnl_r (top meets the corner arc's lower end). Origin: bottom edge centre of the inner (-X) face, "
           "+X outward; the L occurrence is the same file turned 180 deg about Z",
           FELT_SRC))


def knee_brace() -> list[dict]:
    """D20: 45 deg 2040 knee brace, 40 across X, in the side-rail plane, both ends mitred 45 deg.

    Origin: middle of the brace axis. The inside corner (upright front face / rail underside) sits at
    local (Y, Z) = (+brace_c, +brace_c); the brace runs from the upright (bottom end) up to the rail (top end).
    """
    h, top, w = "brace_c", "brace_c - brace_leg", "rail_s*sqrt(2)"
    # Axis direction (Y,Z) = (-1, 1)/sqrt2; the profile's 20 side lies along (1, 1)/sqrt2, its 40 side along X.
    plane = {"origin": [0, 0, 0], "x_dir": [0, 0.70710678, 0.70710678], "y_dir": [-1, 0, 0]}
    # Blank: the mitred trapezoid, end cuts exactly on the upright / rail faces; long sides overrun the
    # profile faces by 0.2 mm (measured along Y/Z) so the intersect has no coincident faces (AGENTS.md §3).
    blank = [[h, f"{top} - 0.2 mm"], [h, f"{top} + {w} + 0.2 mm"],
             [f"{top} + {w} + 0.2 mm", h], [f"{top} - 0.2 mm", h]]
    return profile("Profile_HFS5_2040", plane, DXF2040) + [
        c("solid.extrude", distance="2*brace_leg", direction="symmetric", body_name="Brace_2040", name="Extrude_Brace"),
        c("sketch.create", plane="YZ", name="Sketch_BraceMitre"),
        c("sketch.line", points=blank, closed=True),
        c("sketch.finish"),
        c("solid.extrude", sketch="Sketch_BraceMitre", distance="rail_l + 0.2 mm", direction="symmetric",
          operation="new", body_name="BraceBlank", name="Extrude_BraceBlank"),
        c("solid.combine", target="Brace_2040", tools=["BraceBlank"], operation="intersect", name="Intersect_BraceMitre"),
        c("browser.visibility", visible=False, items=["Sketch_BraceMitre"]),
    ] + finish("Brace_2040", AL, AL_COLOR, "FRM-06",
               "Knee brace (D20), Misumi HFS5-2040, 40 across X, both ends cut 45 deg; long edge = brace_leg*sqrt(2), "
               "from the upright front face up to the side-rail underside. Same part L and R. Origin: middle of the "
               "brace axis; the upright/rail inside corner is at local (Y, Z) = (brace_c, brace_c)",
               SRC_DXF + "; 45 deg mitre both ends")


write("FRM-06_Brace_2040", knee_brace())


def bolt_circles(sketch: str, offset: str, diameter: str, nominal: float, ys: list[str]) -> list[dict]:
    """One YZ sketch with a circle per bolt station, diameter driven by a skeleton parameter."""
    return [c("sketch.create", plane="YZ", offset=offset, name=sketch)] + [
        c("sketch.draw.dimensioned", command="sketch.circle.center",
          params={"center": [y, "-ts_bolt_z"], "diameter": nominal}, dimensions={"diameter": diameter})
        for y in ys
    ] + [c("sketch.finish")]


def side_rail(side: str) -> list[dict]:
    # D9: 4 M6 bolts per side, all into the leg columns' own threads (2 per column).
    holes = [f"ch_y_off + ({leg}) {off}" for leg in ("-leg_yc", "leg_yc")
             for off in ("- ts_bolt_pitch/2", "+ ts_bolt_pitch/2")]
    body = f"SideRail_{side}_4040"
    # R is built as the Y-mirrored L (drilled from -X, same boolean as L) then turned 180 deg about Z:
    # drilling R directly from +X hits a slow boolean retry on the DXF's ~1e-5 mm asymmetry.
    d1, d2 = ("up_y - rail_l/2", "-side_front") if side == "L" else ("-side_front", "up_y - rail_l/2")
    y0, y1 = ("side_front", "up_y - rail_l/2") if side == "L" else ("-(up_y - rail_l/2)", "-side_front")
    # Holes are drilled into a plain blank box (cheap), then the profile is intersected with
    # the blank: one boolean on the complex DXF body (~7.5 s) instead of solid.hole's ~46 s of retries.
    # Blank overruns the rail by 0.1 mm and the cutters overrun the blank by 0.1 mm (AGENTS.md §3).
    cmds = profile("Profile_HFS5_4040", "XZ", DXF4040, [-20.0, 20.0]) + [
        c("solid.extrude", distance=d1, distance2=d2, body_name=body, name="Extrude_SideRail"),
        c("solid.box", length="rail_l + 0.2 mm", width=f"({y1}) - ({y0}) + 0.2 mm", height="rail_l + 0.2 mm",
          corner=["-rail_l - 0.1 mm", f"({y0}) - 0.1 mm", "-rail_l - 0.1 mm"], operation="new",
          body_name="BoltBlank", name="Box_BoltBlank"),
    ] + bolt_circles("Sketch_BoltClear", "-rail_l - 0.2 mm", "sr_clear_d", 6.6, holes) + [
        c("solid.extrude", sketch="Sketch_BoltClear", distance="rail_l + 0.4 mm", operation="cut",
          targets=["BoltBlank"], name="Cut_BoltClear"),
        c("solid.combine", target=body, tools=["BoltBlank"], operation="intersect", name="Intersect_SideBolts"),
        c("browser.visibility", visible=False, items=["Sketch_BoltClear"]),
    ]
    if side == "R":
        cmds.append(c("solid.move", bodies=[body], axis=[0, 0, 1], angle="180 deg", name="Rotate_to_R"))
    outer = "-X" if side == "L" else "+X"
    return cmds + finish(body, AL, AL_COLOR, f"FRM-03{side}",
                         f"Side rail {side}, Misumi HFS5-4040 drilled for 4 M6 through-bolts (D9): Ø sr_clear_d straight through both walls, M6x55 heads on the outer ({outer}) face; at ts_bolt_z below the top, Y = ch_y_off ± leg_yc ± ts_bolt_pitch/2 (leg screws, into the leg columns' threads). Ends: side_front .. up_y - rail_l/2. Origin: top edge of the inner (mating) face at the top-support centre station (Y=0), +Y toward wall, +Z up",
                         SRC_DXF + "; holes per D9")


write("FRM-03L_SideRail_L_4040", side_rail("L"))
write("FRM-03R_SideRail_R_4040", side_rail("R"))
