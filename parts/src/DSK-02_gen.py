"""Generate parts/src/DSK-02_TopSupport.json (Apex Pro / Jiecang top support, bent steel angle).

Layout-driven: imports the skeleton (ts_*, sr_clear_d, leg_yc, ch_y_off). The end-taper chamfer picks its
edges by point, so the points are computed from the evaluated skeleton (tools/skeleton_values.py) and
follow ts_t / ts_len / ts_h when they change.

Local frame: origin = outer web face / flange top edge, mid-length; +X outward (away from the desk
centre), flange toward -X, +Y toward the wall, body below Z = 0.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/2015m/DEV/CAD/desk")
sys.path.insert(0, str(ROOT / "tools"))
import skeleton_values  # noqa: E402

__all__ = ["build", "main"]

TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
SKEL = {"command": "parameters.import", "params": {"path": f"{ROOT.as_posix()}/skeleton/params.json"}}
OUT = ROOT / "parts/src/DSK-02_TopSupport.json"
BODY = "TopSupport_JC"
MATERIAL = "Steel powder-coated"
COLOR = "#a8acaf"  # DeskHaus Silver


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def angle(v: dict[str, float]) -> list[dict]:
    # bottom edge of each web end, at mid-thickness
    ends = [[-v["ts_t"] / 2, sy * v["ts_len"] / 2, -v["ts_h"]] for sy in (1, -1)]
    return [
        c("solid.box", name="TS_Web", body_name=BODY, length="ts_t", width="ts_len", height="ts_h",
          corner=["-ts_t", "-ts_len/2", "-ts_h"]),
        c("solid.chamfer", name="TS_EndTaper", body=BODY, edges=ends, distance="ts_h - ts_t - ts_lip",
          distance2="ts_taper"),
        c("solid.box", name="TS_Flange", operation="join", targets=[BODY], length="ts_w - ts_t + 0.1 mm",
          width="ts_len", height="ts_t", corner=["-ts_w", "-ts_len/2", "-ts_t"]),
    ]


def holes() -> list[dict]:
    return [
        c("solid.cylinder", name="TS_Hole_LegScrew", axis="X", operation="cut", targets=[BODY],
          radius="sr_clear_d/2", height="ts_t + 0.2 mm",
          base=["-ts_t - 0.1 mm", "ch_y_off - leg_yc - ts_bolt_pitch/2", "-ts_bolt_z"]),
        c("solid.pattern.rectangular", name="TS_Hole_LegScrew_Pattern", features=["TS_Hole_LegScrew"],
          dir1=[0, 1, 0], count1=2, spacing1="ts_bolt_pitch"),
        c("solid.mirror", name="TS_Holes_Mirror", features=["TS_Hole_LegScrew", "TS_Hole_LegScrew_Pattern"],
          plane={"origin": ["0 mm", "ch_y_off", "0 mm"], "normal": [0, 1, 0]}),
    ]


def finish() -> list[dict]:
    desc = ("Apex Pro (Jiecang OEM) top support: bent steel angle, outer web + inward top flange, web ends tapered "
            "to a ts_lip lip, 4 x sr_clear_d M6 holes in the web (D9: leg screws, 2 per leg column). Origin: outer "
            "web face / flange top edge, mid-length; +X outward (away from desk centre), flange toward -X, +Y "
            "toward wall, body below Z=0. Serves L and R (L = yaw 180); hole pattern centred on ch_y_off, so this "
            "needs ch_y_off = 0.")
    return [
        c("material.assign", bodies=[BODY], material=MATERIAL),
        c("appearance.assign", bodies=[BODY], color=COLOR),
        c("document.metadata.set", values={
            "part_number": "DSK-02", "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {"Material": MATERIAL, "ReleaseState": "WIP",
                                "Source": "Measured 2026-10-29 (height, screw spacing and height); DeskHaus "
                                          "dimension sheet + photos (refs/apex_pro)"},
        }),
    ]


def build() -> list[dict]:
    return [*TEMPLATE, SKEL, *angle(skeleton_values.values()), *holes(), *finish()]


def main() -> None:
    OUT.write_text(json.dumps({"generated_by": "parts/src/DSK-02_gen.py", "commands": build()}, indent=1),
                   encoding="utf-8")


if __name__ == "__main__":
    main()
