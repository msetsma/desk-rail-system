"""Generate the lower-crossbar console parts: ACC-01 grommet, ACC-02/03/05 printed bays, ACC-06 inlay strip.

Layout (bay edges, face rake, device pockets) comes from ACC_layout.py, shared with the device generator, so a
pocket and the device it holds can't drift apart. The bays use the console frame (ACC_layout docstring): origin on
the bar front face at the top line, console centre x. Each bay is a box trimmed by the raked face; pockets are
boxes built in a "face frame" (x, depth into the console, up the face) and turned into place in one batch, then cut
with one combine. Screws: M5 button heads through a 6 mm spine into HNTT5-5 drop-in T-nuts in the bar's two front
slots (z from the skeleton: con_top + 10 and + 30 below the top line); d4 dowel pins align the bays at the seams
(ACC-04, the control bay, was retired 2026-11-02). Cables leave each bay at the back, over the bar top or below its bottom, to run behind the rails.

    python parts/src/ACC-01-06_console_gen.py
"""
from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "tools"))

import ACC_layout as L  # noqa: E402
import skeleton_values  # noqa: E402

__all__ = ["build_bay", "build_grommet", "build_inlay", "main"]

GEN = "parts/src/ACC-01-06_console_gen.py"
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
SKEL = {"command": "parameters.import", "params": {"path": f"{ROOT.as_posix()}/skeleton/params.json"}}
MATERIAL = "ABS"  # printed in ASA/PETG; ABS density stands in
CHARCOAL = "#34373b"  # matches the user's duckyPad case print
LIGHT_GREY = "#c9cccf"  # duckyPad keycaps and knobs
SOURCE = "3D printed (user's printer), concept 2026-11-02; device sizes partly estimated (see ACC_layout)"
FRAME_NOTE = ("Origin: console top line on the lower crossbar front face at the console centre x (con_x); "
              "+X right, +Y toward the wall, +Z up")

SPINE_T = 6.0  # spine behind the screw counterbores
BORE_D, SCREW_D = 10.0, 5.5  # M5 button head counterbore, clearance
DOWEL_D, DOWEL_DEPTH = 4.2, 8.0
DOWEL_PTS = ((-30.0, -30.0), (-40.0, -90.0))  # (y, z) on the seam faces, clear of every pocket
END_R = 8.0  # outer end radius
GROOVE_X = L.WIDTH / 2 - END_R - 1.0  # groove and inlay end x
OVER = 0.1  # cut overrun (AGENTS §3)


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def f(v: float) -> float:
    return round(v, 3)


class FaceTools:
    """Boxes and cylinders defined in the face frame, rotated onto the raked face and cut in one combine."""

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self.names: list[str] = []
        self.cmds: list[dict] = []

    def box(self, tag: str, x0: float, x1: float, s0: float, s1: float, d0: float, d1: float) -> None:
        """x range, s range (down the face), depth range (into the console; negative = in front)."""
        name = f"{self.prefix}_T_{tag}"
        self.names.append(name)
        self.cmds.append(c("solid.box", name=name, body_name=name, operation="new",
                           corner=[f(x0), f(d0), f(-s1)], length=f(x1 - x0), width=f(d1 - d0), height=f(s1 - s0)))

    def cyl(self, tag: str, x: float, s: float, dia: float, d0: float, d1: float) -> None:
        name = f"{self.prefix}_T_{tag}"
        self.names.append(name)
        self.cmds.append(c("solid.cylinder", name=name, body_name=name, operation="new", axis="Y",
                           diameter=f(dia), height=f(d1 - d0), base=[f(x), f(d0), f(-s)]))

    def cut_into(self, target: str) -> list[dict]:
        return [
            *self.cmds,
            c("solid.move", name=f"{self.prefix}_TiltTools", bodies=self.names, axis=[1, 0, 0], angle=f"{-L.RAKE_DEG} deg"),
            c("solid.move", name=f"{self.prefix}_PlaceTools", bodies=self.names, translate=[0, -L.D_TOP, 0]),
            c("solid.combine", name=f"{self.prefix}_FaceCuts", target=target, tools=self.names, operation="cut"),
        ]


def world_box(name: str, target: str, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float,
              op: str = "cut") -> dict:
    return c("solid.box", name=name, operation=op, targets=[target], corner=[f(x0), f(y0), f(z0)],
             length=f(x1 - x0), width=f(y1 - y0), height=f(z1 - z0))


def screw_bores(prefix: str, body: str, xs: Sequence[float], zs: Sequence[float], y_start: float) -> list[dict]:
    """Counterbore from inside the device pocket to the spine, clearance hole through the spine."""
    out = []
    for i, x in enumerate(xs):
        for j, z in enumerate(zs):
            tag = f"{prefix}_Screw{i + 1}{'ab'[j]}"
            out += [
                c("solid.cylinder", name=f"{tag}_Cbore", operation="cut", targets=[body], axis="Y",
                  diameter=BORE_D, height=f(-SPINE_T - y_start), base=[f(x), f(y_start), f(z)]),
                c("solid.cylinder", name=f"{tag}_Hole", operation="cut", targets=[body], axis="Y",
                  diameter=SCREW_D, height=f(SPINE_T + 2 * OVER), base=[f(x), f(-SPINE_T - OVER), f(z)]),
            ]
    return out


def dowels(prefix: str, body: str, ends: Sequence[tuple[float, int]]) -> list[dict]:
    """Dowel holes into the seam faces: (x of the face, +1 if the bay lies at larger x)."""
    out = []
    for k, (x, side) in enumerate(ends):
        for m, (y, z) in enumerate(DOWEL_PTS):
            base_x = x - side * OVER
            out.append(c("solid.cylinder", name=f"{prefix}_Dowel{k + 1}{'ab'[m]}", operation="cut", targets=[body],
                         axis="X" if side > 0 else [-1, 0, 0], diameter=DOWEL_D, height=DOWEL_DEPTH + OVER,
                         base=[f(base_x), f(y), f(z)]))
    return out


def wedge(prefix: str, body: str, bay: L.Bay, tools: FaceTools) -> list[dict]:
    """The bay blank; the front cut, parting groove and inlay groove go into the face batch."""
    # Grooves stop 1 mm short of the end round's tangent line (a coincident edge makes the boolean retry).
    gx0 = max(bay.x0, -GROOVE_X) - (1 if bay.x0 > -L.WIDTH / 2 else 0)
    gx1 = min(bay.x1, GROOVE_X) + (1 if bay.x1 < L.WIDTH / 2 else 0)
    tools.box("Groove", gx0, gx1, L.GROOVE_S - 1, L.GROOVE_S + 1, -1, 1)
    tools.box("InlayGroove", gx0, gx1, L.INLAY_S - L.INLAY_W / 2, L.INLAY_S + L.INLAY_W / 2, -1, L.INLAY_D)
    depth = L.D_TOP + L.HEIGHT * 0.5  # deeper than the face bottom (60 + 124 tan 20 = 105)
    front = FaceTools(f"{prefix}F")
    front.box("Front", bay.x0 - 1, bay.x1 + 1, -100, 400, -300, 0)
    cmds = [c("solid.box", name=f"{prefix}_Blank", body_name=body, operation="new",
              corner=[f(bay.x0), f(-depth), f(-L.HEIGHT)], length=f(bay.x1 - bay.x0), width=f(depth),
              height=f(L.HEIGHT)), *front.cut_into(body)]
    # Round the outer end while the solid is still simple (2.5 s on the finished bay, a fraction here).
    if bay.x0 <= -L.WIDTH / 2:
        cmds.append(end_round(prefix, body, bay.x0))
    if bay.x1 >= L.WIDTH / 2:
        cmds.append(end_round(prefix, body, bay.x1))
    return cmds


def end_round(prefix: str, body: str, x: float) -> dict:
    _, y, z = L.face_point(x, L.FACE_LEN / 2)
    return c("solid.fillet", name=f"{prefix}_EndRound", body=body, edges=[[f(x), f(y), f(z)]], radius=END_R)


def finish(body: str, pn: str, desc: str, color: str = CHARCOAL) -> list[dict]:
    return [
        c("material.assign", bodies=[body], material=MATERIAL),
        c("appearance.assign", bodies=[body], color=color),
        c("document.metadata.set", values={
            "part_number": pn, "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {"Material": "ASA/PETG print (ABS density)", "ReleaseState": "WIP", "Source": SOURCE}}),
    ]


def audio_bay(bay: L.Bay, slot_z: Sequence[float]) -> list[dict]:
    p, body = "AUD", "Bay_Audio"
    hub, sc = L.DEVICES["hub"], L.DEVICES["scarlett"]
    t = FaceTools(p)
    cmds = wedge(p, body, bay, t)
    # Tail under the bar for the Scarlett's tilted body: back to TAIL_Y, below the bar bottom (+4 mm).
    bar_bottom = slot_z[1] - 10.0
    s_bot = sc.s + sc.h / 2 + 3.0  # 3 mm skin under the Scarlett
    # Where that skin line meets z = -HEIGHT: depth along the face normal from the face.
    fy, fz = L.face_point(0, s_bot)[1:]
    ny, nz = L.inward()[1:]
    t_cross = (-L.HEIGHT - fz) / nz
    y_cross = fy + t_cross * ny
    t_back = (L.TAIL_Y - fy) / ny
    z_low = fz + t_back * nz - 1.0
    cmds += [
        world_box(f"{p}_Tail", body, bay.x0, bay.x1, -1.0, L.TAIL_Y, z_low, bar_bottom - 4.0, op="join"),
        world_box(f"{p}_Under", body, bay.x0, bay.x1, y_cross, L.TAIL_Y, z_low, -L.HEIGHT + OVER, op="join"),
        *screw_bores(p, body, (hub.x - 38, hub.x + 38), slot_z, -58.5),
        *dowels(p, body, ((bay.x1, -1),)),
    ]
    # Trim starts 1 mm deeper than where the skin line meets the bay bottom, so its corner sits inside the
    # Under block instead of on the bottom face (a coincident edge makes the boolean retry).
    t.box("UnderTrim", bay.x0 - 1, bay.x1 + 1, s_bot, 600, t_cross + 1, 400)
    t.box("Hub", hub.x - hub.w / 2, hub.x + hub.w / 2, hub.s - hub.h / 2, hub.s + hub.h / 2, -1, hub.d)
    cable_x0 = bay.x0 + 5.5
    # 1 mm inside the hub pocket's top, bottom and floor so no tool face lands on a pocket face.
    t.box("HubCable", cable_x0, hub.x - hub.w / 2 + OVER, hub.s - hub.h / 2 + 1, hub.s + hub.h / 2 - 1, 3, hub.d - 1)
    t.box("Scarlett", sc.x - sc.w / 2, sc.x + sc.w / 2, sc.s - sc.h / 2, sc.s + sc.h / 2, -1, sc.d + 60)
    cmds += t.cut_into(body)
    # Hub cable: riser from the cable cavity, then back over the bar top (2 mm top skin).
    cy, cz = L.face_point(0, hub.s - hub.h / 2)[1:]
    cmds += [
        # 1 mm in from the cavity's side faces (coincident faces make the boolean retry).
        world_box(f"{p}_HubCableRiser", body, cable_x0 + 1, cable_x0 + 13, cy + 6, cy + 22, cz - 4, -2.0),
        world_box(f"{p}_HubCableBack", body, cable_x0 + 1, cable_x0 + 13, cy + 12, OVER, -8.5, -2.5),
    ]
    desc = (f"Console audio bay (printed): Scarlett Solo 3rd Gen front panel and the 7-port USB hub port face flush in "
            f"the 20 deg face; Scarlett body runs back under the bar in a tail, its back open for plugs; hub cable "
            f"exits over the bar top; 4 x M5 + HNTT5-5. {FRAME_NOTE}")
    return [*cmds, *finish(body, bay.pn, desc)]


def phone_bay(bay: L.Bay, slot_z: Sequence[float]) -> list[dict]:
    p, body = "PHN", "Bay_Phone"
    ph, ms = L.DEVICES["phone"], L.DEVICES["magsafe"]
    t = FaceTools(p)
    cmds = wedge(p, body, bay, t)
    cmds += [
        *screw_bores(p, body, (ph.x - 58, ph.x + 58), slot_z[1:], -64.0),
        *dowels(p, body, ((bay.x0, 1), (bay.x1, -1))),
    ]
    s_top = ph.s - ph.h / 2
    t.box("Phone", ph.x - ph.w / 2, ph.x + ph.w / 2, s_top, ph.s + ph.h / 2, -1, ph.d)
    t.box("ThumbScoop", ph.x - 20, ph.x + 20, s_top - 7, s_top + OVER, -1.5, 8)
    t.cyl("MagSafe", ms.x, ms.s, ms.w, ph.d - OVER, ph.d + ms.d)
    # Relief for the camera plateau on the phone back (ACC-13: x 36..76, z -7..33 in the phone frame, 1.5 proud).
    t.box("CameraRelief", ph.x + 35, ph.x + 77, ph.s - 34, ph.s + 8, ph.d - 0.5, ph.d + 2.5)
    t.box("MagSafeCable", ms.x - 1.75, ms.x + 1.75, ms.s, 160, ph.d - OVER, ph.d + ms.d - 0.2)
    cmds += t.cut_into(body)
    desc = (f"Console phone bay (printed): iPhone 16 Pro Max (cased) landscape in a 12 mm pocket, screen flush, held by "
            f"the Apple MagSafe puck in a pocket behind it; thumb scoop at the top; MagSafe cable out the bottom; "
            f"2 x M5 + HNTT5-5. {FRAME_NOTE}")
    return [*cmds, *finish(body, bay.pn, desc)]


def kvm_key(p: str, body: str, t: FaceTools) -> list[dict]:
    """KVM key: MX switch in a 14 x 14 cut through a 1.5 mm plate, cavity behind, channel to a 3 mm back wall below
    the bar with a d6.2 hole for the 3.5 mm TRS panel jack (cable to the KVM under the desk)."""
    kv = L.DEVICES["kvm"]
    t.box("KeyPlate", kv.x - 7, kv.x + 7, kv.s - 7, kv.s + 7, -1, kv.d + OVER)
    t.box("KeySwitch", kv.x - 7.8, kv.x + 7.8, kv.s - 7.8, kv.s + 7.8, kv.d, 22)
    ky, kz = L.face_point(0, kv.s)[1:]
    return [
        world_box(f"{p}_KeyChannel", body, kv.x - 6, kv.x + 6, ky + 17, -3.0, kz - 14, kz - 2),
        c("solid.cylinder", name=f"{p}_TRSJack", operation="cut", targets=[body], axis="Y", diameter=6.2,
          height=3.0 + 2 * OVER, base=[f(kv.x), -3.0 - OVER, f(kz - 8)]),
    ]


def duckypad_bay(bay: L.Bay, slot_z: Sequence[float]) -> list[dict]:
    p, body = "DPP", "Bay_duckyPad"
    dp = L.DEVICES["duckypad"]
    t = FaceTools(p)
    cmds = wedge(p, body, bay, t)
    cmds += [*screw_bores(p, body, (dp.x - 40, dp.x + 15), slot_z, -80.0), *dowels(p, body, ((bay.x0, 1),))]
    s_top = dp.s - dp.h / 2
    t.box("Pocket", dp.x - dp.w / 2, dp.x + dp.w / 2, s_top, dp.s + dp.h / 2, -1, dp.d)
    usb_x = dp.x + 32.5  # case USB-C cut-out: +Z edge, device x 24.5..40.5 (ACC-16, from the user's STEP)
    t.box("UsbPlug", usb_x - 12, usb_x + 12, 2, s_top + OVER, 3, 22)
    key_cmds = kvm_key(p, body, t)
    cmds += t.cut_into(body)
    uy = L.face_point(0, 2)[1]
    cmds += [world_box(f"{p}_UsbBack", body, usb_x - 10, usb_x + 10, uy + 6, OVER, -8.5, -2.0), *key_cmds]
    desc = (f"Console duckyPad bay (printed): the KVM key (MX switch in a 1.5 mm plate, light grey cap, wired to a "
            f"3.5 mm TRS panel jack in the back wall) in a column left of the user's duckyPad Pro (standard case), "
            f"which sinks 25 mm so its top plate is flush with the 20 deg face; duckyPad USB-C plug cavity at the rear "
            f"edge, cable out over the bar top; 4 x M5 + HNTT5-5. {FRAME_NOTE}")
    return [*cmds, *finish(body, bay.pn, desc)]


def build_bay(bay: L.Bay, slot_z: Sequence[float]) -> list[dict]:
    makers = {"ACC-02": lambda: audio_bay(bay, slot_z), "ACC-03": lambda: phone_bay(bay, slot_z),
              "ACC-05": lambda: duckypad_bay(bay, slot_z)}
    return [*TEMPLATE, *makers[bay.pn]()]


def build_inlay() -> list[dict]:
    body = "Inlay_Strip"
    x = GROOVE_X - 0.1
    cmds = [c("solid.box", name="INL_Strip", body_name=body, operation="new",
              corner=[f(-x), 0, f(-(L.INLAY_S + L.INLAY_W / 2 - 0.1))], length=f(2 * x), width=f(L.INLAY_D - 0.1),
              height=f(L.INLAY_W - 0.2))]
    cmds += [c("solid.move", name="INL_Tilt", bodies=[body], axis=[1, 0, 0], angle=f"{-L.RAKE_DEG} deg"),
             c("solid.move", name="INL_Place", bodies=[body], translate=[0, -L.D_TOP, 0])]
    desc = (f"Console inlay line (printed, light grey): {2 * x:.0f} mm strip pressed flush into the groove "
            f"across all four bays, the console's light grey line. {FRAME_NOTE}")
    return [*TEMPLATE, *cmds, *finish(body, "ACC-06", desc, LIGHT_GREY)]


def build_grommet() -> list[dict]:
    body = "Grommet"
    desc = ("Desk cable grommet (printed): d80 x 2.5 flange on the desktop, sleeve through the grom_d hole (0.2 mm "
            "clearance), 6 mm wall. Origin: hole centre on the desktop top surface; +Y toward the wall, +Z up")
    cmds = [
        SKEL,
        c("solid.cylinder", name="GRM_Flange", body_name=body, operation="new", diameter="80 mm", height="2.5 mm",
          base=["0 mm", "0 mm", "0 mm"]),
        c("solid.cylinder", name="GRM_Sleeve", operation="join", targets=[body], diameter="grom_d - 0.4 mm",
          height="desk_t + 0.1 mm", base=["0 mm", "0 mm", "-desk_t"]),
        c("solid.cylinder", name="GRM_Bore", operation="cut", targets=[body], diameter="grom_d - 12 mm",
          height="desk_t + 2.7 mm", base=["0 mm", "0 mm", "-desk_t - 0.1 mm"]),
    ]
    return [*TEMPLATE, *cmds, *finish(body, "ACC-01", desc)]


def write(stem: str, commands: list[dict]) -> None:
    out = ROOT / "parts/src" / f"{stem}.json"
    out.write_text(json.dumps({"generated_by": GEN, "commands": commands}, indent=1), encoding="utf-8")


def main() -> None:
    v = skeleton_values.values()
    top_to_slot = v["con_top"] + 10.0  # 2040 front slots sit 10 and 30 mm below the bar top
    slot_z = (-top_to_slot, -(top_to_slot + 20.0))
    write("ACC-01_Grommet", build_grommet())
    for bay in L.BAYS:
        write(bay.stem, build_bay(bay, slot_z))
    write("ACC-06_Inlay", build_inlay())


if __name__ == "__main__":
    main()
