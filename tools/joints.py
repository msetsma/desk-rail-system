"""Joint hardware for the rail system: gusset brackets and flat joining plates.

Rule IDs refer to docs/EXTRUSION_GUIDE.md. All geometry is parametric (sketch points and moves
are expressions), so joints follow the frame when parameters change. Brackets are envelopes of
Misumi-style cast gusset brackets (HBLFSD5 2-slot / HBLFSN5 1-slot class), not vendor meshes.
End anchors / end-tap screws are internal and not modelled (see the guide's decision log).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

__all__ = ["JOINT_PARAMS", "joint_commands"]

Cmd = dict[str, object]
Vec = tuple[int, int, int]

JOINT_PARAMS: Sequence[tuple[str, str, str]] = (
    ("brk_t", "5 mm", "Gusset bracket wall thickness"),
    ("brk_a", "40 mm", "Gusset bracket leg length, 2-slot (HBLFSD5 class)"),
    ("brk_a_small", "20 mm", "Gusset bracket leg length, 1-slot (HBLFSN5 class), stile joints"),
    ("plate_t", "4 mm", "Flat joining plate thickness"),
    ("plate_arm", "80 mm", "Joining plate arm along the horizontal member (J4: bolt spread)"),
    ("plate_ext", "60 mm", "Joining plate extension along the upright past the joint"),
    ("up_below", "rail_l + plate_ext",
     "Upright length below desktop underside: to the side-rail T-plate bottom (the panel hangs past it)"),
    ("so_d", "10 mm", "Panel standoff diameter (M5 threaded standoff into a T-nut)"),
    ("so_bar_x", "up_xc/2", "Panel standoffs on each crossbar: at x = 0 and +/- this"),
)


@dataclass(frozen=True)
class Bracket:
    """Gusset bracket: legs run along ``u`` and ``v`` from the inside corner ``at``; ``width``
    is centred on ``at`` along u x v."""

    name: str
    u: Vec
    v: Vec
    at: Sequence[str]
    leg: str
    width: str


def _sketch(name: str, x_dir: Vec, y_dir: Vec, points: Sequence[Sequence[str]]) -> list[Cmd]:
    return [
        {"command": "sketch.create",
         "params": {"plane": {"origin": [0, 0, 0], "x_dir": list(x_dir), "y_dir": list(y_dir)}, "name": name}},
        {"command": "sketch.line", "params": {"points": [list(p) for p in points], "closed": True}},
        {"command": "sketch.finish", "params": {}},
    ]


def _bracket(b: Bracket) -> list[Cmd]:
    a, t = b.leg, "brk_t"
    poly = [("0 mm", "0 mm"), (a, "0 mm"), (a, t), (t, a), ("0 mm", a)]
    return _sketch(f"Sk_{b.name}", b.u, b.v, poly) + [
        {"command": "solid.extrude", "params": {"sketch": f"Sk_{b.name}", "distance": b.width,
                                                "direction": "symmetric", "operation": "new",
                                                "name": b.name, "body_name": b.name}},
        {"command": "solid.move", "params": {"bodies": [b.name], "translate": list(b.at),
                                             "name": f"Place_{b.name}"}},
    ]


def _plate(name: str, x_dir: Vec, y_dir: Vec, poly: Sequence[Sequence[str]],
           direction: str, translate: Sequence[str]) -> list[Cmd]:
    return _sketch(f"Sk_{name}", x_dir, y_dir, poly) + [
        {"command": "solid.extrude", "params": {"sketch": f"Sk_{name}", "distance": "plate_t",
                                                "direction": direction, "operation": "new",
                                                "name": name, "body_name": name}},
        {"command": "solid.move", "params": {"bodies": [name], "translate": list(translate),
                                             "name": f"Place_{name}"}},
    ]


def _tee_joints(tag: str, zt: str) -> tuple[list[Cmd], list[str]]:
    """2040 arm (along Y, 40 side vertical, top at ``zt``) butting the upright front face with
    outer faces flush: T-plate on the outer face + 2-slot gusset under the arm (J1-J4).
    Used by the side rails (D2)."""
    cmds: list[Cmd] = []
    names: list[str] = []
    yf, yb = "(up_y - rail_l/2)", "(up_y + rail_l/2)"
    zr = f"({zt} - rail_l)"
    # T-plate on the flush outer faces, drawn in world (Y, Z); normal +X.
    tee = [(f"{yf} - plate_arm", zr), (yf, zr), (yf, f"{zr} - plate_ext"), (yb, f"{zr} - plate_ext"),
           (yb, f"{zt} + plate_ext"), (yf, f"{zt} + plate_ext"), (yf, zt), (f"{yf} - plate_arm", zt)]
    for side, sign in (("R", ""), ("L", "-")):
        outer = f"{sign}(up_xc + rail_l/2)"
        shift = outer if side == "R" else f"{outer} - plate_t"
        plate = f"Plate_{tag}_{side}"
        cmds += _plate(plate, (0, 1, 0), (0, 0, 1), tee, "positive", [shift, "0 mm", "0 mm"])
        brk = Bracket(f"Bracket_{tag}_{side}", (0, -1, 0), (0, 0, -1),
                      [f"{sign}(up_xc + rail_l/2 - rail_s/2)", yf, zr], "brk_a", "rail_s")
        cmds += _bracket(brk)
        names += [plate, brk.name]
    return cmds, names


def _side_rail_joints() -> tuple[list[Cmd], list[str]]:
    """Side rail end -> upright front face (D2)."""
    return _tee_joints("SideRail", "frame_top")


def _crossbar_joints() -> tuple[list[Cmd], list[str]]:
    """Crossbar ends -> upright inner faces (J2, J3, J5, J6). L-plate on the flush back faces
    (lower bar: leg up, clear of the panel; upper bar: leg down), gusset under each bar end."""
    cmds: list[Cmd] = []
    names: list[str] = []
    for bar, z, up in (("Low", "bar1_z", True), ("High", "bar2_z", False)):
        zb, zt = f"(desk_h + {z} - rail_l/2)", f"(desk_h + {z} + rail_l/2)"
        for side, sign in (("R", 1), ("L", -1)):
            s = "" if sign > 0 else "-"
            xi, xo = f"{s}(up_xc - rail_l/2)", f"{s}(up_xc + rail_l/2)"
            xa = f"{s}(up_xc - rail_l/2 - plate_arm)"
            # L-plate in world (X, Z) on plane normal -Y; extruded "negative" = +Y (behind).
            if up:
                z1 = f"{zt} + plate_ext"
                ell = [(xa, zb), (xo, zb), (xo, z1), (xi, z1), (xi, zt), (xa, zt)]
            else:
                z0 = f"{zb} - plate_ext"
                ell = [(xa, zb), (xi, zb), (xi, z0), (xo, z0), (xo, zt), (xa, zt)]
            plate = f"Plate_Bar{bar}_{side}"
            cmds += _plate(plate, (1, 0, 0), (0, 0, 1), ell, "negative",
                           ["0 mm", "up_y + rail_l/2", "0 mm"])
            brk = Bracket(f"Bracket_Bar{bar}_{side}", (-sign, 0, 0), (0, 0, -1),
                          [xi, "up_y + bar_y_off", zb], "brk_a", "rail_s")
            cmds += _bracket(brk)
            names += [plate, brk.name]
    return cmds, names


def _stile_joints() -> tuple[list[Cmd], list[str]]:
    """Stiles between the crossbars (stile rests on the lower bar, L2): an inside-corner bracket on
    each side of each stile end, in the frame plane so nothing sticks out front or back (J5, J8)."""
    cmds: list[Cmd] = []
    names: list[str] = []
    for stile, x in (("Main", "m1_x"), ("Side", "m3_x")):
        for bar, z, up in (("Low", "bar1_z + rail_l/2", 1), ("High", "bar2_z - rail_l/2", -1)):
            for side, sign in (("R", 1), ("L", -1)):
                s = "+" if sign > 0 else "-"
                brk = Bracket(f"Bracket_Stile{stile}_{bar}{side}", (sign, 0, 0), (0, 0, up),
                              [f"{x} {s} rail_l/2", "stile_y", f"desk_h + {z}"],
                              "brk_a_small", "rail_s")
                cmds += _bracket(brk)
                names.append(brk.name)
    return cmds, names


def _standoff(name: str, x: str, z: str) -> Cmd:
    return {"command": "solid.cylinder",
            "params": {"diameter": "so_d", "height": "pnl_back_gap", "axis": "Y",
                       "base": [x, "up_y + rail_l/2", z], "operation": "new",
                       "name": name, "body_name": name}}


def _panel_standoffs() -> tuple[list[Cmd], list[str]]:
    """Standoffs hold the panel off the back faces so plates and bolt heads stay clear.
    Each lands on a slot: crossbars' upper slot, uprights' outer slot (one per upright stub below
    the desk). The panel needs no support behind it everywhere; its bottom hangs free."""
    slot = "(rail_l/2 - rail_s/2)"
    spots: list[tuple[str, str, str]] = []
    for bar, z in (("Low", "bar1_z"), ("High", "bar2_z")):
        for tag, x in (("C", "0 mm"), ("R", "so_bar_x"), ("L", "-so_bar_x")):
            spots.append((f"Standoff_Bar{bar}_{tag}", x, f"desk_h + {z} + {slot}"))
    for side, s in (("R", ""), ("L", "-")):
        x = f"{s}(up_xc + {slot})"
        spots.append((f"Standoff_Post{side}", x, "frame_top - up_below/2"))
    return [_standoff(*spot) for spot in spots], [spot[0] for spot in spots]


def joint_commands() -> tuple[list[Cmd], list[str]]:
    """All joint hardware commands and the body names they create."""
    cmds: list[Cmd] = []
    names: list[str] = []
    for build in (_side_rail_joints, _crossbar_joints, _stile_joints, _panel_standoffs):
        c, n = build()
        cmds += c
        names += n
    return cmds, names
