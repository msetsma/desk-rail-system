"""Generate parts/src/LAP-02_MacBookPro14.json (Apple MacBook Pro 14in, M4, 2024, lid open).

Purchased fixed-shape model; it imports the skeleton for the lid angle (`lap_lid`, screen at the
monitor tilt) and the tray tilt (`lap_kb_tilt` about the jig hinge axis at `lap_hinge_z`, front edge down). Apple dimensions are local `mbp14_*` parameters
(prefix chosen so they never clash with the skeleton's `mbp_w` / `mbp_d`).
Sources and estimates: refs/macbook_pro_14/README.md.

Local frame: origin = footprint centre on the bottom plane of the feet (the tray surface it rests
on), before the tilt; the tilt turns the laptop about local X at z = lap_hinge_z. +Y toward the hinge (wall side), screen faces -Y (toward the user), X right, Z up.

The lid is built closed with its hinge line on the world X axis, rotated open by the parameter
`mbp14_lid_open` (solid.move axis/angle takes an expression), then translated onto the hinge.
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["build", "main"]

ROOT = Path("C:/Users/2015m/DEV/CAD/desk")
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
OUT = ROOT / "parts/src/LAP-02_MacBookPro14.json"
SKEL = {"command": "parameters.import", "params": {"path": f"{ROOT.as_posix()}/skeleton/params.json"}}

BASE, LID, SCREEN, KEYS, PAD = "MBP_Base", "MBP_Lid", "MBP_Screen", "MBP_Keyboard", "MBP_Trackpad"
MATERIAL = "Al 6063-T5"  # closest template alloy (Apple uses a 6000-series recycled Al)
MATERIAL_SCREEN = "PC"  # stand-in for cover glass (template has no glass)
COLOR_ALU = "#2e2f31"  # Space Black anodised Al; Silver finish would be "#d9dadc" (user hasn't said which)
COLOR_SCREEN = "#050608"  # glossy black glass, panel off
COLOR_KEYS = "#0b0c0d"  # black keycaps
ALU_PBR = {"metallic": 0.9, "roughness": 0.45, "dielectric_ior": 1.5}
GLASS_PBR = {"metallic": 0.0, "roughness": 0.06, "dielectric_ior": 1.5}

# name, expression, comment (MEASURE = estimate, see refs/macbook_pro_14/README.md)
PARAMS: list[tuple[str, str, str]] = [
    ("mbp14_w", "312.6 mm", "Width (Apple tech specs 121552)"),
    ("mbp14_d", "221.2 mm", "Depth (Apple tech specs 121552)"),
    ("mbp14_h", "15.5 mm", "Closed height incl. feet (Apple tech specs 121552)"),
    ("mbp14_foot_h", "0.9 mm", "MEASURE foot height below the base bottom (photos)"),
    ("mbp14_lid_t", "5.0 mm", "MEASURE lid thickness (side photos, ~1/3 of height)"),
    ("mbp14_base_t", "mbp14_h - mbp14_foot_h - mbp14_lid_t", "Base slab thickness (9.6)"),
    ("mbp14_r", "9 mm", "MEASURE plan-view corner radius, base and lid (photos)"),
    ("mbp14_lid_d", "mbp14_d - 1 mm", "MEASURE lid depth (lid sits ~flush with the base front)"),
    ("mbp14_lid_open", "lap_lid", "Lid opening angle from the base top (skeleton: screen at the monitor tilt)"),
    ("mbp14_foot_dia", "13 mm", "MEASURE rubber foot diameter (photos)"),
    ("mbp14_foot_ix", "25 mm", "MEASURE foot centre in from the side edges"),
    ("mbp14_foot_iy", "18 mm", "MEASURE foot centre in from the front/back edges"),
    ("mbp14_kb_w", "276 mm", "MEASURE keyboard well width (14.5 keys at ~19 mm pitch)"),
    ("mbp14_kb_d", "112 mm", "MEASURE keyboard well depth (6 rows incl. full-height F row)"),
    ("mbp14_kb_rear", "10 mm", "MEASURE base rear edge to keyboard well"),
    ("mbp14_kb_dep", "1.0 mm", "MEASURE keyboard well depth below the deck"),
    ("mbp14_key_recess", "0.2 mm", "MEASURE key tops below the deck"),
    ("mbp14_tp_w", "132 mm", "Trackpad width (NanoReview 13.2 cm; MEASURE)"),
    ("mbp14_tp_d", "81 mm", "Trackpad depth (NanoReview 8.1 cm; MEASURE)"),
    ("mbp14_tp_front", "8 mm", "MEASURE base front edge to trackpad"),
    ("mbp14_tp_dep", "0.4 mm", "MEASURE trackpad glass inset depth"),
    ("mbp14_scr_rim", "1.5 mm", "MEASURE aluminium rim around the black cover glass"),
    ("mbp14_scr_chin", "8 mm", "MEASURE hinge-side lid strip without glass (hinge cover)"),
    ("mbp14_scr_t", "0.3 mm", "Cover glass proud of the lid inner face (modelling choice)"),
    ("mbp14_aa_w", "302.4 mm", "Active area width (3024 px at 254 ppi)"),
    ("mbp14_aa_h", "196.4 mm", "Active area height (1964 px at 254 ppi)"),
]

Z_DECK = "mbp14_foot_h + mbp14_base_t"  # base top surface
HINGE_Y = "mbp14_d/2"
HINGE_Z = f"{Z_DECK} + mbp14_lid_t/2 + 0.1 mm"  # barrel radius lid_t/2 + 0.1 mm sits on the deck (no coincident faces with the slab)


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def params_cmd() -> dict:
    rows = [{"name": n, "expression": e, "comment": k} for n, e, k in PARAMS]
    return c("parameters.import", text=json.dumps(rows))


def corner_edges(w: float, d: float, y0: float, z: float) -> list[list[float]]:
    """Points on the 4 vertical edges of a w x d box spanning y0..y0+d (default-param mm)."""
    return [[sx * w / 2, y, z] for sx in (-1, 1) for y in (y0, y0 + d)]


def base(d: dict[str, float]) -> list[dict]:
    zm = d["foot_h"] + d["base_t"] / 2
    return [
        c("solid.box", name="MBP14_BaseSlab", body_name=BASE, operation="new",
          corner=["-mbp14_w/2", "-mbp14_d/2", "mbp14_foot_h"],
          length="mbp14_w", width="mbp14_d", height="mbp14_base_t"),
        c("solid.fillet", name="MBP14_BaseCorners", radius="mbp14_r",
          edges=corner_edges(d["w"], d["d"], -d["d"] / 2, zm)),
        c("solid.cylinder", name="MBP14_Foot", operation="join", targets=[BASE],
          diameter="mbp14_foot_dia", height="mbp14_foot_h + 0.1 mm",
          base=["-mbp14_w/2 + mbp14_foot_ix", "-mbp14_d/2 + mbp14_foot_iy", "0 mm"]),
        c("solid.pattern.rectangular", name="MBP14_Feet", features=["MBP14_Foot"],
          dir1=[1, 0, 0], count1=2, spacing1="mbp14_w - 2*mbp14_foot_ix",
          dir2=[0, 1, 0], count2=2, spacing2="mbp14_d - 2*mbp14_foot_iy"),
    ]


def keyboard() -> list[dict]:
    y0 = "mbp14_d/2 - mbp14_kb_rear - mbp14_kb_d"
    return [
        c("solid.box", name="MBP14_KeyboardWell", operation="cut", targets=[BASE],
          corner=["-mbp14_kb_w/2", y0, f"{Z_DECK} - mbp14_kb_dep"],
          length="mbp14_kb_w", width="mbp14_kb_d", height="mbp14_kb_dep + 0.1 mm"),
        c("solid.box", name="MBP14_Keys", body_name=KEYS, operation="new",
          corner=["-mbp14_kb_w/2", y0, f"{Z_DECK} - mbp14_kb_dep"],
          length="mbp14_kb_w", width="mbp14_kb_d", height="mbp14_kb_dep - mbp14_key_recess"),
    ]


def trackpad() -> list[dict]:
    y0 = "-mbp14_d/2 + mbp14_tp_front"
    return [
        c("solid.box", name="MBP14_TrackpadPocket", operation="cut", targets=[BASE],
          corner=["-mbp14_tp_w/2", y0, f"{Z_DECK} - mbp14_tp_dep"],
          length="mbp14_tp_w", width="mbp14_tp_d", height="mbp14_tp_dep + 0.1 mm"),
        c("solid.box", name="MBP14_TrackpadGlass", body_name=PAD, operation="new",
          corner=["-mbp14_tp_w/2", y0, f"{Z_DECK} - mbp14_tp_dep"],
          length="mbp14_tp_w", width="mbp14_tp_d", height="mbp14_tp_dep"),
    ]


def lid(d: dict[str, float]) -> list[dict]:
    """Lid built closed with the hinge line on world X (lid spans y -lid_d..0, z -t/2..t/2)."""
    return [
        c("solid.box", name="MBP14_LidSlab", body_name=LID, operation="new",
          corner=["-mbp14_w/2", "-mbp14_lid_d", "-mbp14_lid_t/2"],
          length="mbp14_w", width="mbp14_lid_d", height="mbp14_lid_t"),
        c("solid.fillet", name="MBP14_LidCorners", radius="mbp14_r",
          edges=corner_edges(d["w"], d["lid_d"], -d["lid_d"], 0.0)),
        c("solid.box", name="MBP14_CoverGlass", body_name=SCREEN, operation="new",
          corner=["-mbp14_w/2 + mbp14_scr_rim", "-mbp14_lid_d + mbp14_scr_rim", "-mbp14_lid_t/2 - mbp14_scr_t"],
          length="mbp14_w - 2*mbp14_scr_rim", width="mbp14_lid_d - mbp14_scr_rim - mbp14_scr_chin",
          height="mbp14_scr_t"),
        # rounded hinge end (display wraps the hinge): the lid's end face sits on this barrel, so the opened lid
        # meets the deck at the hinge line with no wedge gap
        c("solid.cylinder", name="MBP14_HingeBarrel", axis="X", operation="join", targets=[LID],
          radius="mbp14_lid_t/2 + 0.1 mm", height="mbp14_w - 2*mbp14_r", base=["-(mbp14_w/2 - mbp14_r)", "0 mm", "0 mm"]),
        # axis -X: the free end swings up and back toward +Y
        c("solid.move", name="MBP14_LidOpen", bodies=[LID, SCREEN], axis=[-1, 0, 0], angle="mbp14_lid_open"),
        c("solid.move", name="MBP14_LidToHinge", bodies=[LID, SCREEN], translate=["0 mm", HINGE_Y, HINGE_Z]),
    ]


def tilt() -> list[dict]:
    """Tilt the whole laptop with the tray about the jig hinge axis (local X at lap_hinge_z), front edge down."""
    bodies = [BASE, KEYS, PAD, LID, SCREEN]
    return [
        c("solid.move", name="MBP14_ToHinge", bodies=bodies, translate=["0 mm", "0 mm", "-lap_hinge_z"]),
        c("solid.move", name="MBP14_Tilt", bodies=bodies, axis=[1, 0, 0], angle="lap_kb_tilt"),
        c("solid.move", name="MBP14_FromHinge", bodies=bodies, translate=["0 mm", "0 mm", "lap_hinge_z"]),
    ]


def finish() -> list[dict]:
    desc = ("Apple MacBook Pro 14in (M4, 2024), deck tilted lap_kb_tilt front-down with the tray, lid open to lap_lid so the screen matches the monitor tilt "
            "(purchased, reference model). Origin: footprint centre on the bottom plane of the feet (tray surface) before the "
            "tilt (tilt axis: local X at z = lap_hinge_z); +Y toward the hinge "
            "(wall side), screen faces -Y (user), X right, Z up. Finish Space Black.")
    return [
        c("material.assign", bodies=[BASE, LID, PAD], material=MATERIAL),
        c("material.assign", bodies=[KEYS], material="ABS"),
        c("material.assign", bodies=[SCREEN], material=MATERIAL_SCREEN),
        c("appearance.assign", bodies=[BASE, LID], color=COLOR_ALU, pbr=ALU_PBR),
        c("appearance.assign", bodies=[PAD], color=COLOR_ALU, pbr=GLASS_PBR),
        c("appearance.assign", bodies=[KEYS], color=COLOR_KEYS),
        c("appearance.assign", bodies=[SCREEN], color=COLOR_SCREEN, pbr=GLASS_PBR),
        c("document.metadata.set", values={
            "part_number": "LAP-02", "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {
                "Material": MATERIAL, "ReleaseState": "WIP",
                "Source": "Apple tech specs support.apple.com/en-us/121552 (W, D, H, display); "
                          "lid/base split, radii, keyboard, trackpad, feet MEASURE "
                          "(refs/macbook_pro_14/README.md)",
            },
        }),
    ]


def build() -> list[dict]:
    # default-parameter numbers, only used to pick edges
    d = {"w": 312.6, "d": 221.2, "foot_h": 0.9, "base_t": 9.6, "lid_d": 220.2}
    return [*TEMPLATE, SKEL, params_cmd(), *base(d), *keyboard(), *trackpad(), *lid(d), *tilt(), *finish()]


def main() -> None:
    OUT.write_text(json.dumps({"generated_by": "parts/src/LAP-02_gen.py", "commands": build()}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
