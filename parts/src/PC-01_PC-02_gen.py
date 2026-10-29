"""Generate the build scripts for PC-01 (Fractal North case) and PC-02 (walnut slat front).

Run: python parts/src/PC-01_PC-02_gen.py
Writes parts/src/PC-01_FractalNorth.json and parts/src/PC-02_WalnutSlatFront.json.

Geometry is driven by skeleton parameters (pc_*, slat_*) plus a few fixed vendor constants
(pcn_*) measured from the official Fractal renders (see refs/fractal_north/README.md).
Fillet edge picks are numeric points computed here from the current skeleton values; SolidCraft
tracks the picked edges through later parameter changes.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

sys.path.insert(0, "C:/Users/2015m/DEV/CAD/desk/tools")
import skeleton_values  # noqa: E402

__all__ = ["build_pc01", "build_pc02", "main"]

ROOT = Path(__file__).resolve().parents[2]
SKELETON = "C:/Users/2015m/DEV/CAD/desk/skeleton/params.json"
TEMPLATE = ROOT / "parts" / "_template.json"

CHARCOAL = "#333437"
BRASS = "#b08d57"
LEATHER = "#7a4a2c"
WALNUT = "#634433"

# Top I/O, X centres in mm from the case centre line (measured on top_io.jpg).
IO_Y = "-pc_d/2 + 45 mm"
BUTTON_X = -72.7
JACK_X = (-48.8, -32.2)
USBA_X = (-12.8, 11.2)
USBC_X = 33.5
LINE_X = (40.0, 80.0)

Cmd = dict[str, Any]


def cmd(command: str, **params: Any) -> Cmd:
    return {"command": command, "params": params}


def header(local_params: Sequence[tuple[str, str, str]]) -> list[Cmd]:
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))["commands"]
    cmds = list(template) + [cmd("parameters.import", path=SKELETON)]
    cmds += [cmd("parameters.add", name=n, expression=e, comment=c) for n, e, c in local_params]
    return cmds


def rect(x0: str, y0: str, x1: str, y1: str) -> Cmd:
    return cmd("sketch.line", closed=True, points=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]])


def finish(body: str, material: str, color: str) -> list[Cmd]:
    return [
        cmd("material.assign", bodies=[body], material=material),
        cmd("appearance.assign", bodies=[body], color=color),
    ]


def metadata(pn: str, desc: str, material: str, source: str) -> Cmd:
    return cmd(
        "document.metadata.set",
        values={
            "part_number": pn,
            "description": desc,
            "revision": "A",
            "project": "desk",
            "com.setsma.desk": {"Material": material, "ReleaseState": "WIP", "Source": source},
        },
    )


SHARED_PARAMS = [
    ("pcn_foot_h", "19 mm", "Fractal North feet height (spec: 469 overall - 450 w/o feet)"),
    ("pcn_frame_d", "slat_inset + slat_t + 3 mm", "Front panel frame depth (Y): slat recess + slats + 3 mm rails"),
    ("pcn_edge_r", "6 mm", "Fractal North long-edge radius (MEASURE from renders)"),
]


def _y_edges(x: float, z0: float, z1: float, y: float) -> list[list[float]]:
    return [[-x, y, z0], [x, y, z0], [-x, y, z1], [x, y, z1]]


def build_pc01(v: Mapping[str, float]) -> list[Cmd]:
    body = "PC_FractalNorth"
    brass = "PC_North_Brass"
    body_h = "(pc_h - pcn_foot_h)"
    rear_y = "(pc_d/2 - pcn_rear)"
    w2, d2, foot_h, rear = v["pc_w"] / 2, v["pc_d"] / 2, 19.0, 9.0
    frame_d = v["slat_inset"] + v["slat_t"] + 3.0
    y_mid = (-d2 + frame_d + d2 - rear) / 2
    feet_x, feet_yf, feet_yr = "pc_w/2 - 25 mm", "-pc_d/2 + 34 mm", "pc_d/2 - pcn_rear - 32 mm"
    feet = [[f"-({feet_x})", feet_yf], [feet_x, feet_yf], [f"-({feet_x})", feet_yr], [feet_x, feet_yr]]

    c = header(SHARED_PARAMS + [
        ("pcn_rear", "9 mm", "Rear thumbscrew protrusion (MEASURE, side render)"),
        ("pcn_front_d", "102 mm", "Front section depth: front to top-mesh / side-panel seam (MEASURE)"),
    ])
    c += [
        cmd("solid.box", name="PC01_Body", body_name=body, operation="new",
            length="pc_w", width="pc_d - pcn_frame_d - pcn_rear", height=body_h,
            corner=["-pc_w/2", "-pc_d/2 + pcn_frame_d", f"-{body_h}"]),
        cmd("solid.fillet", name="PC01_EdgeRound", radius="pcn_edge_r",
            edges=_y_edges(w2, 0.0, -(v["pc_h"] - foot_h), y_mid)),
        # Top mesh panel: shallow recess behind the I/O strip, plus vent slots under the mesh.
        cmd("solid.box", name="PC01_TopMeshRecess", operation="cut", targets=[body],
            length="pc_w - 28 mm", width="pc_d - pcn_front_d - pcn_rear - 12 mm", height="1.1 mm",
            corner=["-pc_w/2 + 14 mm", "-pc_d/2 + pcn_front_d", "-1 mm"]),
        cmd("sketch.create", plane="XY", offset="-0.9 mm", name="PC01_TopVent_Sketch"),
        rect("-pc_w/2 + 20 mm", "-pc_d/2 + pcn_front_d + 10 mm",
             "-pc_w/2 + 24 mm", "-pc_d/2 + pcn_front_d + 34 mm"),
        cmd("sketch.pattern.rectangular", entities=["l1", "l2", "l3", "l4"], count=18,
            spacing="(pc_w - 44 mm) / 17", dir=[1, 0], count2=10,
            spacing2="(pc_d - pcn_front_d - pcn_rear - 66 mm) / 9", dir2=[0, 1]),
        cmd("sketch.finish"),
        cmd("solid.extrude", name="PC01_TopVent", sketch="PC01_TopVent_Sketch", distance="2.1 mm",
            direction="negative", operation="cut", targets=[body]),
        # Left (mesh) side panel recess and right-side front-section seam.
        cmd("solid.box", name="PC01_SideMeshRecess", operation="cut", targets=[body],
            length="0.9 mm", width="pc_d - pcn_front_d - pcn_rear - 3 mm", height=f"{body_h} - 32 mm",
            corner=["-pc_w/2 - 0.1 mm", "-pc_d/2 + pcn_front_d", f"-{body_h} + 25 mm"]),
        cmd("solid.box", name="PC01_SideSeam_R", operation="cut", targets=[body],
            length="0.7 mm", width="1 mm", height=f"{body_h} + 0.2 mm",
            corner=["pc_w/2 - 0.6 mm", "-pc_d/2 + pcn_front_d - 0.5 mm", f"-{body_h} - 0.1 mm"]),
        # Top I/O: jacks, USB-A x2, USB-C, power button and accent-line pockets.
        cmd("sketch.create", plane="XY", offset="0.1 mm", name="PC01_TopIO_Sketch"),
        cmd("sketch.circle.center", center=[str(BUTTON_X) + " mm", IO_Y], diameter=16),
        *[cmd("sketch.circle.center", center=[f"{x} mm", IO_Y], diameter=6) for x in JACK_X],
        *[rect(f"{x - 6.5} mm", f"{IO_Y} - 2.75 mm", f"{x + 6.5} mm", f"{IO_Y} + 2.75 mm") for x in USBA_X],
        rect(f"{USBC_X - 4.5} mm", f"{IO_Y} - 1.75 mm", f"{USBC_X + 4.5} mm", f"{IO_Y} + 1.75 mm"),
        rect(f"{LINE_X[0]} mm", f"{IO_Y} - 0.6 mm", f"{LINE_X[1]} mm", f"{IO_Y} + 0.6 mm"),
        cmd("sketch.finish"),
        cmd("solid.extrude", name="PC01_TopIO", sketch="PC01_TopIO_Sketch", distance="4.1 mm",
            direction="negative", operation="cut", targets=[body]),
        # Rear side-panel thumbscrews (4).
        cmd("sketch.create", plane="XZ", offset=f"{rear_y} - 0.1 mm", name="PC01_Thumbscrew_Sketch"),
        *[cmd("sketch.circle.center", center=[x, z], diameter=10)
          for x in ("-(pc_w/2 - 8 mm)", "pc_w/2 - 8 mm") for z in ("22 mm", f"{body_h} - 40 mm")],
        cmd("sketch.finish"),
        cmd("solid.extrude", name="PC01_Thumbscrews", sketch="PC01_Thumbscrew_Sketch",
            distance="pcn_rear + 0.1 mm", operation="join", targets=[body]),
        # Feet: black upper part joined to the case, brass base ring as its own finish body.
        cmd("sketch.create", plane="XY", offset=f"-{body_h} + 0.1 mm", name="PC01_Feet_Sketch"),
        *[cmd("sketch.circle.center", center=p, diameter=22) for p in feet],
        cmd("sketch.finish"),
        cmd("solid.extrude", name="PC01_Feet", sketch="PC01_Feet_Sketch", distance="pcn_foot_h - 6 mm + 0.1 mm",
            direction="negative", operation="join", targets=[body]),
        cmd("sketch.create", plane="XY", offset="-pc_h", name="PC01_FeetBrass_Sketch"),
        *[cmd("sketch.circle.center", center=p, diameter=22) for p in feet],
        cmd("sketch.finish"),
        cmd("solid.extrude", name="PC01_FeetBrass", sketch="PC01_FeetBrass_Sketch", distance="6 mm",
            operation="new", body_name=brass),
        cmd("solid.cylinder", name="PC01_PowerButton", diameter=16, height="4.8 mm",
            base=[f"{BUTTON_X} mm", IO_Y, "-4 mm"], operation="new", body_name="PC_North_Button"),
        cmd("solid.box", name="PC01_AccentLine", operation="new", body_name="PC_North_AccentLine",
            length=f"{LINE_X[1] - LINE_X[0]} mm", width="1.2 mm", height="1 mm",
            corner=[f"{LINE_X[0]} mm", f"{IO_Y} - 0.6 mm", "-1 mm"]),
        cmd("solid.combine", target=brass, operation="join",
            tools=[f"{brass} ({i})" for i in (2, 3, 4)] + ["PC_North_Button", "PC_North_AccentLine"]),
        cmd("timeline.rename", feature="Combine1", name="PC01_Brass_Join"),
        cmd("solid.box", name="PC01_PullTab", operation="new", body_name="PC_North_PullTab",
            length="16 mm", width="pcn_rear + 3 mm", height="1.5 mm",
            corner=["-8 mm", f"{rear_y} - 4 mm", "0 mm"]),
    ]
    c += finish(body, "Steel powder-coated", CHARCOAL)
    c += finish(brass, "Steel zinc-plated", BRASS)
    c += finish("PC_North_PullTab", "PC", LEATHER)
    c.append(metadata(
        "PC-01",
        "Fractal Design North, Charcoal Black, Mesh side (visual model: body with rounded long edges, "
        "top mesh + I/O strip, left mesh panel, feet, rear thumbscrews; front panel is PC-02). "
        "Origin: top face centre of the case body; front at -Y, X right, Z up. "
        "Bodies: PC_FractalNorth (charcoal), PC_North_Brass (feet rings, power button, accent line), "
        "PC_North_PullTab (leather tab).",
        "Steel powder-coated",
        "Fractal North product sheet (447 x 215 x 469 mm) + official renders, refs/fractal_north/",
    ))
    return c


def build_pc02(v: Mapping[str, float]) -> list[Cmd]:
    frame, slats = "PC_FrontFrame", "PC_FrontSlats"
    body_h = "(pc_h - pcn_foot_h)"
    w2, h2 = v["pc_w"] / 2, v["pc_h"] / 2
    frame_d = v["slat_inset"] + v["slat_t"] + 3.0
    y_mid = -v["slat_inset"] + frame_d / 2
    x0 = "-pc_w/2 + pc_bezel + slat_gap"

    c = header(SHARED_PARAMS + [("pcn_lip", "5 mm", "Front frame visible lip width (MEASURE, front render)")])
    c += [
        cmd("solid.box", name="PC02_Frame", body_name=frame, operation="new",
            length="pc_w", width="pcn_frame_d", height=body_h,
            corner=["-pc_w/2", "-slat_inset", "-pc_h/2 + pcn_foot_h"]),
        cmd("solid.fillet", name="PC02_FrameEdgeRound", radius="pcn_edge_r",
            edges=_y_edges(w2, h2, -h2 + 19.0, y_mid)),
        cmd("solid.box", name="PC02_FrameOpening", operation="cut", targets=[frame],
            length="pc_w - 2*pcn_lip", width="slat_inset + slat_t + 0.1 mm", height=f"{body_h} - 2*pcn_lip",
            corner=["-pc_w/2 + pcn_lip", "-slat_inset - 0.1 mm", "-pc_h/2 + pcn_foot_h + pcn_lip"]),
        cmd("solid.box", name="PC02_FrameBackOpening", operation="cut", targets=[frame],
            length="pc_w - 2*pcn_lip", width="3.2 mm", height=f"{body_h} - 2*pc_bezel_v - 16 mm",
            corner=["-pc_w/2 + pcn_lip", "slat_t - 0.1 mm", "-pc_h/2 + pcn_foot_h + pc_bezel_v + 8 mm"]),
        # Slats: XZ sketch (sketch v = -Z), 10 slats patterned in X.
        cmd("sketch.create", plane="XZ", name="PC02_Slats_Sketch"),
        rect(x0, "-(pc_h/2 - pc_bezel_v)", f"{x0} + slat_w", "pc_h/2 - pcn_foot_h - pc_bezel_v"),
        cmd("sketch.pattern.rectangular", entities=["l1", "l2", "l3", "l4"], count=10,
            spacing="slat_w + slat_gap", dir=[1, 0]),
        cmd("sketch.finish"),
        cmd("solid.extrude", name="PC02_Slats", sketch="PC02_Slats_Sketch", distance="slat_t",
            operation="new", body_name=slats),
        cmd("solid.combine", target=slats, tools=[f"{slats} ({i})" for i in range(2, 11)], operation="join"),
        cmd("timeline.rename", feature="Combine1", name="PC02_Slats_Join"),
    ]
    c += finish(slats, "Walnut", WALNUT)
    c += finish(frame, "Steel powder-coated", CHARCOAL)
    c.append(metadata(
        "PC-02",
        "Fractal North front panel, dark walnut: 10 vertical walnut slats in the charcoal front frame "
        "(5 mm lip, top/bottom rails). Origin: placement datum on the slat front face, X centred, "
        "Z = case height centre incl. feet (slat array centre is pcn_foot_h/2 above it); "
        "slats extend +Y (toward wall), X right, Z up.",
        "Walnut",
        "Fractal North official renders (refs/fractal_north/), sizes from skeleton slat_* / pc_*",
    ))
    return c


def main() -> None:
    v = skeleton_values.values()
    out = ROOT / "parts" / "src"
    for name, cmds in (("PC-01_FractalNorth", build_pc01(v)), ("PC-02_WalnutSlatFront", build_pc02(v))):
        (out / f"{name}.json").write_text(json.dumps({"generated_by": "parts/src/PC-01_PC-02_gen.py", "commands": cmds}, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
