"""Generate the purchased-device reference parts of the lower-crossbar console (ACC-11..17).

One build script per device, each marked "generated_by". Envelopes come from ACC_layout.DEVICES, so the
devices and the console pockets agree. Fixed-shape purchased parts: no skeleton import.

Device local frame (all devices, see ACC_layout): origin = centre of the face the user sees when mounted
(flush with the console face); that face looks toward -Y (keys, knobs, caps stand proud toward -Y);
+Z = the device's top edge as mounted (up the console face); X right as the user sees it; the body
occupies y >= 0.

Detail positions are estimates from product photos (MEASURE) unless the Source says otherwise.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "parts/src"))
from ACC_layout import DEVICES, HUB_FP_PORT_X  # noqa: E402

__all__ = ["SCRIPTS", "main"]

GEN = "parts/src/ACC-11-17_devices_gen.py"
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
EPS = 0.1  # overrun of joins / cuts past the faces they start on (AGENTS §3)
AL_PBR = {"metallic": 0.85, "roughness": 0.4, "dielectric_ior": 1.5}
GLASS_PBR = {"metallic": 0.0, "roughness": 0.06, "dielectric_ior": 1.5}

Cmd = dict[str, object]


def c(cmd: str, **params: object) -> Cmd:
    return {"command": cmd, "params": params}


def mm(v: float) -> str:
    return f"{round(v, 4)} mm"


def box(name: str, body: str, x: tuple[float, float], y: tuple[float, float], z: tuple[float, float],
        op: str = "new", target: str | None = None) -> Cmd:
    """Axis-aligned box from ranges. op new names the body; join/cut act on `target` (default `body`)."""
    p: dict[str, object] = {"name": name, "corner": [x[0], y[0], z[0]], "length": mm(x[1] - x[0]),
                            "width": mm(y[1] - y[0]), "height": mm(z[1] - z[0]), "operation": op}
    if op == "new":
        p["body_name"] = body
    else:
        p["targets"] = [target or body]
    return c("solid.box", **p)


def cyl(name: str, body: str, axis: str, base: Sequence[float], d: float, h: float,
        op: str = "new", target: str | None = None) -> Cmd:
    """Cylinder d x h from `base` (centre of its bottom) along +axis."""
    p: dict[str, object] = {"name": name, "axis": axis, "base": list(base), "diameter": mm(d), "height": mm(h),
                            "operation": op}
    if op == "new":
        p["body_name"] = body
    else:
        p["targets"] = [target or body]
    return c("solid.cylinder", **p)


def cyl_y(name: str, body: str, x: float, z: float, d: float, y0: float, y1: float,
          op: str = "new", target: str | None = None) -> Cmd:
    """Cylinder on the device's Y axis (normal to the face) between y0 and y1."""
    return cyl(name, body, "Y", [x, y0, z], d, y1 - y0, op, target)


def merge(body: str, pieces: Sequence[Cmd]) -> list[Cmd]:
    """Separate lumps of one finish: each piece is built as its own new body, then all are combined into `body`
    (a join of a disjoint piece warns; solid.combine doesn't)."""
    out: list[Cmd] = []
    for i, piece in enumerate(pieces):
        params = dict(piece["params"])  # type: ignore[arg-type]
        params["operation"] = "new"
        params.pop("targets", None)
        params["body_name"] = body if i == 0 else f"{body}_{i}"
        out.append({"command": piece["command"], "params": params})
    tools = [f"{body}_{i}" for i in range(1, len(pieces))]
    if tools:
        out.append(c("solid.combine", name=f"{body}_Merge", target=body, tools=tools, operation="join"))
    return out


def finish(bodies: Sequence[str], material: str, color: str, pbr: dict[str, float] | None = None) -> list[Cmd]:
    look: dict[str, object] = {"bodies": list(bodies), "color": color}
    if pbr:
        look["pbr"] = pbr
    return [c("material.assign", bodies=list(bodies), material=material), c("appearance.assign", **look)]


def meta(pn: str, desc: str, material: str, source: str) -> Cmd:
    frame = (" Origin: centre of the mounted visible face (flush with the console face); that face looks -Y, "
             "+Z = device top edge as mounted, X right, body at y >= 0.")
    return c("document.metadata.set", values={
        "part_number": pn, "description": desc + frame, "revision": "A", "project": "desk",
        "com.setsma.desk": {"Material": material, "ReleaseState": "WIP", "Source": source}})


# --- ACC-11 Focusrite Scarlett Solo 3rd Gen -------------------------------------------------------------
def scarlett() -> list[Cmd]:
    d = DEVICES["scarlett"]
    w, h, dep = d.w, d.h, d.d
    body, blk, knob = "Scarlett_Body", "Scarlett_Black", "Scarlett_Knobs"
    cmds = [box("SCAR_Body", body, (-w / 2, w / 2), (0, dep), (-h / 2, h / 2))]
    # front panel, left to right (MEASURE, product photos): XLR combo, inst jack, 2 gain halos, monitor, phones
    jacks = [("XLR", -54.0, 0.0, 22.0, 0.8), ("Inst", -32.0, 0.0, 10.0, 0.8), ("Monitor", 32.0, 2.0, 24.0, 9.0),
             ("Phones", 58.0, -6.0, 10.0, 0.8)]
    # separate bodies seated on the panel faces (touching, no overlap)
    black = [cyl_y(f"SCAR_{n}", blk, x, z, dia, -proud, 0.0) for n, x, z, dia, proud in jacks]
    knobs = [cyl_y(f"SCAR_Gain{i + 1}", knob, x, 4.0, 14.0, -7.0, 0.0) for i, x in enumerate((-12.0, 8.0))]
    # small push buttons (48V, Air) under the gain knobs
    knobs += [box(f"SCAR_Btn{n}", knob, (x - 3.0, x + 3.0), (-1.5, 0.0), (-16.0, -12.5)) for n, x in (("48V", -12.0), ("Air", 8.0))]
    # rear panel: USB-C and RCA L/R (shallow, black)
    black.append(box("SCAR_RearUSBC", blk, (-50.0, -41.0), (dep, dep + 0.6), (-1.6, 1.6)))
    black += [cyl_y(f"SCAR_{n}", blk, x, 0.0, 10.0, dep, dep + 1.0) for n, x in (("RCA_L", 30.0), ("RCA_R", 50.0))]
    cmds += [*merge(blk, black), *merge(knob, knobs)]
    mat = "Al 6063-T5"
    return [*cmds, *finish([body], mat, "#c8102e", AL_PBR), *finish([blk], "ABS", "#141517"),
            *finish([knob], "ABS", "#e9e9e9"),
            meta("ACC-11", f"Focusrite Scarlett Solo 3rd Gen interface, {w:g} x {h:g} face x {dep:g} deep, red "
                 "anodised body, front jacks/knobs proud toward -Y, rear USB-C + RCA toward +Y.", mat,
                 "MEASURE: envelope ~144 x 44 x 96 (Focusrite spec); front/rear detail positions estimated from "
                 "product photos")]


# --- ACC-12 ABFCRTTW 7-port USB hub ----------------------------------------------------------------------
def hub() -> list[Cmd]:
    d = DEVICES["hub"]
    w, h, dep = d.w, d.h, d.d
    body, blk = "Hub_Body", "Hub_PortsCable"
    pitch, recess, port_d = 18.0, 1.0, 7.0  # port pitch, port insert recess, port opening depth (USB-C plug 6.5)
    ports = [(-3 * pitch + i * pitch, "A" if i < 4 else "C") for i in range(7)]
    size = {"A": (13.0, 5.0), "C": (9.0, 3.2)}
    cmds = [box("HUB_Body", body, (-w / 2, w / 2), (0, dep), (-h / 2, h / 2))]
    for i, (x, kind) in enumerate(ports):
        pw, ph = size[kind]
        cmds.append(box(f"HUB_Port{i + 1}_{kind}", body, (x - pw / 2, x + pw / 2), (-EPS, port_d), (-ph / 2, ph / 2), "cut"))
    inside = [box(f"HUB_PortInside{i + 1}", blk, (x - size[k][0] / 2, x + size[k][0] / 2), (recess, port_d),
                  (-size[k][1] / 2, size[k][1] / 2)) for i, (x, k) in enumerate(ports)
              if x != HUB_FP_PORT_X]  # the fingerprint dongle's plug fills that port (ACC-15)
    inside.append(cyl("HUB_Cable", blk, "X", [-w / 2 - 12.0, dep * 0.75, 0.0], 3.0, 12.0))  # stub stays inside the bay cable cavity
    cmds += merge(blk, inside)
    mat = "Al 6063-T5"
    return [*cmds, *finish([body], mat, "#6e7378", AL_PBR), *finish([blk], "ABS", "#141517"),
            meta("ACC-12", f"ABFCRTTW 7-port USB 3.0 hub, {w:g} x {h:g} port face x {dep:g} deep, 4 USB-A then 3 USB-C "
                 "along +X in the -Y face, captive cable d3 x 12 stub out of the -X end (back half).", mat,
                 "MEASURE: envelope from listings (130 x 30 x 17); port pitch and cable exit estimated")]


# --- ACC-13 iPhone 16 Pro Max in a case, landscape --------------------------------------------------------
def phone() -> list[Cmd]:
    d = DEVICES["phone"]
    w, h, dep = d.w, d.h, d.d
    case, scr = "iPhone_Case", "iPhone_Screen"
    r_case, r_scr, lip, scr_t = 10.0, 8.0, 4.0, 1.0  # case corner R, screen corner R, case lip, glass thickness
    sw, sh = w - 2 * lip, h - 2 * lip
    inset = 1.0  # glass face below the case lip
    bump = (36.0, 76.0, -7.0, 33.0)  # camera plateau x0, x1, z0, z1: upper left seen from the back = +X, +Z
    cmds = [
        box("IPH_Case", case, (-w / 2, w / 2), (0, dep), (-h / 2, h / 2)),
        c("solid.fillet", name="IPH_CaseCorners", radius=mm(r_case), body=case,
          edges=[[sx * w / 2, dep / 2, sz * h / 2] for sx in (-1, 1) for sz in (-1, 1)]),
        box("IPH_ScreenPocket", case, (-sw / 2, sw / 2), (-EPS, inset + scr_t), (-sh / 2, sh / 2), "cut"),
        box("IPH_Screen", scr, (-sw / 2, sw / 2), (inset, inset + scr_t), (-sh / 2, sh / 2)),
        c("solid.fillet", name="IPH_ScreenCorners", radius=mm(r_scr), body=scr,
          edges=[[sx * sw / 2, inset + scr_t / 2, sz * sh / 2] for sx in (-1, 1) for sz in (-1, 1)]),
        box("IPH_CameraBump", case, (bump[0], bump[1]), (dep - EPS, dep + 1.5), (bump[2], bump[3]), "join"),
    ]
    return [*cmds, *finish([case], "PC", "#1c1c1e"), *finish([scr], "PC", "#0a0a0c", GLASS_PBR),
            meta("ACC-13", f"Apple iPhone 16 Pro Max in a case, landscape, {w:g} x {h:g} x {dep:g} (case), screen "
                 "toward -Y inset 1 mm, camera plateau 1.5 mm proud on the back (+Y) at +X/+Z.", "PC",
                 "MEASURE: phone 163 x 77.6 x 8.25 (Apple spec) + case estimate; camera plateau estimated")]


# --- ACC-14 Apple MagSafe Charger ---------------------------------------------------------------------------
def magsafe() -> list[Cmd]:
    d = DEVICES["magsafe"]
    dia, t, face_t = 55.5, 4.5, 0.8
    if dia > d.w or t > d.d:
        raise ValueError("MagSafe puck larger than its pocket in ACC_layout.DEVICES")
    face, rim, cable = "MagSafe_Face", "MagSafe_Body", "MagSafe_Cable"
    cmds = [
        cyl_y("MAG_Face", face, 0.0, 0.0, dia, 0.0, face_t),
        cyl_y("MAG_Body", rim, 0.0, 0.0, dia, face_t, t),
        # cable: own body, touching the rim (a join on the curved rim failed: "boolean Union: implausible result volume")
        cyl("MAG_Cable", cable, "Z", [0.0, face_t + (t - face_t) / 2, -dia / 2 - 20.0], 3.0, 20.0),
    ]
    return [*cmds, *finish([face, cable], "PC", "#e8e8ea"), *finish([rim], "Al 6063-T5", "#c0c0c4", AL_PBR),
            meta("ACC-14", f"Apple MagSafe Charger 25 W puck d{dia:g} x {t:g}, charging face toward -Y, aluminium "
                 "back, cable d3 x 20 radially out of the bottom (-Z).", "Al 6063-T5",
                 "Apple spec d55.5 x 4.5 (approx.); cable stub length is a modelling choice")]


# --- ACC-15 USB-C fingerprint dongle -------------------------------------------------------------------------
def fingerprint() -> list[Cmd]:
    d = DEVICES["fingerprint"]
    w, h, dep = d.w, d.h, d.d
    body, sens, plug = "Finger_Body", "Finger_Sensor", "Finger_Plug"
    sd, rec = 9.0, 0.5  # sensor diameter, sensor recess
    pl, pw, pt = 6.5, 8.3, 2.5  # USB-C plug length (+X), width (Z), thickness (Y)
    cmds = [
        box("FPR_Body", body, (-w / 2, w / 2), (0, dep), (-h / 2, h / 2)),
        cyl_y("FPR_SensorRecess", body, 0.0, 0.0, sd + 0.4, -EPS, rec, "cut"),
        cyl_y("FPR_Sensor", sens, 0.0, 0.0, sd, rec - 0.3, rec),
        box("FPR_Plug", plug, (w / 2 - EPS, w / 2 + pl), (dep / 2 - pt / 2, dep / 2 + pt / 2), (-pw / 2, pw / 2)),
    ]
    return [*cmds, *finish([body], "ABS", "#1e1f21"), *finish([sens], "PC", "#3a4a55", GLASS_PBR),
            *finish([plug], "Steel zinc-plated", "#c0c0c4", AL_PBR),
            meta("ACC-15", f"USB-C fingerprint reader dongle, {w:g} x {h:g} x {dep:g}, round sensor d{sd:g} on the -Y "
                 "face, USB-C plug 6.5 out of the +X end.", "ABS",
                 "MEASURE: model unknown; envelope and sensor estimated")]


# --- ACC-16 duckyPad Pro in the user's standard case -----------------------------------------------------------
DPP_DIR = f"{ROOT.as_posix()}/refs/ducky_pad_pro"
# STEP case coords (refs/ducky_pad_pro, from the STL/STEP): outline x -3.5..112.5, y -3.5..99.5, top face z 15.503675.
# The rear edge (STEP +Y = 99.5) holds the USB-C cut-out (x 79..95, z -2.5..8.5) and the two knob holes, so it goes
# to device +Z; the case top looks to device -Y.
DPP_CX, DPP_CY, DPP_TOP = 54.5, 48.0, 15.503675
DPP_MATRIX = [1, 0, 0, -DPP_CX, 0, 0, -1, DPP_TOP, 0, 1, 0, -DPP_CY]  # (x, y, z) -> (x - cx, top - z, y - cy)
DPP_KEYS_X = (10.0, 29.0, 48.0, 67.0)  # switch cut-out centres (14 mm squares in the plate at z 5.25..6.75)
DPP_KEYS_Y = (10.0, 29.0, 48.0, 67.0, 86.0)
DPP_PLATE_TOP = 6.75
DPP_KNOBS = ((101.0, 63.75), (101.0, 87.75))  # encoder holes d16.7 in the top
DPP_BUTTONS = ((84.0, 7.0), (99.5, 7.0))  # button holes d10.4 in the top
DPP_OLED = (77.0, 108.4, 21.3, 54.2)  # OLED opening x0, x1, y0, y1 (opening 76.4..109 x 20.75..54.76)


def dpp(x: float, y: float, z: float) -> tuple[float, float, float]:
    """STEP case coordinates -> device frame."""
    return (x - DPP_CX, DPP_TOP - z, y - DPP_CY)


def dpp_box(name: str, body: str, x: tuple[float, float], y: tuple[float, float], z: tuple[float, float],
            op: str = "new") -> Cmd:
    """A box given in STEP case coordinates, built in the device frame."""
    a, b = dpp(x[0], y[0], z[0]), dpp(x[1], y[1], z[1])
    return box(name, body, *[(min(a[i], b[i]), max(a[i], b[i])) for i in range(3)], op)


def dpp_cyl(name: str, body: str, x: float, y: float, d: float, z0: float, z1: float, op: str = "new") -> Cmd:
    """A cylinder on the case's Z axis (STEP coords) from z0 up to z1: device -Y."""
    return cyl(name, body, "Y", list(dpp(x, y, z1)), d, z1 - z0, op)


def duckypad() -> list[Cmd]:
    d = DEVICES["duckypad"]
    caps, knobs, oled = "DPP_Keycaps", "DPP_KnobsButtons", "DPP_OLED"
    cap, cap_h, cap_lift = 18.0, 8.0, 7.0  # keycap square, height, skirt above the plate top (MEASURE)
    z_cap = DPP_PLATE_TOP + cap_lift
    cmds: list[Cmd] = [
        c("file.insert_step", path=f"{DPP_DIR}/DPP Case - Bottom.step", name="DPP Case Bottom", matrix=DPP_MATRIX),
        c("file.insert_step", path=f"{DPP_DIR}/DPP Case - Top.step", name="DPP Case Top", matrix=DPP_MATRIX),
        c("body.rename", body="Bottom Plate", name="DPP_CaseBottom"),
        c("body.rename", body="Top Plate", name="DPP_CaseTop"),
    ]
    cmds += merge(caps, [dpp_box(f"DPP_Key_{kx:g}_{ky:g}", caps, (kx - cap / 2, kx + cap / 2),
                                 (ky - cap / 2, ky + cap / 2), (z_cap, z_cap + cap_h))
                         for kx in DPP_KEYS_X for ky in DPP_KEYS_Y])
    knob_d, knob_proud, btn_d, btn_proud = 14.0, 12.0, 9.5, 2.5
    pieces = [dpp_cyl(f"DPP_Knob{i + 1}", knobs, x, y, knob_d, DPP_TOP - 1.0, DPP_TOP + knob_proud)
              for i, (x, y) in enumerate(DPP_KNOBS)]
    pieces += [dpp_cyl(f"DPP_Button{i + 1}", knobs, x, y, btn_d, DPP_TOP - 6.0, DPP_TOP + btn_proud)
               for i, (x, y) in enumerate(DPP_BUTTONS)]
    cmds += merge(knobs, pieces)
    x0, x1, y0, y1 = DPP_OLED
    cmds.append(dpp_box("DPP_OLED", oled, (x0, x1), (y0, y1), (6.25, 7.25)))
    case_w, case_h = 116.0, 103.0
    if case_w > d.w or case_h > d.h:
        raise ValueError("duckyPad case larger than its pocket in ACC_layout.DEVICES")
    mat = "ABS"
    return [*cmds, *finish(["DPP_CaseTop", "DPP_CaseBottom"], mat, "#2e3033"), *finish([caps, knobs], "ABS", "#c9cccf"),
            *finish([oled], "PC", "#0d2a55", GLASS_PBR),
            meta("ACC-16", "duckyPad Pro in the user's standard printed case (116 x 103 x 24.7), 20 keycaps 4 x 5 at "
                 "19 mm, 2 knurled knobs (rear right), 2 buttons (front right), OLED; case rear edge (USB-C) at +Z.",
                 mat, "User CAD refs/ducky_pad_pro/DPP Case - Top/Bottom.step (github msetsma/ducky-pad-pro "
                 "case/standard); keycaps, knobs, buttons and OLED are MEASURE estimates; case printed (PLA/PETG, "
                 "ABS as stand-in)")]


# --- ACC-17 KVM key: Cherry MX switch + 1u cap ------------------------------------------------------------------
def kvm() -> list[Cmd]:
    d = DEVICES["kvm"]
    cap, sw = "KVM_Keycap", "KVM_Switch"
    cap_w, cap_top, cap_skirt, wall = 18.0, -11.0, -3.0, 1.2
    top_w, top_h, low_w, low_h = 15.4, 5.0, d.w, 5.0  # MX upper housing (above the plate), lower housing (in the cut)
    cmds = [
        box("KVM_Cap", cap, (-cap_w / 2, cap_w / 2), (cap_top, cap_skirt), (-cap_w / 2, cap_w / 2)),
        c("solid.shell", name="KVM_CapHollow", body=cap, thickness=mm(wall), faces=[[0.0, cap_skirt, 0.0]]),
        box("KVM_HousingTop", sw, (-top_w / 2, top_w / 2), (-top_h, 0.0), (-top_w / 2, top_w / 2)),
        box("KVM_HousingLow", sw, (-low_w / 2, low_w / 2), (-EPS, low_h), (-low_w / 2, low_w / 2), "join"),
    ]
    return [*cmds, *finish([cap], "ABS", "#c9cccf"), *finish([sw], "PC", "#2a2b2d"),
            meta("ACC-17", "KVM key: one Cherry MX switch in a 14 x 14 plate cut + 1u keycap (18 x 18 x 8, top 11 "
                 "proud of the plate, hollow skirt); upper housing 15.4 sq x 5 above the plate, lower 14 sq x 5 below; "
                 "origin = plate top face at the switch centre.", "ABS",
                 "Cherry MX datasheet (approx.); keycap profile simplified to a box; pins omitted")]


SCRIPTS: Mapping[str, Callable[[], list[Cmd]]] = {
    "scarlett": scarlett, "hub": hub, "phone": phone, "magsafe": magsafe,
    "fingerprint": fingerprint, "duckypad": duckypad, "kvm": kvm,
}


def main() -> None:
    for key, fn in SCRIPTS.items():
        out = ROOT / "parts/src" / f"{DEVICES[key].stem}.json"
        cmds = [*TEMPLATE, *fn()]
        out.write_text(json.dumps({"generated_by": GEN, "commands": cmds}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
