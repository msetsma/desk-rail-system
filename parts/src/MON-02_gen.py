"""Generate parts/src/MON-02_Monitor_Side_27in.json (generic 27in 16:9 monitor, portrait, VESA mounted).

The side monitor isn't picked yet, so this is a generic 27in panel styled like MON-01 (thin slab, rear
housing, VESA boss, screen face inset in a bezel). Outline and depth come from the skeleton `m3_*`
MEASURE parameters; the active area is the standard 27in 16:9 size (local `m27_*` parameters).
Portrait: the thin bezels are on the top, bottom and inner (+X) edge, the wider landscape chin on
the outer (-X) edge.

Local frame (kept from Rev A): origin = VESA mounting face centre (rear of the VESA boss), screen faces
-Y, X right, Z up (unyawed).
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["build", "main"]

ROOT = Path("C:/Users/2015m/DEV/CAD/desk")
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
SKEL = {"command": "parameters.import", "params": {"path": f"{ROOT.as_posix()}/skeleton/params.json"}}
OUT = ROOT / "parts/src/MON-02_Monitor_Side_27in.json"
BODY = "Monitor_Side"
MATERIAL = "ABS"
COLOR_HOUSING = "#15171a"  # matte black plastic (same as MON-01)
COLOR_SCREEN = "#050608"  # panel face, off

# name, expression, comment
PARAMS: list[tuple[str, str, str]] = [
    ("m27_aa_long", "596.736 mm", "27in 16:9 active area, long side (portrait: Z)"),
    ("m27_aa_short", "335.664 mm", "27in 16:9 active area, short side (portrait: X)"),
    ("m27_bez", "(m3_h - m27_aa_long)/2", "Thin bezel, top / bottom / inner edge (portrait)"),
    ("m27_boss", "120 mm", "MEASURE VESA boss square (generic)"),
    ("m27_boss_d", "8 mm", "MEASURE VESA boss depth behind the rear housing"),
    ("m27_vesa", "100 mm", "VESA hole pattern"),
]

# default-parameter numbers, only used to pick faces
M3_W, M3_H, M3_T, AA_LONG, AA_SHORT = 363.0, 612.0, 45.0, 596.736, 335.664
X_SCREEN_R = "m3_w/2 - m27_bez"
X_SCREEN_L = "m3_w/2 - m27_bez - m27_aa_short"


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def xz_plane(y: float, name: str) -> dict:
    """Sketch plane parallel to XZ at y; sketch x = X, sketch y = Z, normal = -Y."""
    return c("sketch.create", plane={"origin": [0, y, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name=name)


def params_cmds() -> list[dict]:
    return [c("parameters.add", name=n, expression=e, comment=k) for n, e, k in PARAMS]


def shell() -> list[dict]:
    hsg_d = "m3_t - mon_panel_t - m27_boss_d"
    return [
        c("solid.box", name="M27_Panel", body_name=BODY, operation="new",
          corner=["-m3_w/2", "-m3_t", "-m3_h/2"], length="m3_w", width="mon_panel_t", height="m3_h"),
        c("solid.box", name="M27_RearHousing", operation="join", targets=[BODY],
          corner=["-m3_w*mon_back_frac/2", "-m3_t + mon_panel_t - 0.1 mm", "-m3_h*mon_back_frac/2"],
          length="m3_w*mon_back_frac", width=f"{hsg_d} + 0.1 mm", height="m3_h*mon_back_frac"),
        c("solid.box", name="M27_VesaBoss", operation="join", targets=[BODY],
          corner=["-m27_boss/2", "-m27_boss_d - 0.1 mm", "-m27_boss/2"],
          length="m27_boss", width="m27_boss_d + 0.1 mm", height="m27_boss"),
    ]


def vesa_holes() -> list[dict]:
    pts = [[sx, sz] for sx in ("-m27_vesa/2", "m27_vesa/2") for sz in ("-m27_vesa/2", "m27_vesa/2")]
    return [
        xz_plane(0.1, "Sk_M27_VesaHoles"),
        *[c("sketch.circle.center", center=p, radius=2.0) for p in pts],
        c("sketch.finish"),
        c("solid.extrude", sketch="Sk_M27_VesaHoles", distance="m27_boss_d + 0.1 mm", operation="cut",
          targets=[BODY], name="M27_VesaHoles_M4"),
    ]


def screen() -> list[dict]:
    zb, zt = "-m27_aa_long/2", "m27_aa_long/2"
    return [
        xz_plane(-M3_T - 0.1, "Sk_M27_Screen"),
        c("sketch.line", closed=True, points=[[X_SCREEN_L, zb], [X_SCREEN_R, zb], [X_SCREEN_R, zt], [X_SCREEN_L, zt]]),
        c("sketch.finish"),
        c("solid.extrude", sketch="Sk_M27_Screen", distance="0.4 mm", direction="negative",
          operation="cut", targets=[BODY], name="M27_ScreenFace"),
    ]


def finish() -> list[dict]:
    bez = (M3_H - AA_LONG) / 2
    screen_x = M3_W / 2 - bez - AA_SHORT / 2
    desc = ("Side monitor, generic 27in 16:9 in portrait, VESA 100x100 mounted (model not picked yet). "
            "Thin bezel top/bottom/inner edge, landscape chin on the outer (-X) edge. Origin: VESA mounting "
            "face centre (rear of the VESA boss); screen faces -Y, X right, Z up (unyawed)")
    return [
        c("material.assign", bodies=[BODY], material=MATERIAL),
        c("appearance.assign", bodies=[BODY], color=COLOR_HOUSING),
        c("appearance.assign", faces=[[screen_x, -M3_T + 0.3, 0.0]], body=BODY, color=COLOR_SCREEN,
          pbr={"metallic": 0.0, "roughness": 0.08, "dielectric_ior": 1.5}),
        c("document.metadata.set", values={
            "part_number": "MON-02", "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {
                "Material": MATERIAL, "ReleaseState": "WIP",
                "Source": "Generic 27in 16:9 active area; outline and depth from skeleton m3_* MEASURE params",
            },
        }),
    ]


def build() -> list[dict]:
    return [*TEMPLATE, SKEL, *params_cmds(), *shell(), *vesa_holes(), *screen(), *finish()]


def main() -> None:
    OUT.write_text(json.dumps({"commands": build()}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
