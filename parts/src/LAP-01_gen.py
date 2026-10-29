"""Generate parts/src/LAP-01_LaptopMount.json (user-built laptop mount arm on the lower 2040 crossbar).

Placeholder envelope for the jig the user will build: a C-clamp on the lower crossbar, a short riser,
a straight arm toward the user and a pivot puck under the tray centre (the tray is LAP-03 and turns
on the puck to face the Eye). No pole. Layout-driven: imports the skeleton (lap_reach, lap_tray_z,
lap_tray_t, bar1_z, rail_l, rail_s); jig sizes are local `lmnt_*` MEASURE parameters.

Local frame: origin = on the crossbar top face, clamp centre in X, bar centre line in Y (world
(lap_x, stile_y, lap_clamp_z)). +Y toward the wall, X right, Z up. The bar occupies y in
[-rail_s/2, rail_s/2], z in [-rail_l, 0]; clamp faces sit 0.1 mm off it. Nothing extends behind
y = +rail_s/2.
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["build", "main"]

ROOT = Path("C:/Users/2015m/DEV/CAD/desk")
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
SKEL = {"command": "parameters.import", "params": {"path": f"{ROOT.as_posix()}/skeleton/params.json"}}
OUT = ROOT / "parts/src/LAP-01_LaptopMount.json"
BODY = "LaptopMount_Arm"
MATERIAL = "Al 6063-T5"  # MEASURE: the user's jig material isn't chosen yet
COLOR = "#2a2b2d"  # dark grey (jig placeholder)

# name, expression, comment
PARAMS: list[tuple[str, str, str]] = [
    ("lmnt_w", "40 mm", "MEASURE clamp and riser width (X)"),
    ("lmnt_t", "6 mm", "MEASURE clamp plate thickness"),
    ("lmnt_arm_w", "30 mm", "MEASURE arm width (X)"),
    ("lmnt_arm_t", "12 mm", "MEASURE arm thickness (Z)"),
    ("lmnt_puck_d", "50 mm", "MEASURE pivot puck size under the tray centre"),
    ("lmnt_puck_h", "8 mm", "MEASURE pivot puck height"),
    ("lmnt_tray_bot", "lap_tray_z + lap_yoke_bot - bar1_z - rail_l/2", "Puck top = LAP-03 hinge stem bottom, above the bar top (local Z)"),
    ("lmnt_arm_z", "lmnt_tray_bot - lmnt_puck_h - lmnt_arm_t", "Arm underside above the bar top (local Z)"),
    ("lmnt_front", "rail_s/2 + 0.1 mm + lmnt_t", "Clamp spine front face, in front of the bar centre line"),
]


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def box(name: str, corner: list[str], length: str, width: str, height: str, new: bool = False) -> dict:
    extra = {"body_name": BODY, "operation": "new"} if new else {"operation": "join", "targets": [BODY]}
    return c("solid.box", name=name, corner=corner, length=length, width=width, height=height, **extra)


def clamp() -> list[dict]:
    return [
        box("LMNT_TopPlate", ["-lmnt_w/2", "-lmnt_front", "0.1 mm"], "lmnt_w", "lmnt_front + rail_s/2", "lmnt_t", new=True),
        box("LMNT_Spine", ["-lmnt_w/2", "-lmnt_front", "-rail_l - 0.1 mm - lmnt_t"], "lmnt_w", "lmnt_t",
            "rail_l + 0.2 mm + 2*lmnt_t"),
        box("LMNT_Jaw", ["-lmnt_w/2", "-lmnt_front", "-rail_l - 0.1 mm - lmnt_t"], "lmnt_w",
            "lmnt_front + rail_s/2", "lmnt_t"),
    ]


def arm() -> list[dict]:
    return [
        # spans from the clamp top plate to the arm, whether the arm sits above or below the bar top
        box("LMNT_Riser", ["-lmnt_w/2", "-lmnt_front - lmnt_w + 0.1 mm", "min(0.1 mm, lmnt_arm_z)"], "lmnt_w", "lmnt_w",
            "max(lmnt_arm_z + lmnt_arm_t, lmnt_t + 0.1 mm) - min(0.1 mm, lmnt_arm_z)"),
        box("LMNT_Arm", ["-lmnt_arm_w/2", "-lap_reach - lmnt_puck_d/2", "lmnt_arm_z"], "lmnt_arm_w",
            "lap_reach + lmnt_puck_d/2 - lmnt_front - lmnt_w/2", "lmnt_arm_t"),
        box("LMNT_Puck", ["-lmnt_puck_d/2", "-lap_reach - lmnt_puck_d/2", "lmnt_arm_z + lmnt_arm_t - 0.1 mm"],
            "lmnt_puck_d", "lmnt_puck_d", "lmnt_puck_h"),
    ]


def finish() -> list[dict]:
    desc = ("User-built laptop mount (placeholder envelope): C-clamp on the lower 2040 crossbar, riser, straight "
            "arm toward the user, pivot puck under the LAP-03 tray centre. Origin: crossbar top face, clamp centre X, "
            "bar centre line Y; +Y toward the wall, Z up")
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
    return [*TEMPLATE, SKEL, *params, *clamp(), *arm(), *finish()]


def main() -> None:
    OUT.write_text(json.dumps({"generated_by": "parts/src/LAP-01_gen.py", "commands": build()}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
