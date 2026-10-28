"""Generate the ErgoDox EZ build scripts (INP-03 left, INP-04 right) into parts/src/.

Geometry sources (refs/ergodox_ez/README.md):
- case outline: ZSA 1:1 printable PDF -> ergodox_ez_left.dxf (right = its mirror, written here)
- key centres, sizes and thumb angle: keys_left.json, extracted from the same PDF's vector paths
- SA keycap heights per row: Signature Plastics nominal values (MEASURE, secondary sources)

Origin (kept from Rev A): DXF origin = front-left corner of the outline bbox, bottom face; +Y toward
the wall, Z up. The right half mirrors the left about x = OUTLINE_W / 2, so its bbox is identical.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

__all__ = ["build", "main"]

ROOT = Path("C:/Users/2015m/DEV/CAD/desk")
REFS = ROOT / "refs/ergodox_ez"
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
SKEL = {"command": "parameters.import", "params": {"path": f"{ROOT.as_posix()}/skeleton/params.json"}}

OUTLINE_W = 202.2584  # DXF x extent (kb_w = 202.26 mm)
PITCH = 19.05  # 1u
CAP_GAP = 0.85  # 1u cap footprint = 18.2 mm
CAP_R = 3.0  # cap corner radius at the base (> kb_cap_inset so the tapered top stays valid)
SW = 14.0  # MX switch housing top, square
BOTTOM_ROW_Y = 66.0  # keys below this (non-thumb) are the bottom modifier row

MATERIAL = "ABS"
COLOR_CASE = "#eeeeea"  # ZSA white case
COLOR_SWITCH = "#2b2b2b"  # switch housings (dark)
COLOR_CAPS = "#cdcdc8"  # light grey SA keycaps

# name, expression, comment
LOCAL_PARAMS = [
    ("kb_sw_h", "6 mm", "MEASURE: switch housing exposed between plate (case top) and SA cap skirt"),
    ("kb_chamfer", "1 mm", "Case top edge chamfer"),
    ("kb_cap_inset", "2.75 mm", "SA cap top inset per side (18.2 base -> 12.7 top)"),
    ("sa_r1", "16.5 mm", "MEASURE: SA row 1 (number row) cap height, SP nominal 0.65 in"),
    ("sa_r2", "13.7 mm", "MEASURE: SA row 2 (QWERT) cap height, est."),
    ("sa_r3", "11.9 mm", "MEASURE: SA row 3 (home row + thumbs) cap height, SP nominal 0.47 in"),
    ("sa_r4", "13.2 mm", "MEASURE: SA row 4 (ZXCV + bottom row) cap height, est."),
]


@dataclass(frozen=True)
class Key:
    x: float
    y: float
    w: float  # along the key's local x (cap footprint, mm)
    d: float  # along the key's local y
    ang: float  # deg, about Z
    row: str  # sa_r1..sa_r4


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def _cap_size(drawn: float) -> float:
    units = round(drawn / PITCH * 2) / 2
    return units * PITCH - CAP_GAP


def load_keys() -> list[Key]:
    raw = json.loads((REFS / "keys_left.json").read_text(encoding="utf-8"))
    main = [k for k in raw if k["ang"] == 0 and k["c"][1] >= BOTTOM_ROW_Y]
    cols: dict[float, list[dict]] = {}
    for k in main:
        cols.setdefault(round(k["c"][0], 0), []).append(k)
    row_of: dict[tuple[float, float], str] = {}
    for col in cols.values():
        col.sort(key=lambda k: -k["c"][1])
        names = ["sa_r1", "sa_r2", "sa_r4"] if len(col) == 3 else ["sa_r1", "sa_r2", "sa_r3", "sa_r4"]
        for k, name in zip(col, names):
            row_of[tuple(k["c"])] = name
    keys = []
    for k in raw:
        if k["ang"] != 0:
            row = "sa_r3"
        elif k["c"][1] < BOTTOM_ROW_Y:
            row = "sa_r4"
        else:
            row = row_of[tuple(k["c"])]
        keys.append(Key(k["c"][0], k["c"][1], _cap_size(k["foot"][0]), _cap_size(k["foot"][1]), k["ang"], row))
    return keys


def mirror_keys(keys: Sequence[Key]) -> list[Key]:
    return [Key(OUTLINE_W - k.x, k.y, k.w, k.d, -k.ang, k.row) for k in keys]


def write_mirrored_dxf(src: Path, dst: Path) -> None:
    lines = src.read_text(encoding="ascii").split("\n")
    out = list(lines)
    for i in range(len(lines) - 1):
        if lines[i].strip() in ("10", "11"):
            out[i + 1] = f"{OUTLINE_W - float(lines[i + 1]):.4f}"
    dst.write_text("\n".join(out), encoding="ascii")


def _plane(ang: float) -> object:
    if ang == 0:
        return "XY"
    a = math.radians(ang)
    return {"origin": [0, 0, 0], "x_dir": [math.cos(a), math.sin(a), 0], "y_dir": [-math.sin(a), math.cos(a), 0]}


def _local(k: Key) -> tuple[float, float]:
    a = math.radians(k.ang)
    return k.x * math.cos(a) + k.y * math.sin(a), -k.x * math.sin(a) + k.y * math.cos(a)


def _rect(u: float, v: float, w: float, d: float, radius: float | None) -> dict:
    p0 = [round(u - w / 2, 4), round(v - d / 2, 4)]
    p1 = [round(u + w / 2, 4), round(v + d / 2, 4)]
    if radius is None:
        return c("sketch.rectangle.two_point", p0=p0, p1=p1)
    return c("sketch.rectangle.rounded", p0=p0, p1=p1, radius=radius)


def _pieces(body: str, count: int) -> list[str]:
    """A new extrude of n disjoint profiles makes n bodies: body, body (2) .. body (n)."""
    return [body] + [f"{body} ({i})" for i in range(2, count + 1)]


def _merge(body: str, count: int) -> list[dict]:
    if count < 2:
        return []
    return [c("solid.combine", target=body, tools=_pieces(body, count)[1:], operation="join")]


def _sketch(name: str, ang: float, rects: list[dict]) -> list[dict]:
    return [c("sketch.create", plane=_plane(ang), name=name), *rects, c("sketch.finish")]


def case_cmds(side: str, dxf: Path) -> list[dict]:
    sk = f"Sketch_{side}_Outline"
    body = f"Keyboard_{side}_Case"
    return [
        c("sketch.create", plane="XY", name=sk),
        c("sketch.insert_dxf", path=dxf.as_posix()),
        c("sketch.finish"),
        c("solid.extrude", sketch=sk, distance="kb_case_h - kb_chamfer", operation="new",
          name=f"Extrude_{side}_Case", body_name=body),
        c("solid.extrude", sketch=sk, start_offset="kb_case_h - kb_chamfer", distance="kb_chamfer",
          taper="-45 deg", operation="join", targets=[body], name=f"Extrude_{side}_CaseChamfer"),
    ]


def switch_cmds(side: str, keys: Sequence[Key]) -> list[dict]:
    """New bodies per sketch plane, then one combine (a join of disjoint pieces warns)."""
    body = f"Keyboard_{side}_Switches"
    cmds: list[dict] = []
    pieces: list[str] = []
    for ang in sorted({k.ang for k in keys}, key=abs):
        tag = "Main" if ang == 0 else "Thumb"
        sk = f"Sketch_{side}_Switches_{tag}"
        rects = [_rect(*_local(k), SW, SW, None) for k in keys if k.ang == ang]
        name = body if not pieces else f"{body}_{tag}"
        cmds += _sketch(sk, ang, rects)
        cmds.append(c("solid.extrude", sketch=sk, start_offset="kb_case_h", distance="kb_sw_h",
                      operation="new", name=f"Extrude_{side}_Switches_{tag}", body_name=name))
        pieces += _pieces(name, len(rects))
    return cmds + [c("solid.combine", target=body, tools=pieces[1:], operation="join")]


def cap_groups(keys: Sequence[Key]) -> list[tuple[str, float, str]]:
    """(row, angle, tag) per keycap body: one body per SA row height (and thumb plane)."""
    return [(row, ang, row.upper().replace("SA_", "") + ("" if ang == 0 else "_Thumb"))
            for row, ang in sorted({(k.row, k.ang) for k in keys})]


def cap_cmds(side: str, keys: Sequence[Key]) -> list[dict]:
    """One body per row group: joining all tapered caps into one body costs ~20 s of booleans."""
    cmds: list[dict] = []
    for row, ang, tag in cap_groups(keys):
        sk = f"Sketch_{side}_Caps_{tag}"
        rects = [_rect(*_local(k), k.w, k.d, CAP_R) for k in keys if k.row == row and k.ang == ang]
        cmds += _sketch(sk, ang, rects)
        cmds.append(c("solid.extrude", sketch=sk, start_offset="kb_case_h + kb_sw_h", distance=row,
                      taper=f"-atan(kb_cap_inset / {row})", operation="new",
                      name=f"Extrude_{side}_Caps_{tag}", body_name=f"Keyboard_{side}_Keycaps_{tag}"))
        cmds += _merge(f"Keyboard_{side}_Keycaps_{tag}", len(rects))
    return cmds


def finish_cmds(side: str, pn: str, dxf: Path, keys: Sequence[Key]) -> list[dict]:
    case, sw = f"Keyboard_{side}_Case", f"Keyboard_{side}_Switches"
    caps = [f"Keyboard_{side}_Keycaps_{tag}" for _, _, tag in cap_groups(keys)]
    half = "left" if side == "L" else "right (mirror of left)"
    return [
        c("material.assign", bodies=[case, sw, *caps], material=MATERIAL),
        c("appearance.assign", bodies=[case], color=COLOR_CASE),
        c("appearance.assign", bodies=[sw], color=COLOR_SWITCH),
        c("appearance.assign", bodies=caps, color=COLOR_CAPS),
        c("document.metadata.set", values={
            "part_number": pn,
            "description": (
                f"ZSA ErgoDox EZ {half}, white case, light grey SA keycaps (38 keys, flat/untented). "
                "Bodies: case (outline extrude, 1 mm top chamfer), switch housings, keycaps per SA row "
                "(tapered rounded blocks: R1, R2, R3, R3_Thumb, R4). Origin: DXF origin = front-left corner "
                "of the outline bbox on the bottom face; +Y toward wall, Z up"
            ),
            "revision": "A",
            "project": "desk",
            "com.setsma.desk": {
                "Material": MATERIAL,
                "ReleaseState": "WIP",
                "Source": (
                    f"ZSA 1:1 PDF refs/ergodox_ez/1-1-ergodox.pdf: outline {dxf.name}, key layout "
                    "keys_left.json; SA heights SP nominal (MEASURE)"
                ),
            },
        }),
    ]


def build(side: str, pn: str, dxf: Path, keys: Sequence[Key]) -> list[dict]:
    params = [c("parameters.add", name=n, expression=e, comment=m) for n, e, m in LOCAL_PARAMS]
    return [*TEMPLATE, SKEL, *params, *case_cmds(side, dxf), *switch_cmds(side, keys),
            *cap_cmds(side, keys), *finish_cmds(side, pn, dxf, keys)]


def _write(fname: str, cmds: list[dict]) -> None:
    out = ROOT / "parts/src" / f"{fname}.json"
    out.write_text(json.dumps({"commands": cmds}, indent=1), encoding="utf-8")


def main() -> None:
    left_dxf = REFS / "ergodox_ez_left.dxf"
    right_dxf = REFS / "ergodox_ez_right_mirror.dxf"
    write_mirrored_dxf(left_dxf, right_dxf)
    keys = load_keys()
    _write("INP-03_ErgoDoxEZ_Left", build("L", "INP-03", left_dxf, keys))
    _write("INP-04_ErgoDoxEZ_Right", build("R", "INP-04", right_dxf, mirror_keys(keys)))


if __name__ == "__main__":
    main()
