"""Generate parts/src/MON-01_Monitor_Main_32in.json (Gigabyte M32U, stand removed, VESA mounted).

Purchased fixed-shape model: no skeleton import. Vendor dimensions are local `m32u_*` parameters.
Sources and estimates: refs/gigabyte_m32u/README.md.

Local frame: origin = VESA mounting face centre (rear face of the VESA boss), screen faces -Y,
X right, Z up. The VESA centre sits m32u_vesa_dz above the overall outline centre.
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["build", "main"]

ROOT = Path("C:/Users/2015m/DEV/CAD/desk")
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
OUT = ROOT / "parts/src/MON-01_Monitor_Main_32in.json"
BODY = "Monitor_Main"
MATERIAL = "ABS"
COLOR_HOUSING = "#15171a"  # matte black plastic (legacy colour)
COLOR_SCREEN = "#050608"  # panel face, off

# name, expression, comment (MEASURE = estimate, see refs/gigabyte_m32u/README.md)
PARAMS: list[tuple[str, str, str]] = [
    ("m32u_w", "715.8 mm", "Width without stand (Gigabyte spec page)"),
    ("m32u_h", "423.8 mm", "Height without stand (Gigabyte spec page)"),
    ("m32u_d", "68.2 mm", "Depth without stand, screen front to VESA boss face (Gigabyte spec page)"),
    ("m32u_aa_w", "697.3056 mm", "Active area width (manual p.39)"),
    ("m32u_aa_h", "392.2344 mm", "Active area height (manual p.39)"),
    ("m32u_bez_side", "(m32u_w - m32u_aa_w)/2", "Side bezel to active area (9.25)"),
    ("m32u_bez_top", "m32u_bez_side", "Top bezel = side (dual-stage, reviews 8-9 mm)"),
    ("m32u_vesa_dz", "6.7 mm", "VESA centre above outline centre (scaled manual p.16 drawing, +-0.5)"),
    ("m32u_slab_t", "18 mm", "MEASURE panel thickness at the edge (photo; review says ~17 thinnest)"),
    ("m32u_back_d", "54 mm", "MEASURE screen front to rear housing back (side photo)"),
    ("m32u_hsg_drop", "106.4 mm", "Top edge down to rear housing top (manual p.16 drawing)"),
    ("m32u_hsg_r", "30 mm", "MEASURE rounded top of rear housing (side photo)"),
    ("m32u_boss", "131 mm", "VESA boss square (manual p.16 drawing)"),
    ("m32u_port_z", "77.3 mm", "Port line (downward-facing I/O) above bottom edge (manual p.16)"),
    ("m32u_pkt_wt", "387 mm", "I/O pocket width at the port line (manual p.16)"),
    ("m32u_pkt_wb", "452 mm", "I/O pocket width at the bottom edge (manual p.16)"),
    ("m32u_pkt_floor", "30 mm", "MEASURE screen front to I/O pocket floor"),
    ("m32u_vesa", "100 mm", "VESA hole pattern (manual p.16)"),
]

Z_TOP = "m32u_h/2 - m32u_vesa_dz"
Z_BOT = "-m32u_h/2 - m32u_vesa_dz"
Y_FRONT = "-m32u_d"
Y_BACK = "-m32u_d + m32u_back_d"


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def xz_plane(y: str | float, name: str) -> dict:
    """Sketch plane parallel to XZ at world y; sketch x = X, sketch y = Z, normal = -Y."""
    return c("sketch.create", plane={"origin": [0, y, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name=name)


def params_cmd() -> dict:
    rows = [{"name": n, "expression": e, "comment": k} for n, e, k in PARAMS]
    return c("parameters.import", text=json.dumps(rows))


def shell() -> list[dict]:
    return [
        c("solid.box", name="M32U_Panel", body_name=BODY, operation="new",
          corner=["-m32u_w/2", Y_FRONT, Z_BOT], length="m32u_w", width="m32u_slab_t", height="m32u_h"),
        c("solid.box", name="M32U_RearHousing", operation="join", targets=[BODY],
          corner=["-m32u_w/2 + 1 mm", "-m32u_d + m32u_slab_t - 0.1 mm", f"{Z_BOT} + 1 mm"],
          length="m32u_w - 2 mm", width="m32u_back_d - m32u_slab_t + 0.1 mm",
          height="m32u_h - m32u_hsg_drop - 1 mm"),
        c("solid.box", name="M32U_VesaBoss", operation="join", targets=[BODY],
          corner=["-m32u_boss/2", f"{Y_BACK} - 0.1 mm", "-m32u_boss/2"],
          length="m32u_boss", width="m32u_d - m32u_back_d + 0.1 mm", height="m32u_boss"),
    ]


def housing_round(back_y: float, top_z: float) -> list[dict]:
    """One fillet on the top-back edge of the rear housing (point given in default-param mm)."""
    return [c("solid.fillet", edges=[[200.0, back_y, top_z]], radius="m32u_hsg_r", name="M32U_HousingRound")]


def io_pocket(back_y: float) -> list[dict]:
    zt, zb = f"{Z_BOT} + m32u_port_z", f"{Z_BOT} - 0.1 mm"
    pts = [["-m32u_pkt_wt/2", zt], ["m32u_pkt_wt/2", zt], ["m32u_pkt_wb/2 + 0.05 mm", zb], ["-m32u_pkt_wb/2 - 0.05 mm", zb]]
    return [
        xz_plane(back_y + 0.1, "Sk_M32U_IOPocket"),
        c("sketch.line", points=pts, closed=True),
        c("sketch.finish"),
        c("solid.extrude", sketch="Sk_M32U_IOPocket", distance="m32u_back_d - m32u_pkt_floor + 0.1 mm",
          operation="cut", targets=[BODY], name="M32U_IOPocket"),
    ]


def vesa_holes() -> list[dict]:
    pts = [[sx, sz] for sx in ("-m32u_vesa/2", "m32u_vesa/2") for sz in ("-m32u_vesa/2", "m32u_vesa/2")]
    circles = [c("sketch.circle.center", center=p, radius=2.0) for p in pts]
    return [
        xz_plane(0.1, "Sk_M32U_VesaHoles"),
        *circles,
        c("sketch.finish"),
        c("solid.extrude", sketch="Sk_M32U_VesaHoles", distance="10.1 mm", operation="cut",
          targets=[BODY], name="M32U_VesaHoles_M4"),
    ]


def screen(front_y: float) -> list[dict]:
    zb = f"{Z_BOT} + m32u_h - m32u_bez_top - m32u_aa_h"
    zt = f"{Z_TOP} - m32u_bez_top"
    return [
        xz_plane(front_y - 0.1, "Sk_M32U_Screen"),
        c("sketch.line", closed=True, points=[["-m32u_aa_w/2", zb], ["m32u_aa_w/2", zb],
                                              ["m32u_aa_w/2", zt], ["-m32u_aa_w/2", zt]]),
        c("sketch.finish"),
        c("solid.extrude", sketch="Sk_M32U_Screen", distance="0.4 mm", direction="negative",
          operation="cut", targets=[BODY], name="M32U_ScreenFace"),
    ]


def finish(front_y: float, screen_z: float) -> list[dict]:
    desc = ("Gigabyte M32U 31.5in 4K monitor, stand removed, VESA 100x100 mounted (purchased, reference model). "
            "Origin: VESA mounting face centre (rear of VESA boss); screen faces -Y, X right, Z up. "
            "VESA centre is m32u_vesa_dz = 6.7 mm above the outline centre (= active-area centre).")
    return [
        c("material.assign", bodies=[BODY], material=MATERIAL),
        c("appearance.assign", bodies=[BODY], color=COLOR_HOUSING),
        c("appearance.assign", faces=[[0.0, front_y + 0.3, screen_z]], body=BODY, color=COLOR_SCREEN,
          pbr={"metallic": 0.0, "roughness": 0.08, "dielectric_ior": 1.5}),
        c("document.metadata.set", values={
            "part_number": "MON-01", "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {
                "Material": MATERIAL, "ReleaseState": "WIP",
                "Source": "Gigabyte M32U spec page + user manual (refs/gigabyte_m32u/README.md); "
                          "slab/housing depth MEASURE from photos",
            },
        }),
    ]


def build() -> list[dict]:
    # default-parameter numbers, only used to pick edges/faces
    d, h, dz, back_d, drop = 68.2, 423.8, 6.7, 54.0, 106.4
    front_y, back_y = -d, -d + back_d
    z_top = h / 2 - dz
    bez = (715.8 - 697.3056) / 2
    screen_z = z_top - bez - 392.2344 / 2
    return [
        *TEMPLATE,
        params_cmd(),
        *shell(),
        *housing_round(back_y, z_top - drop),
        *io_pocket(back_y),
        *vesa_holes(),
        *screen(front_y),
        *finish(front_y, screen_z),
    ]


def main() -> None:
    OUT.write_text(json.dumps({"generated_by": "parts/src/MON-01_gen.py", "commands": build()}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
