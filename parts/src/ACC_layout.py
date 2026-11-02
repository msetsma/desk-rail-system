"""Shared layout of the lower-crossbar console (ACC-00): one source of truth for the bays and devices.

Console frame (every bay part uses it as its local frame, and is placed at
x = con_x, y = stile_front, z = desk_h + bar1_z + rail_l/2 + con_top):
    origin = the console top line on the lower crossbar's front face, at the console centre x;
    +X right, +Y toward the wall (into the bar), +Z up.

The front face is one plane raked RAKE back from vertical. A point on it is given by (x, s): s runs down the
face from the top-front edge. `face_frame()` gives the face point and the face axes, so pockets are built as
plain boxes in a "face frame" (x, depth into the console, up the face) and turned into place.

Device local frame (every purchased device part, ACC-11..17): origin = centre of the face you see when it is
mounted, that face looks toward -Y, +Z = the device's top edge (up the console face once mounted), X right.
`device_mount()` gives each device's face point, so the assembly can place it with the console tilt.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "RAKE_DEG", "D_TOP", "HEIGHT", "WIDTH", "FACE_LEN", "SEAM_GAP", "BAY_EDGES", "Bay", "BAYS", "Device", "DEVICES",
    "face_point", "inward", "up_face", "device_mount", "TAIL_Y", "INLAY_S", "INLAY_W", "INLAY_D", "GROOVE_S",
]

RAKE_DEG = 20.0  # face lean back from vertical, toward the seated eye (24 deg below level)
D_TOP = 60.0  # console depth at the top line (bar front face to the top-front edge)
HEIGHT = 124.0  # top line to console bottom (z)
WIDTH = 594.0
SEAM_GAP = 0.5  # each bay stops this far short of a shared edge: a 1 mm seam line between bays
BAY_EDGES = (-297.0, -127.0, 53.0, 153.0, 297.0)
TAIL_Y = 12.0  # audio bay tail under the bar reaches this far behind the bar front face (bar back is +20)
GROOVE_S = 10.6  # parting-line groove centre (s): level with the bar top when con_top = 10
INLAY_S, INLAY_W, INLAY_D = 124.0, 3.0, 1.5  # light grey inlay line: centre s, width, depth

_SIN, _COS = math.sin(math.radians(RAKE_DEG)), math.cos(math.radians(RAKE_DEG))
FACE_LEN = HEIGHT / _COS  # face length along s


def face_point(x: float, s: float) -> tuple[float, float, float]:
    """Console-frame point on the front face, s mm down from the top-front edge."""
    return (x, -D_TOP - s * _SIN, -s * _COS)


def inward() -> tuple[float, float, float]:
    """Unit normal into the console (away from the user)."""
    return (0.0, _COS, -_SIN)


def up_face() -> tuple[float, float, float]:
    """Unit vector up the face (toward the top line)."""
    return (0.0, _SIN, _COS)


@dataclass(frozen=True)
class Bay:
    """One printed bay: part number, stem, x range in the console frame, devices it holds."""

    pn: str
    stem: str
    x0: float
    x1: float
    holds: str


BAYS = (
    Bay("ACC-02", "ACC-02_Bay_Audio", BAY_EDGES[0], BAY_EDGES[1] - SEAM_GAP, "Scarlett Solo + USB hub"),
    Bay("ACC-03", "ACC-03_Bay_Phone", BAY_EDGES[1] + SEAM_GAP, BAY_EDGES[2] - SEAM_GAP, "iPhone StandBy + MagSafe"),
    Bay("ACC-04", "ACC-04_Bay_Control", BAY_EDGES[2] + SEAM_GAP, BAY_EDGES[3] - SEAM_GAP, "KVM key + fingerprint reader"),
    Bay("ACC-05", "ACC-05_Bay_duckyPad", BAY_EDGES[3] + SEAM_GAP, BAY_EDGES[4], "duckyPad Pro"),
)


@dataclass(frozen=True)
class Device:
    """A purchased device set flush in the face: pocket centre (x, s), size along x / along s, depth."""

    pn: str
    stem: str
    x: float
    s: float
    w: float  # along X
    h: float  # along the face (s)
    d: float  # depth into the console
    note: str


DEVICES = {
    "hub": Device("ACC-12", "ACC-12_USBHub_ABFCRTTW", -212.0, 27.0, 130.0, 30.0, 17.0,
                  "ABFCRTTW 7-port USB 3.0, 130 x 30 x 17 (listings), ports face out"),
    "scarlett": Device("ACC-11", "ACC-11_ScarlettSolo3", -212.0, 82.0, 144.0, 44.0, 96.0,
                       "Focusrite Scarlett Solo 3rd Gen, ~144 x 96 x 44, MEASURE"),
    "phone": Device("ACC-13", "ACC-13_iPhone16ProMax", -37.0, 62.0, 168.0, 82.0, 12.0,
                    "iPhone 16 Pro Max in a case, landscape, ~168 x 82 x 12, MEASURE the case"),
    "magsafe": Device("ACC-14", "ACC-14_MagSafeCharger", -37.0, 62.0, 55.8, 55.8, 4.6,
                      "Apple MagSafe Charger 25 W, d55.5 x 4.5, behind the phone (face at the phone pocket floor)"),
    "kvm": Device("ACC-17", "ACC-17_KVMKey", 75.0, 68.0, 14.0, 14.0, 1.5,
                  "MX switch in a 14 x 14 cut through a 1.5 mm plate, light grey 1u cap"),
    "fingerprint": Device("ACC-15", "ACC-15_FingerprintDongle", 110.0, 68.0, 30.0, 15.0, 7.0,
                          "USB-C fingerprint dongle, ~30 x 15 x 7, MEASURE"),
    "duckypad": Device("ACC-16", "ACC-16_duckyPadPro", 225.0, 61.8, 116.6, 103.6, 25.0,
                       "duckyPad Pro in the user's standard case, 116 x 103 x 25 (+0.3 clearance per side)"),
}


def device_mount(key: str, depth: float = 0.0) -> tuple[float, float, float]:
    """Console-frame position of a device's local origin: its pocket centre on the face, pushed `depth` in.

    The MagSafe puck sits at the phone pocket floor, so it is mounted at depth = phone depth."""
    dev = DEVICES[key]
    px, py, pz = face_point(dev.x, dev.s)
    _, ny, nz = inward()
    return (px, py + depth * ny, pz + depth * nz)
