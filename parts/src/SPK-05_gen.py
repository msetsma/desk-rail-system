"""Generate parts/src/SPK-05_SpkWedge.json (low-profile speaker tilt wedge, product TBD).

Purchased part, envelope model: a solid wedge, thin at the rear, rising toward the front so a speaker laid
on it tilts up toward the ear. The 62x32 layout needs it this low: a 75 mm Aperta300 or a 2 in Auralex
MoPAD-XL puts the speaker top above the side screen's bottom edge, and then no depth clears both the screen
and the mouse pad (tools/spk_laid.py scan, 2026-10-31). Size and angle are MEASURE until a product is
picked (foam or rubber desktop wedges, ~8 deg, ~12 mm at the thin end).

Used by the 62x32 layout variant (speakers laid on their side, tools/build_variant.py), which reads STAND
below so the speaker sits on this top face. Not layout-driven: local `st_*` parameters only.

Local frame: origin = rear bottom edge centre (on the desktop); -Y = front (toward the listener), X along
the long side, Z up.
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["STAND", "build", "main"]

ROOT = Path("C:/Users/2015m/DEV/CAD/desk")
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
OUT = ROOT / "parts/src/SPK-05_SpkWedge.json"
BODY = "SpkWedge"
TOOL = "SpkWedge_TopCut"
MATERIAL = "ABS"  # MEASURE: stands in for foam / rubber until a product is picked
COLOR = "#2b2b2b"  # charcoal (typical foam wedge)

# Single source for the wedge size and tilt: the variant build reads it to seat the speaker.
STAND: dict[str, float] = {"w": 300.0, "d": 220.0, "h": 12.0, "tilt_deg": 8.0}

PARAMS: list[tuple[str, str, str]] = [
    ("st_w", f"{STAND['w']} mm", "MEASURE wedge length (X), ~ the laid R-40M's 298.5 mm"),
    ("st_d", f"{STAND['d']} mm", "MEASURE wedge depth (Y), ~ the R-40M's 214.3 mm"),
    ("st_h", f"{STAND['h']} mm", "MEASURE wedge thickness at the rear (thin end)"),
    ("st_tilt", f"{STAND['tilt_deg']} deg", "MEASURE wedge angle, front up"),
]


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def wedge() -> list[dict]:
    """Block to the front height, minus a cutter turned front-up about X and lifted to the rear height."""
    return [
        c("solid.box", name="SW_Block", body_name=BODY, corner=["-st_w/2", "-st_d", "0 mm"], length="st_w",
          width="st_d", height="st_h + st_d*tan(st_tilt) + 1 mm", operation="new"),
        c("solid.box", name="SW_Cutter", body_name=TOOL, corner=["-st_w/2 - 1 mm", "-st_d - 50 mm", "0 mm"],
          length="st_w + 2 mm", width="st_d + 100 mm", height="100 mm", operation="new"),
        c("solid.move", name="SW_CutterTilt", bodies=[TOOL], axis=[1, 0, 0], angle="-st_tilt"),
        c("solid.move", name="SW_CutterLift", bodies=[TOOL], translate=["0 mm", "0 mm", "st_h"]),
        c("solid.combine", name="SW_TopFace", target=BODY, tools=[TOOL], operation="cut", keep_tools=False),
    ]


def finish() -> list[dict]:
    desc = (f"Low-profile speaker tilt wedge (purchased, product TBD, envelope), {STAND['tilt_deg']} deg up. "
            "Origin: rear bottom edge centre on the desktop; -Y front, X long side, Z up")
    return [
        c("material.assign", bodies=[BODY], material=MATERIAL),
        c("appearance.assign", bodies=[BODY], color=COLOR),
        c("document.metadata.set", values={
            "part_number": "SPK-05", "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {"Material": MATERIAL, "ReleaseState": "WIP",
                                "Source": "Envelope; size and angle MEASURE until a product is picked"},
        }),
    ]


def build() -> list[dict]:
    params = [c("parameters.add", name=n, expression=e, comment=k) for n, e, k in PARAMS]
    return [*TEMPLATE, *params, *wedge(), *finish()]


def main() -> None:
    OUT.write_text(json.dumps({"generated_by": "parts/src/SPK-05_gen.py", "commands": build()}, indent=1),
                   encoding="utf-8")


if __name__ == "__main__":
    main()
