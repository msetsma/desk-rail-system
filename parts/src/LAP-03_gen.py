"""Generate parts/src/LAP-03_LaptopTray.json (user-built laptop tray, sized to the MacBook Pro 14in).

The tray shares the laptop's local frame, so the laptop sits aligned on it by construction: its front
edge rests 0.1 mm off the front lip, and the tray margin wraps the sides and back. The plate tilts
front-down by lap_kb_tilt on a hinge barrel (axis local X at lap_hinge_z), and a stem carries the
hinge down to the LAP-01 pivot puck; tray and laptop are both placed at (lap_x, lap_y, desk_h +
lap_tray_z), yaw -lap_yaw. Layout-driven: imports the skeleton (mbp_w, mbp_d, lap_tray_t,
lap_tray_m, lap_lip_h, lap_kb_tilt, lap_hinge_r, lap_hinge_z, lap_yoke_bot).

Local frame: origin = tray top surface at the laptop footprint centre, before the tilt. +Y toward the laptop hinge,
the laptop screen faces -Y, X right, Z up.
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["build", "main"]

ROOT = Path("C:/Users/2015m/DEV/CAD/desk")
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
SKEL = {"command": "parameters.import", "params": {"path": f"{ROOT.as_posix()}/skeleton/params.json"}}
OUT = ROOT / "parts/src/LAP-03_LaptopTray.json"
BODY = "LaptopTray"
MATERIAL = "Al 6063-T5"  # MEASURE: the user's jig material isn't chosen yet
COLOR = "#2a2b2d"  # dark grey (jig placeholder, matches LAP-01)
LIP_T = "4 mm"  # front lip thickness
HINGE_L = "60 mm"  # MEASURE tilt hinge barrel length (X)


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def tray() -> list[dict]:
    front = f"-mbp_d/2 - 0.1 mm - {LIP_T}"
    return [
        c("solid.box", name="LTRAY_Plate", body_name=BODY, operation="new",
          corner=["-mbp_w/2 - lap_tray_m", front, "-lap_tray_t"], length="mbp_w + 2*lap_tray_m",
          width=f"mbp_d + 0.1 mm + {LIP_T} + lap_tray_m", height="lap_tray_t"),
        c("solid.box", name="LTRAY_Lip", operation="join", targets=[BODY],
          corner=["-mbp_w/2 - lap_tray_m", front, "-0.1 mm"], length="mbp_w + 2*lap_tray_m",
          width=LIP_T, height="lap_lip_h + 0.1 mm"),
    ]


def hinge() -> list[dict]:
    """Tilt the plate front-down about the hinge axis, then add the hinge barrel (on the axis, so the tilt
    doesn't move it) and the stem down to the LAP-01 pivot puck top (lap_yoke_bot)."""
    return [
        c("solid.move", name="LTRAY_ToHinge", bodies=[BODY], translate=["0 mm", "0 mm", "-lap_hinge_z"]),
        c("solid.move", name="LTRAY_Tilt", bodies=[BODY], axis=[1, 0, 0], angle="lap_kb_tilt"),
        c("solid.move", name="LTRAY_FromHinge", bodies=[BODY], translate=["0 mm", "0 mm", "lap_hinge_z"]),
        c("solid.cylinder", name="LTRAY_HingeBarrel", axis="X", operation="join", targets=[BODY],
          radius="lap_hinge_r", height=HINGE_L, base=[f"-{HINGE_L}/2", "0 mm", "lap_hinge_z"]),
        c("solid.box", name="LTRAY_HingeStem", operation="join", targets=[BODY],
          corner=[f"-{HINGE_L}/2", "-lap_hinge_r", "lap_yoke_bot"], length=HINGE_L, width="2*lap_hinge_r",
          height="lap_hinge_z - lap_yoke_bot"),
    ]


def finish() -> list[dict]:
    desc = ("User-built laptop tray (placeholder) sized to the MacBook Pro 14in footprint, front lip the laptop "
            "rests against, tilted lap_kb_tilt front-down on a hinge barrel + stem to the LAP-01 puck. Origin: tray top at "
            "the laptop footprint centre before the tilt (tilt axis: local X at z = lap_hinge_z); +Y toward the hinge, screen faces -Y, Z up")
    return [
        c("material.assign", bodies=[BODY], material=MATERIAL),
        c("appearance.assign", bodies=[BODY], color=COLOR),
        c("document.metadata.set", values={
            "part_number": "LAP-03", "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {"Material": MATERIAL, "ReleaseState": "WIP",
                                "Source": "Placeholder for the user's own jig; sized from Apple MacBook Pro 14 specs"},
        }),
    ]


def build() -> list[dict]:
    return [*TEMPLATE, SKEL, *tray(), *hinge(), *finish()]


def main() -> None:
    OUT.write_text(json.dumps({"commands": build()}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
