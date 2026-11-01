"""Generate parts/src/LAP-01_LaptopMount.json (user-built laptop mount arm on the right 2040 stile).

Placeholder envelope for the jig the user will build: a base plate T-nut-bolted to the right stile's front
slot (height freely adjustable), a riser dropping in front of the lower crossbar, an L arm toward the user
and sideways (lap_arm_dx), and a pivot puck under the tray centre (the tray is LAP-03 and turns on the puck
to face the Eye). Layout-driven: imports the skeleton (lap_reach, lap_arm_dx, lap_tray_z, lap_yoke_bot,
bar1_z, rail_l); jig sizes are local `lmnt_*` MEASURE parameters.

Local frame: origin = on the right stile's front face plane, stile centre in X, at the stile's bottom end
(= lower crossbar top face); world (stile_r_x, stile_front, lap_mount_z), no rotation. +Y toward the wall,
X right, Z up. The stile and crossbar sit at y >= 0 (crossbar z in [-rail_l, 0]); every face of the part
stays at y <= -0.1 mm. The puck top sits ~30 mm below the stile bottom, so the riser drops past the
crossbar front face. The desktop top is at z = -(bar1_z + rail_l/2).
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["build", "main"]

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
SKEL = {"command": "parameters.import", "params": {"path": f"{ROOT.as_posix()}/skeleton/params.json"}}
OUT = ROOT / "parts/src/LAP-01_LaptopMount.json"
BODY = "LaptopMount_Arm"
MATERIAL = "Al 6063-T5"  # MEASURE: the user's jig material isn't chosen yet
COLOR = "#2a2b2d"  # dark grey (jig placeholder)

# name, expression, comment
PARAMS: list[tuple[str, str, str]] = [
    ("lmnt_w", "40 mm", "MEASURE base plate and riser width (X), = stile width"),
    ("lmnt_t", "6 mm", "MEASURE base plate thickness (Y)"),
    ("lmnt_plate_bot", "5 mm", "MEASURE base plate bottom above the stile bottom end (local Z)"),
    ("lmnt_plate_h", "80 mm", "MEASURE base plate height (Z)"),
    ("lmnt_riser_d", "20 mm", "MEASURE riser depth (Y), in front of the base plate"),
    ("lmnt_arm_w", "30 mm", "MEASURE arm width"),
    ("lmnt_arm_t", "12 mm", "MEASURE arm thickness (Z)"),
    ("lmnt_puck_d", "50 mm", "MEASURE pivot puck size under the tray centre"),
    ("lmnt_puck_h", "8 mm", "MEASURE pivot puck height"),
    ("lmnt_tray_bot", "lap_tray_z + lap_yoke_bot - bar1_z - rail_l/2", "Puck top = LAP-03 hinge stem bottom (local Z)"),
    ("lmnt_arm_z", "lmnt_tray_bot - lmnt_puck_h - lmnt_arm_t", "Arm underside (local Z)"),
    ("lmnt_front", "0.1 mm + lmnt_t", "Base plate front face, in front of the stile front plane"),
    ("lmnt_plate_top", "lmnt_plate_bot + lmnt_plate_h", "Base plate top (local Z)"),
]


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def box(name: str, corner: list[str], length: str, width: str, height: str, new: bool = False) -> dict:
    extra = {"body_name": BODY, "operation": "new"} if new else {"operation": "join", "targets": [BODY]}
    return c("solid.box", name=name, corner=corner, length=length, width=width, height=height, **extra)


def base_plate() -> list[dict]:
    return [box("LMNT_BasePlate", ["-lmnt_w/2", "-lmnt_front", "lmnt_plate_bot"], "lmnt_w", "lmnt_t", "lmnt_plate_h",
                new=True)]


def arm() -> list[dict]:
    riser_y = "-lmnt_front - lmnt_riser_d"
    riser_z = "min(lmnt_arm_z + 0.1 mm, lmnt_plate_bot)"
    return [
        # overlaps the plate front 0.1 mm; runs from just inside the arm up to 0.1 mm under the plate top
        box("LMNT_Riser", ["-lmnt_w/2", riser_y, riser_z], "lmnt_w", "lmnt_riser_d + 0.1 mm",
            f"lmnt_plate_top - 0.1 mm - {riser_z}"),
        # Y leg: 0.1 mm into the riser front, out to the puck line (ends at the X leg centre line)
        box("LMNT_ArmY", ["-lmnt_arm_w/2", "-lap_reach", "lmnt_arm_z"], "lmnt_arm_w",
            f"lap_reach + {riser_y} + 0.1 mm", "lmnt_arm_t"),
        # X leg: along the puck line from the stile centre to the pivot X
        box("LMNT_ArmX", ["min(0 mm, lap_arm_dx) - lmnt_arm_w/2", "-lap_reach - lmnt_arm_w/2", "lmnt_arm_z"],
            "abs(lap_arm_dx) + lmnt_arm_w", "lmnt_arm_w", "lmnt_arm_t"),
        box("LMNT_Puck", ["lap_arm_dx - lmnt_puck_d/2", "-lap_reach - lmnt_puck_d/2", "lmnt_arm_z + lmnt_arm_t - 0.1 mm"],
            "lmnt_puck_d", "lmnt_puck_d", "lmnt_puck_h"),
    ]


def finish() -> list[dict]:
    desc = ("User-built laptop mount (placeholder envelope): base plate T-nut-bolted to the right 2040 stile's front "
            "slot, riser in front of the lower crossbar, L arm toward the user, pivot puck under the LAP-03 tray "
            "centre. Origin: stile front face plane, stile centre X, stile bottom end (crossbar top); +Y toward the "
            "wall, Z up")
    return [
        c("material.assign", bodies=[BODY], material=MATERIAL),
        c("appearance.assign", bodies=[BODY], color=COLOR),
        c("document.metadata.set", values={
            "part_number": "LAP-01", "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {"Material": MATERIAL, "ReleaseState": "WIP",
                                "Source": "Placeholder for the user's own jig; sizes MEASURE"},
        }),
    ]


def build() -> list[dict]:
    params = [c("parameters.add", name=n, expression=e, comment=k) for n, e, k in PARAMS]
    return [*TEMPLATE, SKEL, *params, *base_plate(), *arm(), *finish()]


def main() -> None:
    OUT.write_text(json.dumps({"generated_by": "parts/src/LAP-01_gen.py", "commands": build()}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
