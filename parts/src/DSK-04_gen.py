"""Generate parts/src/DSK-04_Leg.json (DeskHaus Apex Pro / Jiecang 3-stage lifting column).

Standard (non-inverted) column, as in the DeskHaus renders (refs/apex_pro/photos): the widest stage
stands on the foot and the stages get narrower toward the top. The smallest stage enters the
column-top housing, which sits between the 2 channel bars under the top-support flange.

Local frame: origin = top face centre (frame_top), +X toward the outer (top support) side,
+Y toward the wall, body below Z=0. The bottom stage ends on the foot top (frame_top - foot_h).

Usage: python parts/src/DSK-04_gen.py [skeleton_path] [out_json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

__all__ = ["build", "main"]

ROOT = Path("C:/Users/2015m/DEV/CAD/desk")
TEMPLATE = ROOT / "parts" / "_template.json"
DEFAULT_SKEL = "skeleton/params.json"
DEFAULT_OUT = ROOT / "parts" / "src" / "DSK-04_Leg.json"
SILVER = "#a8acaf"
STEEL = "Steel powder-coated"


def cmd(c: str, **p: object) -> dict:
    return {"command": c, "params": p}


def par(name: str, expr: str, comment: str) -> dict:
    return cmd("parameters.add", name=name, expression=expr, comment=comment)


def rrect(sk: str, offset: str, hx: str, hy: str, r: str) -> list[dict]:
    """Centred rounded rectangle (half sizes hx, hy) on XY at offset."""
    pts = [[f"-({hx})", f"-({hy})"], [f"{hx}", f"-({hy})"], [f"{hx}", f"{hy}"], [f"-({hx})", f"{hy}"]]
    return [
        cmd("sketch.create", plane="XY", offset=offset, name=sk),
        cmd("sketch.line", points=pts, closed=True),
        cmd("sketch.fillet", points=["l1.start", "l1.end", "l2.end", "l3.end"], radius=r),
        cmd("sketch.finish"),
    ]


# Shared with DSK-03 (channel-screw positions must match).
JC_SHARED = [
    par("jc_hsg_in", "40 mm", "MEASURE Apex Pro column-top housing: reach inward of the column outer face (X), assembly guide step 1"),
    par("jc_hsg_below", "6 mm", "MEASURE column-top housing: depth below the channel bars"),
    par("jc_scr_pitch", "50 mm", "MEASURE channel-to-column M6x10 screws: X pitch of the 2 per side (assembly guide step 1)"),
    par("jc_hsg_xc", "((leg_inset - ts_t) - (leg_x/2 + jc_hsg_in))/2", "Column-top housing X centre from leg centre (channel screws are centred on it)"),
]

LEG_PARAMS = [
    par("jc_top_min", "21.5 in", "Apex Pro frame-top height fully retracted (DeskHaus callout 21.5-47.5 in; spec sheet 22.5 in incl. 1 in top)"),
    par("jc_s0", "10 mm", "MEASURE visible length of each upper stage when fully retracted"),
    par("jc_step", "2.5 mm", "Stage-to-stage inset per side, measured 2026-10-29 (50.2x80.6 bottom / 45.2x75.4 / 40.3x70.3 top)"),
    par("jc_r", "4 mm", "MEASURE bottom-stage corner radius"),
    par("jc_ext", "max(frame_top - jc_top_min, 0 mm)", "Column extension above fully retracted"),
    par("jc_vis", "jc_s0 + jc_ext/2", "Visible length of the top and middle stages (extension split evenly)"),
    par("jc_hsg_d", "ch_h + jc_hsg_below", "Column-top housing depth below frame top"),
    par("jc_z_mid", "jc_hsg_d + jc_vis", "Top (smallest) stage bottom end = middle stage top, below frame top"),
    par("jc_z_bot", "jc_z_mid + jc_vis", "Middle stage bottom end = bottom (widest) stage top, below frame top"),
]


def housing() -> list[dict]:
    """Column-top housing between the channel bars, chamfered inner corners."""
    xo, xi = "leg_inset - ts_t", "-(leg_x/2 + jc_hsg_in)"
    return [
        cmd("sketch.create", plane="XY", name="Leg_Housing_Sketch"),
        cmd("sketch.line", closed=True, points=[
            [xo, "-leg_hsg_y/2"], [xo, "leg_hsg_y/2"], [f"{xi} + 12 mm", "leg_hsg_y/2"], [xi, "leg_hsg_y/2 - 12 mm"],
            [xi, "-(leg_hsg_y/2 - 12 mm)"], [f"{xi} + 12 mm", "-leg_hsg_y/2"]]),
        cmd("sketch.finish"),
        cmd("solid.extrude", name="Leg_Housing", body_name="Leg", distance="jc_hsg_d", direction="negative"),
    ]


def stages() -> list[dict]:
    """3 stages, narrowest at the top; each smaller stage overruns 0.1 mm into the next."""
    c = rrect("Leg_StageTop_Sketch", "-1 mm", "leg_x/2 - 2*jc_step", "leg_y/2 - 2*jc_step", "jc_r - 1 mm")
    c.append(cmd("solid.extrude", name="Leg_StageTop", operation="join", targets=["Leg"],
                 distance="jc_z_mid - 1 mm + 0.1 mm", direction="negative"))
    c += rrect("Leg_StageMid_Sketch", "-jc_z_mid", "leg_x/2 - jc_step", "leg_y/2 - jc_step", "jc_r - 0.5 mm")
    c.append(cmd("solid.extrude", name="Leg_StageMid", operation="join", targets=["Leg"],
                 distance="jc_vis + 0.1 mm", direction="negative"))
    c += rrect("Leg_StageBot_Sketch", "-jc_z_bot", "leg_x/2", "leg_y/2", "jc_r")
    c.append(cmd("solid.extrude", name="Leg_StageBot", operation="join", targets=["Leg"],
                 distance="frame_top - foot_h - jc_z_bot", direction="negative"))
    return c


def cuts() -> list[dict]:
    """Flange notch, 2 M6 taps for the top-support screws, 4 M6 taps for the channel screws."""
    return [
        cmd("solid.box", name="Leg_UnderFlangeCut", operation="cut", targets=["Leg"],
            length="(leg_inset - ts_t) - (leg_inset - ts_w) + 0.1 mm", width="leg_hsg_y + 0.2 mm", height="ts_t + 0.1 mm",
            corner=["leg_inset - ts_w", "-leg_hsg_y/2 - 0.1 mm", "-ts_t"]),
        cmd("solid.cylinder", name="Leg_Tap", axis="X", operation="cut", targets=["Leg"], radius="3 mm",
            height="(sb_len - sr_seat_t - ts_t) + 0.1 mm",
            base=["(leg_inset - ts_t) - (sb_len - sr_seat_t - ts_t)", "-ts_bolt_pitch/2", "-ts_bolt_z"]),
        cmd("solid.pattern.rectangular", name="Leg_Tap_Pattern", features=["Leg_Tap"], dir1=[0, 1, 0], count1=2,
            spacing1="ts_bolt_pitch"),
        cmd("solid.cylinder", name="Leg_ChTap", axis="Y", operation="cut", targets=["Leg"], radius="2.5 mm",
            height="leg_hsg_y + 0.2 mm", base=["jc_hsg_xc - jc_scr_pitch/2", "-leg_hsg_y/2 - 0.1 mm", "-ch_h/2"]),
        cmd("solid.pattern.rectangular", name="Leg_ChTap_Pattern", features=["Leg_ChTap"], dir1=[1, 0, 0], count1=2,
            spacing1="jc_scr_pitch"),
    ]


DESC = ("Apex Pro (Jiecang OEM) 3-stage lifting column, narrowest at the top (DeskHaus renders): column-top housing "
        "between the 2 channel bars (leg_y wide, outer face on the top-support web, chamfered inner end, notched ts_t "
        "under the flange), then stages leg_x x leg_y less 2*jc_step / jc_step / 0 per side from top to bottom; the "
        "extension above jc_top_min is split evenly between the top and middle stages; the bottom (widest) stage ends "
        "on the foot top (frame_top - foot_h below origin). 2 M6 taps (ts_bolt_pitch) in the outer face for the D9 "
        "leg screws, 4 M6 taps in the +-Y faces for the channel-bar screws. Origin: top face centre (frame_top); "
        "+X toward the outer (top support) side, +Y toward wall, body below Z=0.")
SOURCE = ("DeskHaus dimension sheet (end/front views, 2.76 in), callout card 21.5-47.5 in, product renders "
          "(stages taper toward the top), assembly guide steps 1-2, Jiecang 3-stage rectangular 80x50 mm; "
          "MEASURE: stage insets, housing size, screw pitch")


def finish() -> list[dict]:
    return [
        cmd("material.assign", bodies=["Leg"], material=STEEL),
        cmd("appearance.assign", bodies=["Leg"], color=SILVER),
        cmd("document.metadata.set", values={
            "part_number": "DSK-04", "description": DESC, "revision": "A", "project": "desk",
            "com.setsma.desk": {"Material": STEEL, "ReleaseState": "WIP", "Source": SOURCE},
        }),
    ]


def build(skel: str = DEFAULT_SKEL) -> dict:
    head = json.loads(TEMPLATE.read_text(encoding="utf-8"))["commands"]
    head = head + [cmd("parameters.import", path=skel)]
    return {"commands": head + JC_SHARED + LEG_PARAMS + housing() + stages() + cuts() + finish()}


def main(argv: list[str]) -> None:
    skel = argv[1] if len(argv) > 1 else DEFAULT_SKEL
    out = Path(argv[2]) if len(argv) > 2 else DEFAULT_OUT
    out.write_text(json.dumps({"generated_by": "parts/src/DSK-04_gen.py", **build(skel)}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
