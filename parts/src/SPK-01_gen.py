"""Generate parts/src/SPK-01_R40M_Speaker.json (Klipsch R-40M bookshelf speaker, multibody per finish).

Layout-driven: imports the skeleton for the outer box (spk_w, spk_d, spk_h), the swivel point (spk_mount_frac)
and the tilt (spk_tilt). Face details keep their sizes (MEASURE estimates from refs/klipsch_r40m photos) and
hang from datums of the box: front-face details from the baffle (y = -spk_d), the tweeter/horn from the top,
the woofer, port, posts and logo from the bottom. Expression-capable inputs (boxes, cylinders) use skeleton
expressions; plain-number inputs (sketch origins, the dust-cap sphere centre) are computed from the evaluated
skeleton (tools/skeleton_values.py) with the same offsets, so a change of spk_d or spk_h moves the whole face
(AGENTS §3).

Local frame: origin = swivel point = centre of the rear face at spk_mount_frac*spk_h above the bottom;
+Z up, -Y = front (baffle faces the listener), un-tilted, un-yawed.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import skeleton_values  # noqa: E402

__all__ = ["build", "main"]

TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
SKEL = {"command": "parameters.import", "params": {"path": f"{ROOT.as_posix()}/skeleton/params.json"}}
OUT = ROOT / "parts/src/SPK-01_R40M_Speaker.json"

# Datum expressions (mm); the numbers below are offsets from them (MEASURE estimates from photos).
FRONT = "-spk_d"
TOP = "spk_h*(1 - spk_mount_frac)"
BOT = "-spk_mount_frac*spk_h"

HORN_DROP, HORN_H = 136.0, 131.0  # horn pocket: top edge down to its bottom, and its height
GROOVE_DROP = 151.0  # top edge down to the baffle groove
WOOFER_UP = 78.0  # bottom edge up to the woofer centre
LOGO_UP = 153.375  # bottom edge up to the logo sketch origin
PORT_UP = 158.5  # bottom edge up to the rear port centre
POST_UP = 41.5  # bottom edge up to the binding posts
POST_X = 13.0
SCREW_X = 55.0
SCREW_TOP_DROP, SCREW_MID_DZ, SCREW_BOT_UP = 18.025, 1.225, 19.475  # rear-panel screws: rows from top / mid / bottom
HORN_MOUTH_HALF = (66.603, 63.29)
HORN_MID_HALF = (36.0, 34.0)
HORN_THROAT_R = 14.0

# y offsets behind the cabinet front (+ = into the cabinet)
Y_HORN_MOUTH, Y_HORN_MID, Y_HORN_THROAT = 0.9, 11.0, 33.0
Y_PLUG = 31.5
Y_BAFFLE = 1.0  # baffle front face (woofer recess sketch, logo)
Y_CONE, Y_CONE_CAVITY, Y_DUST_CAP, Y_DOME = 8.0, 7.0, 15.3, 63.4

BODIES = ["R40M_Cabinet", "R40M_Baffle", "R40M_Logo", "R40M_RearPanel", "R40M_PostRed", "R40M_PostBlack",
          "R40M_Screws", "R40M_Horn", "R40M_TweeterRing", "R40M_TweeterPlug", "R40M_Cone", "R40M_TrimRing",
          "R40M_Surround", "R40M_DustCap"]
# body, material, colour
FINISHES = [
    ("R40M_Cabinet", "MDF", "#1d1c1b"),
    ("R40M_Baffle", "ABS", "#141414"),
    ("R40M_Logo", "ABS", "#b07a52"),
    ("R40M_RearPanel", "ABS", "#141414"),
    ("R40M_PostRed", "ABS", "#a3161b"),
    ("R40M_PostBlack", "ABS", "#111111"),
    ("R40M_Screws", "Steel black-oxide", "#111111"),
    ("R40M_Horn", "ABS", "#0e0e0f"),
    ("R40M_TweeterRing", "ABS", "#0a0a0a"),
    ("R40M_TweeterPlug", "ABS", "#b07a52"),
    ("R40M_Cone", "ABS", "#c8783f"),
    ("R40M_TrimRing", "ABS", "#141414"),
    ("R40M_Surround", "ABS", "#0a0a0a"),
    ("R40M_DustCap", "ABS", "#c8783f"),
]
LOGO_SKETCH = ROOT / "refs/klipsch_r40m/R40M_logo_sketch.json"  # text outlines (Klipsch / REFERENCE)


@dataclass(frozen=True)
class Datums:
    """Evaluated datums (mm) for plain-number inputs, from the same expressions as FRONT / TOP / BOT."""

    front: float
    top: float
    bot: float

    @property
    def tweeter_z(self) -> float:
        return self.top - HORN_DROP + HORN_H / 2

    @property
    def woofer_z(self) -> float:
        return self.bot + WOOFER_UP

    @property
    def mid(self) -> float:
        return (self.top + self.bot) / 2


def datums(v: Mapping[str, float]) -> Datums:
    return Datums(front=-v["spk_d"], top=v["spk_h"] * (1 - v["spk_mount_frac"]), bot=-v["spk_mount_frac"] * v["spk_h"])


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def mm(x: float) -> str:
    return f"{x:g} mm"


def off(datum: str, x: float) -> str:
    """Expression: datum + x mm."""
    return f"{datum} {'+' if x >= 0 else '-'} {abs(x):g} mm"


def xz_plane(y: float, z: float, name: str, y_dir: int = 1) -> dict:
    return c("sketch.create", plane={"origin": [0, round(y, 6), round(z, 6)], "x_dir": [1, 0, 0], "y_dir": [0, 0, y_dir]},
             name=name)


def cabinet() -> list[dict]:
    horn_z = off(TOP, -HORN_DROP)
    return [
        c("solid.box", corner=["-spk_w/2", FRONT, BOT], length="spk_w", width="spk_d", height="spk_h",
          operation="new", name="R40M_Cabinet", body_name="R40M_Cabinet"),
        c("solid.box", corner=["-spk_w/2 + 5 mm", FRONT, off(BOT, 5)], length="spk_w - 10 mm", width="3 mm",
          height="spk_h - 10 mm", operation="cut", name="R40M_FrontPocket", targets=["R40M_Cabinet"]),
        c("solid.box", corner=["-spk_w/2 + 5 mm", off(FRONT, Y_BAFFLE), off(BOT, 5)], length="spk_w - 10 mm",
          width="2 mm", height="spk_h - 10 mm", operation="new", name="R40M_Baffle", body_name="R40M_Baffle"),
        c("solid.box", corner=["-spk_w/2 + 5 mm", FRONT, horn_z], length="spk_w - 10 mm", width="42 mm",
          height=mm(HORN_H), operation="cut", name="R40M_HornPocket", targets=["R40M_Cabinet", "R40M_Baffle"]),
        c("solid.box", corner=["-spk_w/2 + 5 mm", off(FRONT, Y_BAFFLE), horn_z], length="spk_w - 10 mm",
          width="40 mm", height=mm(HORN_H), operation="new", name="R40M_Horn", body_name="R40M_Horn"),
    ]


def tweeter(d: Datums) -> list[dict]:
    z = d.tweeter_z
    z_expr = off(TOP, -HORN_DROP + HORN_H / 2)
    (mx, my), (hx, hy) = HORN_MOUTH_HALF, HORN_MID_HALF
    return [
        xz_plane(d.front + Y_HORN_MOUTH, z, "Sk_R40M_HornMouth"),
        c("sketch.rectangle.two_point", p0=[-mx, -my], p1=[mx, my]),
        c("sketch.finish"),
        xz_plane(d.front + Y_HORN_MID, z, "Sk_R40M_HornMid"),
        c("sketch.rectangle.two_point", p0=[-hx, -hy], p1=[hx, hy]),
        c("sketch.finish"),
        xz_plane(d.front + Y_HORN_THROAT, z, "Sk_R40M_HornThroat"),
        c("sketch.circle.center", center=[0, 0], radius=HORN_THROAT_R),
        c("sketch.finish"),
        c("solid.loft", sections=[{"sketch": "Sk_R40M_HornMouth"}, {"sketch": "Sk_R40M_HornMid"},
                                  {"sketch": "Sk_R40M_HornThroat"}],
          operation="cut", targets=["R40M_Horn"], name="R40M_HornFlare"),
        c("solid.cylinder", base=["0 mm", off(FRONT, Y_HORN_THROAT), z_expr], axis=[0, -1, 0], radius="11 mm",
          height="1.5 mm", operation="new", name="R40M_TweeterRing", body_name="R40M_TweeterRing"),
        c("solid.cylinder", base=["0 mm", off(FRONT, Y_PLUG), z_expr], axis=[0, -1, 0], radius="6 mm",
          height="4 mm", operation="new", name="R40M_TweeterPlug", body_name="R40M_TweeterPlug"),
        c("solid.box", corner=["-spk_w/2 + 5 mm", off(FRONT, Y_BAFFLE), off(TOP, -GROOVE_DROP)],
          length="spk_w - 10 mm", width="0.6 mm", height="0.8 mm", operation="cut", name="R40M_Groove",
          targets=["R40M_Baffle"]),
    ]


def ring(name: str, y_off: float, z_expr: str, dia: float, h: float, op: str, target: str | None = None) -> dict:
    """Cylinder on the woofer axis facing the listener (axis -Y), based y_off behind the front."""
    extra: dict[str, object] = {"targets": [target]} if target else {"body_name": name}
    return c("solid.cylinder", base=["0 mm", off(FRONT, y_off), z_expr], axis=[0, -1, 0], radius=f"{dia:g} mm / 2",
             height=mm(h), operation=op, name=name, **extra)


def woofer(d: Datums) -> list[dict]:
    z = d.woofer_z
    z_expr = off(BOT, WOOFER_UP)
    cone = off(FRONT, Y_CONE)
    return [
        xz_plane(d.front + Y_BAFFLE, z, "Sk_R40M_WooferRecess"),
        c("sketch.circle.center", center=[0, 0], radius=60.5),
        c("sketch.finish"),
        c("solid.extrude", sketch="Sk_R40M_WooferRecess", distance="7 mm", direction="negative", taper="-56 deg",
          operation="cut", targets=["R40M_Baffle", "R40M_Cabinet"], name="R40M_WooferRecess"),
        c("solid.cylinder", base=["0 mm", cone, z_expr], axis=[0, 1, 0], radius="68 mm / 2", height="20 mm",
          operation="cut", name="R40M_ConeHole", targets=["R40M_Cabinet"]),
        c("solid.cylinder", base=["0 mm", cone, z_expr], axis=[0, 1, 0], radius="68 mm / 2", height="14 mm",
          operation="new", name="R40M_Cone", body_name="R40M_Cone"),
        xz_plane(d.front + Y_CONE_CAVITY, z, "Sk_R40M_ConeCavity"),
        c("sketch.circle.center", center=[0, 0], radius=35.61),
        c("sketch.finish"),
        c("solid.extrude", sketch="Sk_R40M_ConeCavity", distance="13 mm", direction="negative", taper="-57.7 deg",
          operation="cut", targets=["R40M_Cone"], name="R40M_ConeCavity"),
        ring("R40M_TrimRing", Y_CONE, z_expr, 92, 3, "new"),
        ring("R40M_TrimRingBore", Y_CONE, z_expr, 80, 3, "cut", "R40M_TrimRing"),
        ring("R40M_Surround", Y_CONE, z_expr, 80, 2, "new"),
        ring("R40M_SurroundBore", Y_CONE, z_expr, 68, 2, "cut", "R40M_Surround"),
        ring("R40M_DustCap", Y_DUST_CAP, z_expr, 45.2, 5.1, "new"),
        c("solid.sphere", center=[0, round(d.front + Y_DOME, 6), round(z, 6)], radius="53.1 mm",
          operation="intersect", targets=["R40M_DustCap"], name="R40M_DustCapDome"),
    ]


def post(name: str, x: float, z_expr: str) -> list[dict]:
    return [
        c("solid.cylinder", base=[mm(x), "-0.5 mm", z_expr], axis=[0, 1, 0], radius="11 mm / 2", height="12 mm",
          operation="new", name=name, body_name=name),
        c("solid.cylinder", base=[mm(x), "11.5 mm", z_expr], axis=[0, 1, 0], radius="4 mm / 2", height="1 mm",
          operation="cut", name=f"{name}Hole", targets=[name]),
    ]


def rear(d: Datums) -> list[dict]:
    post_z = off(BOT, POST_UP)
    # screw sketch: sketch y = -Z
    rows = (d.top - SCREW_TOP_DROP, d.mid + SCREW_MID_DZ, d.bot + SCREW_BOT_UP)
    screws = [c("sketch.circle.center", center=[sx * SCREW_X, round(-z, 6)], radius=3.0) for z in rows for sx in (-1, 1)]
    names = ["R40M_Screws"] + [f"R40M_Screws ({i})" for i in range(2, len(screws) + 1)]
    return [
        c("solid.box", corner=["-spk_w/2 + 4 mm", "-2 mm", off(BOT, 4)], length="spk_w - 8 mm", width="2 mm",
          height="spk_h - 8 mm", operation="cut", name="R40M_RearPocket", targets=["R40M_Cabinet"]),
        c("solid.box", corner=["-spk_w/2 + 4 mm", "-2 mm", off(BOT, 4)], length="spk_w - 8 mm", width="1.5 mm",
          height="spk_h - 8 mm", operation="new", name="R40M_RearPanel", body_name="R40M_RearPanel"),
        xz_plane(0.5, d.bot + PORT_UP, "Sk_R40M_PortFlare", y_dir=-1),
        c("sketch.circle.center", center=[0, 0], radius=37.0),
        c("sketch.finish"),
        c("solid.extrude", sketch="Sk_R40M_PortFlare", distance="9 mm", direction="negative", taper="-45 deg",
          operation="cut", targets=["R40M_RearPanel", "R40M_Cabinet"], name="R40M_PortFlare"),
        c("solid.cylinder", base=["0 mm", "-6 mm", off(BOT, PORT_UP)], axis=[0, -1, 0], radius="55.6 mm / 2",
          height="140 mm", operation="cut", name="R40M_PortTube", targets=["R40M_Cabinet"]),
        *post("R40M_PostRed", -POST_X, post_z)[:1],
        *post("R40M_PostBlack", POST_X, post_z)[:1],
        *post("R40M_PostRed", -POST_X, post_z)[1:],
        *post("R40M_PostBlack", POST_X, post_z)[1:],
        xz_plane(-0.5, 0, "Sk_R40M_Screws", y_dir=-1),
        *screws,
        c("sketch.finish"),
        c("solid.extrude", sketch="Sk_R40M_Screws", distance="0.5 mm", direction="positive", operation="new",
          name="R40M_Screws", body_name="R40M_Screws"),
        c("solid.combine", target="R40M_Screws", tools=names[1:], operation="join", keep_tools=False),
        c("timeline.rename", feature="Combine1", name="R40M_ScrewsJoin"),
    ]


def logo(d: Datums) -> list[dict]:
    """Bronze logo on the baffle: text outlines from LOGO_SKETCH, extruded 0.3 mm toward the listener."""
    sketch = json.loads(LOGO_SKETCH.read_text(encoding="utf-8"))
    letters = ["R40M_Logo"] + [f"R40M_Letter_{i}" for i in range(2, 18)]
    plane = {"origin": [0.0, round(d.front + Y_BAFFLE, 6), round(d.bot + LOGO_UP, 6)],
             "x_dir": [1.0, 0.0, 0.0], "y_dir": [-0.0, 0.0, 1.0]}
    return [
        c("timeline.add", feature={"name": "Sk_R40M_Logo", "plane": {"plane": plane, "type": "custom"},
                                   "sketch": sketch, "type": "sketch", "id": 9001}),
        c("timeline.add", feature={"body_names": letters, "extent": {"convention": "total_distance",
                                                                     "direction": "positive", "distance": "0.3 mm"},
                                   "name": "R40M_Letters", "operation": "new_body", "profiles": {"type": "all"},
                                   "type": "extrude", "sketch": 9001}),
        c("solid.combine", target="R40M_Logo", tools=letters[1:], operation="join", keep_tools=False),
        c("timeline.rename", feature="Combine1", name="R40M_LogoJoin"),
    ]


def finish() -> list[dict]:
    desc = ("Klipsch R-40M bookshelf speaker (purchased, reference model, multibody per finish). Origin: swivel point "
            "= centre of the rear face at spk_mount_frac*spk_h above the bottom; +Z up, -Y = front (baffle faces the "
            "listener), un-tilted, un-yawed. Outer box from spk_w/spk_d/spk_h; face details placed from the box "
            "(front face, top and bottom edges), sizes MEASURE estimates.")
    cmds: list[dict] = []
    for body, material, color in FINISHES:
        cmds += [c("material.assign", bodies=[body], material=material),
                 c("appearance.assign", bodies=[body], color=color)]
    return cmds + [
        c("solid.move", bodies=BODIES, axis=[1, 0, 0], angle="spk_tilt", name="Tilt_spk_tilt"),
        c("document.metadata.set", values={
            "part_number": "SPK-01", "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {
                "Material": "MDF cabinet, polymer/ABS drivers and trim", "ReleaseState": "WIP",
                "Source": "Klipsch spec 147.6x214.3x298.5 mm + photos refs/klipsch_r40m; legacy desk_rails.solidcraft "
                          "R40_* features",
            },
        }),
    ]


def build(v: Mapping[str, float] | None = None) -> list[dict]:
    d = datums(skeleton_values.values() if v is None else v)
    return [*TEMPLATE, SKEL, *cabinet(), *tweeter(d), *woofer(d), *rear(d), *logo(d), *finish()]


def main() -> None:
    OUT.write_text(json.dumps({"generated_by": "parts/src/SPK-01_gen.py", "commands": build()}, indent=1),
                   encoding="utf-8")


if __name__ == "__main__":
    main()
