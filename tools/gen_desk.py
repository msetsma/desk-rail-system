"""Generate desk_rails.json, the SolidCraft build script for the desk + rail model.

Edit PARAMS here (or in the app's Parameters table), then:

    python tools/gen_desk.py
    solidcraft-cli run desk_rails.json --save desk_rails.solidcraft --quiet

Axes: origin on the floor under the frame center, X = width (+ right), Y = depth (+ toward the
wall), Z = up. Lengths in mm unless an expression carries a unit.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from joints import JOINT_PARAMS, joint_commands

__all__ = ["build_commands", "main"]

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PROFILES = ROOT / "profiles"
OUT = ROOT / "desk_rails.json"

Cmd = dict[str, object]

# (name, expression, comment). Comments starting with MEASURE are for the user's caliper numbers.
PARAMS: Sequence[tuple[str, str, str]] = (
    # Desktop
    ("desk_h", "30 in", "Desktop TOP surface height above floor (range ~22.5-48.5 in)"),
    ("desk_w", "74 in", "Desktop width X (Karlby 74; new top TBD)"),
    ("desk_d", "26 in", "Desktop depth Y (Karlby 26; new top TBD)"),
    ("desk_t", "1.5 in", "Desktop thickness"),
    ("desk_y_off", "0 in", "Desktop center offset from frame center, +Y = toward wall"),
    # Extrusion sizes (20-series)
    ("rail_l", "40 mm", "Extrusion long side (4040 / 2040)"),
    ("rail_s", "20 mm", "Extrusion short side (2040)"),
    # Frame (TopSupport_*, ChannelBar_*, Leg_*, Foot_*)
    ("up_side_inset", "0 in", "Side rail / upright outer face inset from desktop side edge (X)"),
    ("frame_w", "desk_w - 2*(rail_s + up_side_inset)",
     "Derived: TopSupport outer-to-outer (X). Channel bars get cut to suit; override with a number if needed"),
    ("ts_len", "21.125 in", "MEASURE TopSupport: length front to back (Y), PDF 21.125"),
    ("ts_w", "1.45 in", "MEASURE TopSupport: width (X), PDF 1.45"),
    ("ts_h", "1.57 in", "MEASURE TopSupport: height (Z), PDF 1.57"),
    ("ch_h", "1.2 in", "MEASURE ChannelBar: height (Z)"),
    ("ch_bar_w", "1 in", "MEASURE ChannelBar: width of one bar (Y)"),
    ("ch_y_off", "0 in", "MEASURE ChannelBar/Leg: front-back offset of leg pairs from top support center, +Y = wall"),
    ("leg_yc", "5.6 in", "MEASURE Leg: frame center to leg center (Y); front/back symmetric"),
    ("leg_x", "2.75 in", "MEASURE Leg: top stage size along X"),
    ("leg_y", "2 in", "MEASURE Leg: top stage size along Y"),
    ("ch_bar_gap", "leg_y", "MEASURE ChannelBar: gap between the 2 bars of one channel (leg sits in it)"),
    ("leg_inset", "ts_w + leg_x/2", "MEASURE Leg: top support outer face to leg center (X)"),
    ("foot_len", "27.5 in", "Foot: length (Y)"),
    ("foot_w", "2.75 in", "MEASURE Foot: width (X)"),
    ("foot_h", "1.25 in", "MEASURE Foot: height incl. glides (Z)"),
    ("frame_top", "desk_h - desk_t", "Derived: desktop underside = frame top"),
    # Monitors (direct VESA mount via printed adapters on vertical stiles; sizes without stands)
    ("m1_w", "714 mm", "MEASURE Monitor_Main: 32in 16:9 width (X)"),
    ("m1_h", "420 mm", "MEASURE Monitor_Main: height (Z)"),
    ("m1_t", "48 mm", "MEASURE Monitor_Main: max depth incl. rear bulge (Y)"),
    ("m3_w", "363 mm", "MEASURE Monitor_Side: 27in rotated portrait, width (X)"),
    ("m3_h", "612 mm", "MEASURE Monitor_Side: height (Z)"),
    ("m3_t", "45 mm", "MEASURE Monitor_Side: max depth incl. rear bulge (Y)"),
    ("mon_panel_t", "12 mm", "MEASURE Monitors: thin outer-edge thickness (screen slab)"),
    ("mon_back_frac", "0.6", "Rear bulge size as a fraction of monitor width / height (envelope only)"),
    ("m1_x", "0 mm", "Main monitor center X"),
    ("mon_clearance", "8 in", "Gap: desktop surface to bottom edge of the monitors (space for items under them)"),
    ("mon_gap", "10 mm", "Gap between monitor edges"),
    ("m3_bot", "mon_clearance", "Side monitor bottom edge above desktop surface"),
    ("mon_standoff", "15 mm", "VESA adapter thickness: stile front face to monitor back"),
    ("vesa", "100 mm", "MEASURE Monitors: VESA hole pattern size (100x100 typical at 27-32in)"),
    ("m1_tilt", "0 deg", "Main monitor tilt back (top away from you), set by a wedge adapter"),
    ("m3_yaw", "15 deg",
     "Side monitor toe-in toward you about its inner front edge (stays at the main's front depth)"),
    ("m1_off", "mon_standoff + m1_h*mon_back_frac/2*sin(m1_tilt)",
     "Monitor_Main adapter thickness at the VESA center (grows with tilt so the bulge clears the stile)"),
    ("bar1_gap", "25 mm",
     "Lower crossbar top below the lowest monitor bottom edge (bar shows in the gap; mount things to it)"),
    ("m3_edge_x", "m1_x - m1_w/2 - mon_gap", "Derived: side monitor inner (right) front edge X"),
    ("m3_x", "m3_edge_x - m3_w/2*cos(m3_yaw) - m3_t*sin(m3_yaw)",
     "Derived: side monitor VESA center X after toe-in (Stile_Side sits here)"),
    ("vesa_adp", "120 mm", "MEASURE VESA adapter: outside size (square, centered on the VESA center)"),
    ("m1_adp_top", "mon_clearance + m1_h/2 + vesa_adp/2",
     "Derived: Monitor_Main adapter top above desktop surface (ports sit at/below it; before tilt)"),
    ("m3_adp_top", "m3_bot + m3_h/2 + vesa_adp/2",
     "Derived: Monitor_Side adapter top above desktop surface (ports sit at/below it; before tilt)"),
    # Rear uprights + crossbars
    ("rear_gap", "10 mm", "Desktop rear edge to upright front face"),
    ("up_y", "desk_d/2 + desk_y_off + rear_gap + rail_l/2", "Derived: upright center Y"),
    ("up_xc", "frame_w/2 + rail_s - rail_l/2", "Derived: upright center X (outer face flush with side rail)"),
    ("bar1_z", "min(mon_clearance, m3_bot) - bar1_gap - rail_l/2",
     "Lower crossbar center above desktop surface (default: in the gap under the monitors)"),
    ("bar2_z", "max(m1_adp_top, m3_adp_top) - rail_l/2",
     "Upper crossbar center above desktop surface (default: top flush with the highest adapter top;"
     " stiles sit between the bars, so an adapter may overlap the coplanar bar front)"),
    ("up_above", "bar2_z + rail_l/2", "Derived: upright top above desktop surface (flush with upper crossbar)"),
    ("bar_y_off", "rail_l/2 - rail_s/2",
     "Crossbar center Y from upright center: +10 = on back slot (back faces flush), -10 = front slot"),
    ("stile_y", "up_y + bar_y_off", "Derived: stile center Y (between the crossbars, faces flush)"),
    ("stile_front", "stile_y - rail_s/2", "Derived: stile front face Y (monitor adapters bolt here)"),
    ("mon_front", "stile_front - m1_off - m1_t", "Derived: main monitor front face Y (before tilt)"),
    ("m3_off", "stile_front - mon_front - m3_t*cos(m3_yaw) + m3_w/2*sin(m3_yaw)",
     "Derived: Monitor_Side adapter thickness at the VESA center (wedge; inner front edge meets the main's)"),
    # Side rails (2040 along each top support's outer face, front end butting the upright front face;
    # T-joint: flat joining plate on the shared outer face + end anchor + inside corner bracket)
    ("side_front", "-ts_len/2", "Side rail front end Y (default: top support front end)"),
    # Ergonomics (eye marker; tools/audit.py checks screen height and gaze angles against it)
    ("eye_above_desk", "18 in",
     "MEASURE Seated: floor-to-eye height minus your typing desk height (about the same standing)"),
    ("eye_back", "6 in", "MEASURE Eyes out from the desktop front edge (toward you, -Y) in your normal posture"),
    # Speakers (Klipsch Reference R-40M pair, hung by their own swivel mount on the back, ~3/4 up, from
    # a bracket in the upright's front slot: vertical slot = height is free; swivel = toe-in + tilt down)
    ("spk_w", "147.6 mm", "Speaker: width (X), R-40M spec"),
    ("spk_d", "214.3 mm", "Speaker: depth front to back (Y), R-40M spec"),
    ("spk_h", "298.5 mm", "Speaker: height (Z), R-40M spec"),
    ("spk_horn", "110 mm", "MEASURE Speaker: square Tractrix horn faceplate size (1in tweeter, centered on it)"),
    ("spk_wf_d", "115 mm", "MEASURE Speaker: woofer outside diameter incl. trim ring (4in spun-copper cone)"),
    ("spk_mount_frac", "0.75", "MEASURE Speaker: swivel mount height on the back, as a fraction of height from the bottom"),
    ("spk_tw_down", "3 in", "MEASURE Speaker: tweeter center below the speaker top"),
    ("spk_wf_down", "spk_tw_down + spk_horn/2 + 10 mm + spk_wf_d/2",
     "MEASURE Speaker: woofer center below the speaker top (default: just under the horn)"),
    ("spk_bot", "mon_clearance", "Speaker bottom above desktop surface (bracket slides along the upright slot)"),
    ("spk_mount_d", "30 mm", "Upright front face to the speaker back at the swivel (bracket + swivel depth)"),
    ("spk_px", "up_xc + rail_l/2 - spk_w/2",
     "Speaker swivel X (default: speaker outer face flush with the upright before toe-in)"),
    ("spk_py", "up_y - rail_l/2 - spk_mount_d", "Derived: swivel Y (speaker back face)"),
    ("spk_pz", "spk_bot + spk_mount_frac*spk_h", "Derived: swivel height above desktop surface"),
    ("spk_aim", "atan((spk_px - m1_x) / (spk_py - spk_d/2 + desk_d/2 - desk_y_off + eye_back))",
     "Derived: toe-in that points the speakers straight at the Eye marker"),
    ("spk_yaw_max", "25 deg", "Toe-in limit (the left speaker nears the portrait monitor past this)"),
    ("spk_yaw", "min(spk_aim, spk_yaw_max)", "Speaker toe-in actually used"),
    ("spk_tilt_aim", "atan((spk_bot + spk_h - spk_tw_down - eye_above_desk) * cos(spk_aim)"
     " / (spk_py - spk_d/2 + desk_d/2 - desk_y_off + eye_back))",
     "Derived: tilt down that points the tweeter at the Eye (negative = it would need to tilt up)"),
    ("spk_tilt", "max(spk_tilt_aim, 0 deg)", "Speaker tilt down actually used (the swivel tilts down only)"),
    # Modesty / privacy panel (behind the uprights)
    ("pnl_drop", "14 in", "Panel bottom below desktop underside"),
    ("pnl_cover", "15 mm", "Panel rise past the highest of the upright tops and adapter tops (hides cable exits)"),
    ("pnl_above", "max(up_above, m1_adp_top, m3_adp_top) + pnl_cover",
     "Panel top above desktop surface (monitors show above it; ports + cables stay hidden)"),
    ("pnl_t", "0.25 in", "Panel thickness"),
    ("pnl_back_gap", "12 mm", "Standoff length: upright/crossbar back face to panel (clears plates + bolt heads)"),
    ("pnl_side", "0 mm", "Panel overhang past each upright outer face (X)"),
)

UNITLESS = frozenset({"mon_back_frac", "spk_mount_frac"})
# Pinned to the top of the app's Parameters table.
FAVORITES = frozenset({"desk_h", "desk_w", "desk_d", "mon_clearance"})


@dataclass(frozen=True)
class Standard:
    """One extrusion standard and its 4040/2040 profile files.

    ``wide_x_2040``: the 2040 DXF is drawn 40 wide along X (else 20 wide, 40 tall).
    """

    key: str
    row: str
    f4040: str
    f2040: str
    wide_x_2040: bool


STANDARDS: Sequence[Standard] = (
    Standard("HFS5", "Misumi_HFS5", "misumi_hfs5_4040.dxf", "misumi_hfs5_2040.dxf", False),
    Standard("8020", "8020_20series", "8020_20-4040.dxf", "8020_20-2040.dxf", True),
    Standard("VSLOT", "OpenBuilds_Vslot", "openbuilds_vslot_4040.dxf", "openbuilds_vslot_2040.dxf", False),
)
DEFAULT_ROW = "Misumi_HFS5"

COLORS: Mapping[str, tuple[str, str]] = {
    "wood": ("#B5835A", "Butcher block"),
    "steel": ("#2E3136", "Frame steel (black)"),
    "alu": ("#D4D8DD", "Aluminium extrusion"),
    "panel": ("#4F6D7A", "Modesty panel"),
    "screen": ("#15171A", "Monitor"),
    "hardware": ("#D98E04", "Joint hardware (brackets, plates)"),
    "speaker": ("#3B3431", "Speaker"),
    "copper": ("#B87333", "Spun-copper woofer"),
    "eye": ("#E0412F", "Eye position marker"),
}


def box(name: str, length: str, width: str, height: str, center: Sequence[str]) -> Cmd:
    return {
        "command": "solid.box",
        "params": {"name": name, "body_name": name, "operation": "new",
                   "length": length, "width": width, "height": height, "center": list(center)},
    }


def frame_boxes() -> list[Cmd]:
    lx = "frame_w/2 - leg_inset"
    bar = "(ch_bar_gap/2 + ch_bar_w/2)"
    cmds = [
        box("Desktop", "desk_w", "desk_d", "desk_t", ["0 mm", "desk_y_off", "desk_h - desk_t/2"]),
        box("TopSupport_R", "ts_w", "ts_len", "ts_h", ["frame_w/2 - ts_w/2", "0 mm", "frame_top - ts_h/2"]),
        box("TopSupport_L", "ts_w", "ts_len", "ts_h", ["-(frame_w/2 - ts_w/2)", "0 mm", "frame_top - ts_h/2"]),
    ]
    for side, yc, outer_sign in (("Back", "leg_yc + ch_y_off", "+"), ("Front", "-leg_yc + ch_y_off", "-")):
        inner_sign = "-" if outer_sign == "+" else "+"
        for which, sign in (("Outer", outer_sign), ("Inner", inner_sign)):
            cmds.append(box(f"ChannelBar_{side}{which}", "frame_w - 2*ts_w", "ch_bar_w", "ch_h",
                            ["0 mm", f"{yc} {sign} {bar}", "frame_top - ch_h/2"]))
    for nm, x, y in (("RB", lx, "leg_yc + ch_y_off"), ("RF", lx, "-leg_yc + ch_y_off"),
                     ("LB", f"-({lx})", "leg_yc + ch_y_off"), ("LF", f"-({lx})", "-leg_yc + ch_y_off")):
        cmds.append(box(f"Leg_{nm}", "leg_x", "leg_y", "frame_top - foot_h", [x, y, "(frame_top + foot_h)/2"]))
    cmds += [
        box("Foot_R", "foot_w", "foot_len", "foot_h", [lx, "ch_y_off", "foot_h/2"]),
        box("Foot_L", "foot_w", "foot_len", "foot_h", [f"-({lx})", "ch_y_off", "foot_h/2"]),
    ]
    return cmds


def profile_sketch(name: str, plane: object, dxf: str) -> list[Cmd]:
    return [
        {"command": "sketch.create", "params": {"plane": plane, "name": name}},
        {"command": "sketch.insert_dxf", "params": {"path": (PROFILES / dxf).as_posix()}},
        {"command": "sketch.finish", "params": {}},
    ]


def placed_extrusion(body: str, sketch: str, length: str, translate: Sequence[str]) -> list[Cmd]:
    return [
        {"command": "solid.extrude", "params": {"sketch": sketch, "distance": length, "operation": "new",
                                                "name": body, "body_name": body}},
        {"command": "solid.move", "params": {"bodies": [body], "translate": list(translate),
                                             "name": f"Place_{body}"}},
    ]


def extrusion_set(std: Standard) -> tuple[list[Cmd], list[str], list[str]]:
    """Commands, feature names and body names of one standard's extrusions."""
    k = std.key
    # 2040 crossbar: extrude +X, 40 side along Z. 2040 side rail: extrude +Y, 40 side along Z.
    # 2040 stile: extrude +Z, 40 side along X (faces the monitors).
    if std.wide_x_2040:
        bar_plane = {"origin": [0, 0, 0], "x_dir": [0, 0, 1], "y_dir": [0, -1, 0]}
        side_plane = {"origin": [0, 0, 0], "x_dir": [0, 0, 1], "y_dir": [1, 0, 0]}
        stile_plane: object = "XY"
    else:
        bar_plane = {"origin": [0, 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}
        side_plane = {"origin": [0, 0, 0], "x_dir": [-1, 0, 0], "y_dir": [0, 0, 1]}
        stile_plane = {"origin": [0, 0, 0], "x_dir": [0, -1, 0], "y_dir": [1, 0, 0]}
    cmds = (profile_sketch(f"Profile4040_{k}", "XY", std.f4040)
            + profile_sketch(f"Profile2040bar_{k}", bar_plane, std.f2040)
            + profile_sketch(f"Profile2040side_{k}", side_plane, std.f2040)
            + profile_sketch(f"Profile2040stile_{k}", stile_plane, std.f2040))
    up_len, up_z0 = "desk_h + up_above - frame_top + up_below", "frame_top - up_below"
    bar_len, bar_x0 = "2*up_xc - rail_l", "-(up_xc - rail_l/2)"
    side_len = "up_y - rail_l/2 - side_front"
    side_x, side_z = "frame_w/2 + rail_s/2", "frame_top - rail_l/2"
    # Stiles sit between the crossbars: resting on the lower bar, butting the upper bar's underside.
    stile_len, stile_z0 = "bar2_z - bar1_z - rail_l", "desk_h + bar1_z + rail_l/2"
    parts = (
        ("Upright_R", f"Profile4040_{k}", up_len, ["up_xc", "up_y", up_z0]),
        ("Upright_L", f"Profile4040_{k}", up_len, ["-up_xc", "up_y", up_z0]),
        ("Crossbar_Low", f"Profile2040bar_{k}", bar_len, [bar_x0, "up_y + bar_y_off", "desk_h + bar1_z"]),
        ("Crossbar_High", f"Profile2040bar_{k}", bar_len, [bar_x0, "up_y + bar_y_off", "desk_h + bar2_z"]),
        ("SideRail_R", f"Profile2040side_{k}", side_len, [side_x, "side_front", side_z]),
        ("SideRail_L", f"Profile2040side_{k}", side_len, [f"-({side_x})", "side_front", side_z]),
        ("Stile_Main", f"Profile2040stile_{k}", stile_len, ["m1_x", "stile_y", stile_z0]),
        ("Stile_Side", f"Profile2040stile_{k}", stile_len, ["m3_x", "stile_y", stile_z0]),
    )
    bodies, features = [], []
    for part, sketch, length, tr in parts:
        body = f"{part}_{k}"
        cmds += placed_extrusion(body, sketch, length, tr)
        bodies.append(body)
        features += [body, f"Place_{body}"]
    return cmds, features, bodies


def panel() -> Cmd:
    return box("ModestyPanel", "2*up_xc + rail_l + 2*pnl_side", "pnl_t", "pnl_drop + desk_t + pnl_above",
               ["0 mm", "up_y + rail_l/2 + pnl_back_gap + pnl_t/2",
                "(frame_top - pnl_drop + desk_h + pnl_above)/2"])


def _turn(bodies: Sequence[str], name: str, axis: Sequence[int], angle: str) -> Cmd:
    return {"command": "solid.move", "params": {"bodies": list(bodies), "axis": list(axis), "angle": angle,
                                                "name": name}}


def _shift(bodies: Sequence[str], name: str, translate: Sequence[str]) -> Cmd:
    return {"command": "solid.move", "params": {"bodies": list(bodies), "translate": list(translate),
                                                "name": name}}


def monitors() -> tuple[list[Cmd], list[str]]:
    """Each monitor: thin screen slab plus a smaller rear bulge carrying the VESA face.

    Main is built around its VESA face center. Side is built around its inner (right) front edge,
    toed in about that edge, and placed so the edge meets the main's left front edge at the same
    depth. Both then tilt together about the main's VESA axis, so the edges stay matched.
    """
    main, side = ["Monitor_Main", "Monitor_Main_Back"], ["Monitor_Side", "Monitor_Side_Back"]
    b1, b3 = "(m1_t - mon_panel_t)", "(m3_t - mon_panel_t)"
    ty, tz = "stile_front - m1_off", "desk_h + mon_clearance + m1_h/2"
    return [
        box(main[0], "m1_w", "mon_panel_t", "m1_h", ["0 mm", f"-{b1} - mon_panel_t/2", "0 mm"]),
        box(main[1], "m1_w*mon_back_frac", b1, "m1_h*mon_back_frac", ["0 mm", f"-{b1}/2", "0 mm"]),
        _shift(main, "Place_Monitor_Main", ["m1_x", ty, tz]),
        box(side[0], "m3_w", "mon_panel_t", "m3_h", ["-m3_w/2", "mon_panel_t/2", "0 mm"]),
        box(side[1], "m3_w*mon_back_frac", b3, "m3_h*mon_back_frac", ["-m3_w/2", f"mon_panel_t + {b3}/2", "0 mm"]),
        _turn(side, "Aim_Monitor_Side", (0, 0, 1), "m3_yaw"),
        _shift(side, "Place_Monitor_Side", ["m3_edge_x", "mon_front", "desk_h + m3_bot + m3_h/2"]),
        _shift(main + side, "Tilt_Monitors_To", ["0 mm", f"-({ty})", f"-({tz})"]),
        _turn(main + side, "Tilt_Monitors", (1, 0, 0), "-m1_tilt"),
        _shift(main + side, "Tilt_Monitors_Back", ["0 mm", ty, tz]),
    ], main + side


def _speaker_face(side: str) -> tuple[list[Cmd], str, str]:
    """R-40M front details in the speaker's build frame (swivel at origin): Tractrix horn plate
    and woofer, 3 mm proud of the front face so they show in renders."""
    top, front = "spk_h*(1 - spk_mount_frac)", "-spk_d"
    horn, woofer = f"SpkFace_{side}_Horn", f"SpkFace_{side}_Woofer"
    return [
        box(horn, "spk_horn", "3 mm", "spk_horn", ["0 mm", f"{front} - 1.5 mm", f"{top} - spk_tw_down"]),
        {"command": "solid.cylinder",
         "params": {"diameter": "spk_wf_d", "height": "3 mm", "axis": "Y",
                    "base": ["0 mm", f"{front} - 3 mm", f"{top} - spk_wf_down"], "operation": "new",
                    "name": woofer, "body_name": woofer}},
    ], horn, woofer


def speakers() -> tuple[list[Cmd], list[str], list[str], list[str], list[str]]:
    """Speaker envelopes (with front details) hung from their back swivel (built around it, tilted
    down, toed in, then placed), plus the mount: flange in the upright's front slot, block out to
    the swivel, swivel. Returns commands, speaker, mount, horn and woofer body names."""
    pz = "desk_h + spk_pz"
    cmds: list[Cmd] = []
    mounts: list[str] = []
    horns: list[str] = []
    woofers: list[str] = []
    for side, s, turn in (("R", "", "-spk_yaw"), ("L", "-", "spk_yaw")):
        spk, m = f"Speaker_{side}", f"SpkMount_{side}"
        face, horn, woofer = _speaker_face(side)
        horns.append(horn)
        woofers.append(woofer)
        whole = [spk, horn, woofer]
        cmds += [box(spk, "spk_w", "spk_d", "spk_h", ["0 mm", "-spk_d/2", "spk_h/2 - spk_mount_frac*spk_h"]),
                 *face,
                 _turn(whole, f"Tilt_{spk}", (1, 0, 0), "spk_tilt"),
                 _turn(whole, f"Aim_{spk}", (0, 0, 1), turn),
                 _shift(whole, f"Place_{spk}", [f"{s}spk_px", "spk_py", pz]),
                 box(f"{m}_Flange", "rail_l", "4 mm", "60 mm", [f"{s}up_xc", "up_y - rail_l/2 - 2 mm", pz]),
                 box(f"{m}_Block", "up_xc + rail_l/2 - spk_px + 10 mm", "spk_mount_d - 18 mm", "30 mm",
                     [f"{s}(up_xc + rail_l/2 + spk_px - 10 mm)/2", "(spk_py + 14 mm + up_y - rail_l/2 - 4 mm)/2", pz]),
                 # Ball swivel 8 mm behind the speaker back: clears the back face up to ~40 deg combined turn.
                 {"command": "solid.sphere",
                  "params": {"diameter": "12 mm", "center": [f"{s}spk_px", "spk_py + 8 mm", pz],
                             "operation": "new", "name": f"{m}_Swivel", "body_name": f"{m}_Swivel"}}]
        mounts += [f"{m}_Flange", f"{m}_Block", f"{m}_Swivel"]
    return cmds, ["Speaker_R", "Speaker_L"], mounts, horns, woofers


def eye_marker() -> Cmd:
    return {"command": "solid.sphere",
            "params": {"name": "Eye", "body_name": "Eye", "operation": "new", "diameter": "30 mm",
                       "center": ["m1_x", "-desk_d/2 + desk_y_off - eye_back", "desk_h + eye_above_desk"]}}


def appearance(bodies: Sequence[str], look: str) -> Cmd:
    color, label = COLORS[look]
    return {"command": "appearance.assign", "params": {"bodies": list(bodies), "color": color, "name": label}}


def configurations(features: Mapping[str, Sequence[str]]) -> Iterator[Cmd]:
    every = [f for fs in features.values() for f in fs]
    yield {"command": "config.configure", "params": {"features": every}}
    for std in STANDARDS:
        own = set(features[std.key])
        values = {f"suppress:{f}": "false" if f in own else "true" for f in every}
        yield {"command": "config.row", "params": {"name": std.row, "values": values}}
    yield {"command": "config.row", "params": {"name": "Default", "delete": True}}
    yield {"command": "config.activate", "params": {"row": DEFAULT_ROW}}


def build_commands() -> list[Cmd]:
    cmds: list[Cmd] = [{"command": "parameters.add", "params": {"name": n, "expression": e, "comment": c}}
                       for n, e, c in (*PARAMS, *JOINT_PARAMS)]
    for cmd in cmds:
        if cmd["params"]["name"] in UNITLESS:  # type: ignore[index]
            cmd["params"]["unit"] = ""  # type: ignore[index]
        if cmd["params"]["name"] in FAVORITES:  # type: ignore[index]
            cmd["params"]["favorite"] = True  # type: ignore[index]
    frame = frame_boxes()
    cmds += frame
    features: dict[str, list[str]] = {}
    alu: list[str] = []
    for std in STANDARDS:
        set_cmds, feats, bodies = extrusion_set(std)
        cmds += set_cmds
        features[std.key] = feats
        alu += bodies
    cmds.append(panel())
    screens, screen_names = monitors()
    cmds += screens
    spk_cmds, spk_names, spk_mounts, spk_horns, spk_woofers = speakers()
    cmds += spk_cmds
    cmds.append(eye_marker())
    joint_cmds, hardware = joint_commands()
    cmds += joint_cmds
    steel = [c["params"]["body_name"] for c in frame if c["params"]["name"] != "Desktop"]  # type: ignore[index]
    cmds += [appearance(["Desktop"], "wood"), appearance(steel, "steel"),
             appearance(alu, "alu"), appearance(["ModestyPanel"], "panel"),
             appearance(screen_names, "screen"), appearance(hardware, "hardware"),
             appearance(spk_names, "speaker"), appearance(spk_mounts, "hardware"),
             appearance(spk_horns, "screen"), appearance(spk_woofers, "copper"),
             appearance(["Eye"], "eye")]
    cmds += list(configurations(features))
    return cmds


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cmds = build_commands()
    OUT.write_text(json.dumps({"commands": cmds}, indent=1), encoding="utf-8")
    log.info("wrote %s (%d commands)", OUT, len(cmds))


if __name__ == "__main__":
    main()
