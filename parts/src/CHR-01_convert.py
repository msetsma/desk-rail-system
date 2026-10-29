"""Convert the Herman Miller Mirra 2 3D DWG into the faceted STEP that CHR-01 imports.

    python parts/src/CHR-01_convert.py          # then: python parts/src/CHR-01_gen.py; python tools/regen_parts.py CHR

Pipeline (refs/herman_miller_mirra2/README.md):
1. LibreDWG `dwg2dxf` (free, https://github.com/LibreDWG/libredwg/releases): raw/*_3D.dwg (R2004) -> DXF.
   The DWG holds ~34k 3DFACEs on one layer per part group (SEAT-FRAME, SEAT-BASE ...), in inches.
2. ezdxf + trimesh: faces per layer, inches -> mm, turned so the chair faces +Y (the DWG faces +X), origin
   already on the floor at the gas-cylinder axis. Layers and connected pieces are grouped per finish.
3. User settings baked in: arm pads raised to the top of their travel (posts stretched above ARM_CUT_Z)
   and slid fully back. Seat height stays parametric in the part (`chr_seat_h`, a move of the upper group).
4. Decimated (fast-simplification) to keep the frozen part quick to insert, then written with
   tools/mesh_step.py as planar-face B-rep bodies. A summary JSON next to it carries reference heights.

Needs: pip install ezdxf trimesh scipy networkx fast-simplification. DWG2DXF env var overrides the tool path.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import ezdxf
import fast_simplification
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.mesh_step import write_step

__all__ = ["Body", "ConvertError", "convert", "group_bodies", "load_layers", "main"]

log = logging.getLogger(__name__)

REFS = ROOT / "refs/herman_miller_mirra2"
DWG = REFS / "raw/HMI_Mirra_2_Chair_Suspension_Back_Adjustable_Arms_3D.dwg"
OUT_DIR = REFS / "converted"
DXF = OUT_DIR / "mirra2_3d.dxf"
STEP = OUT_DIR / "CHR-01_mirra2.step"
SUMMARY = OUT_DIR / "CHR-01_mirra2.json"
DWG2DXF = os.environ.get("DWG2DXF", "C:/Users/2015m/cad_tools/libredwg/x/dwg2dxf.exe")

IN_MM = 25.4
ARM_H_MAX = 200.0  # arm pad top above the seat: user 2026-10-29, arms all the way up sit about level with the desk frame (584-635 mm, seat at 406), which matches the vendor model (199.7); the spec says up to 11.5 in
ARM_DEPTH = 2.0 * IN_MM  # spec: pads slide 2 in front to back
ARM_DEPTH_BACK = ARM_DEPTH / 2  # MEASURE: the vendor model's pads are assumed mid-travel
ARM_X = 160.0  # SEAT-FRAME pieces wholly outboard of this are the arms
ARM_CUT_Z = 590.0  # arm posts are vertical from ~580 mm to the pad plate: stretch above this
JUNK_TRIS = 2  # pieces this small (slivers, stray faces) are dropped, except in triangle-soup layers
DECIMATE_ABOVE = 100  # pieces with more triangles are decimated to DECIMATE_KEEP of them
DECIMATE_KEEP = 1.0  # full vendor resolution (user 2026-10-29: 0.3 / 1500 cap looked too rough)
DECIMATE_MAX = 10**9  # no cap
MIN_HEIGHT = 0.01  # mm: thinner triangles are dropped
NO_DECIMATE = frozenset({"Chair_Base"})  # triangle soup (unshared vertices): nothing to collapse


class ConvertError(Exception):
    """The vendor DWG can't be converted."""


@dataclass(frozen=True)
class Body:
    """A finished body: name and the layer pieces it takes."""

    name: str
    pieces: tuple[trimesh.Trimesh, ...]

    def mesh(self, reduce: Callable[[trimesh.Trimesh], trimesh.Trimesh]) -> trimesh.Trimesh:
        """Pieces reduced one by one and kept apart: welding pieces that touch (seat fabric on its trim)
        makes edges with 3+ faces, which SolidCraft imports but then can't export to STEP."""
        return trimesh.util.concatenate([reduce(p) for p in self.pieces])


def dwg_to_dxf(dwg: Path = DWG, dxf: Path = DXF) -> Path:
    if dxf.is_file() and dxf.stat().st_mtime >= dwg.stat().st_mtime:
        return dxf
    dxf.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([DWG2DXF, "-y", "-o", str(dxf), str(dwg)], capture_output=True, text=True, check=False)
    if result.returncode != 0 or not dxf.is_file():
        raise ConvertError(f"dwg2dxf failed: {(result.stderr or result.stdout)[-400:]}")
    return dxf


def load_layers(dxf: Path) -> dict[str, trimesh.Trimesh]:
    """3DFACEs per layer as welded meshes in the part frame (mm, chair faces +Y)."""
    tris: dict[str, list[np.ndarray]] = {}
    for e in ezdxf.readfile(dxf).modelspace().query("3DFACE"):
        v = np.array([e.dxf.vtx0, e.dxf.vtx1, e.dxf.vtx2, e.dxf.vtx3], float)
        layer = tris.setdefault(e.dxf.layer, [])
        layer.append(v[[0, 1, 2]])
        if np.linalg.norm(v[3] - v[2]) > 1e-9:  # a quad, not a triangle with vtx3 == vtx2
            layer.append(v[[0, 2, 3]])
    out = {}
    for name, t in tris.items():
        a = np.array(t) * IN_MM
        a = np.stack([-a[..., 1], a[..., 0], a[..., 2]], -1)  # +90 deg about Z: DWG +X (front) -> +Y
        m = trimesh.Trimesh(vertices=a.reshape(-1, 3), faces=np.arange(a.shape[0] * 3).reshape(-1, 3))
        m.merge_vertices(digits_vertex=3)
        m.update_faces(m.nondegenerate_faces(height=1e-6))
        m.remove_unreferenced_vertices()
        out[name] = m
    return out


def _pieces(m: trimesh.Trimesh, keep_small: bool = False) -> list[trimesh.Trimesh]:
    return [p for p in m.split(only_watertight=False) if keep_small or len(p.faces) > JUNK_TRIS]


def _by(pieces: Sequence[trimesh.Trimesh], test: Callable[[trimesh.Trimesh], bool]) -> list[trimesh.Trimesh]:
    return [p for p in pieces if test(p)]


def _casters(layer: trimesh.Trimesh) -> list[Body]:
    """Five casters: each wheel (the watertight pieces) with the stem pieces nearest to it."""
    pieces = _pieces(layer)
    wheels = sorted((p for p in pieces if p.is_watertight and len(p.faces) > 100),
                    key=lambda p: np.arctan2(p.centroid[1], p.centroid[0]) % (2 * np.pi))
    if len(wheels) != 5:
        raise ConvertError(f"expected 5 caster wheels, found {len(wheels)}")
    groups: list[list[trimesh.Trimesh]] = [[w] for w in wheels]
    for p in pieces:
        if any(p is w for w in wheels):
            continue
        d = [np.linalg.norm(p.centroid[:2] - w.centroid[:2]) for w in wheels]
        groups[int(np.argmin(d))].append(p)
    return [Body(f"Chair_Caster_{i + 1}", tuple(g)) for i, g in enumerate(groups)]


def _stretch(m: trimesh.Trimesh, cut_z: float, dz: float) -> trimesh.Trimesh:
    v = m.vertices.copy()
    v[v[:, 2] > cut_z, 2] += dz
    return trimesh.Trimesh(vertices=v, faces=m.faces.copy(), process=False)


def _shift(m: trimesh.Trimesh, d: Sequence[float]) -> trimesh.Trimesh:
    return trimesh.Trimesh(vertices=m.vertices + np.asarray(d, float), faces=m.faces.copy(), process=False)


def seat_top(layers: Mapping[str, trimesh.Trimesh]) -> float:
    """Seat reference height: the top of the seat suspension (SEAT-FABRIC)."""
    return float(layers["SEAT-FABRIC"].bounds[1][2])


def group_bodies(layers: Mapping[str, trimesh.Trimesh]) -> tuple[list[Body], dict[str, float]]:
    """Group layer pieces into finish bodies and apply the arm settings; returns bodies and reference values."""
    seat_z = seat_top(layers)
    frame = _pieces(layers["SEAT-FRAME"])
    pads = _pieces(layers["SEAT-ARMPAD"], keep_small=True)
    pad_top = float(layers["SEAT-ARMPAD"].bounds[1][2])
    dz = seat_z + ARM_H_MAX - pad_top
    base = _pieces(layers["SEAT-BASE"], keep_small=True)  # the 5-star base is triangle soup
    tube = _by(base, lambda p: p.bounds[1][2] < 230 and np.abs(p.bounds[:, :2]).max() < 30 and len(p.faces) > 50)
    if len(tube) != 1:
        raise ConvertError(f"expected one gas-cylinder tube in SEAT-BASE, found {len(tube)}")

    def is_arm(p: trimesh.Trimesh, side: float) -> bool:
        return p.bounds[0][0] > ARM_X if side > 0 else p.bounds[1][0] < -ARM_X

    def arm(side: float) -> list[trimesh.Trimesh]:
        return [_stretch(p, ARM_CUT_Z, dz) for p in frame if is_arm(p, side)]

    def pad(side: float) -> list[trimesh.Trimesh]:
        return [_shift(p, (0, -ARM_DEPTH_BACK, dz)) for p in pads if side * p.centroid[0] > 0]

    upper = [p for p in base if p.bounds[0][2] > 300]
    lower = [p for p in base if p.bounds[0][2] <= 300 and not any(p is t for t in tube)]
    white = [p for p in frame if not (is_arm(p, 1) or is_arm(p, -1))]
    bodies = [
        Body("Chair_Frame", tuple(white + _pieces(layers["SEAT-BACK"]) + _pieces(layers["SEAT-ADJBACKSUPPORT"])
                                  + _pieces(layers["SEAT-ADJBACKLUMBAR"]))),
        Body("Chair_BackFabric", tuple(_pieces(layers["SEAT-BACKFABRIC"]))),
        Body("Chair_Seat", tuple(_pieces(layers["SEAT-FABRIC"]) + _pieces(layers["SEAT-FABRICTRIM"]))),
        Body("Chair_Arm_R", tuple(arm(1))),
        Body("Chair_Arm_L", tuple(arm(-1))),
        Body("Chair_ArmPad_R", tuple(pad(1))),
        Body("Chair_ArmPad_L", tuple(pad(-1))),
        Body("Chair_Mechanism", tuple(upper)),
        Body("Chair_Controls", tuple(_pieces(layers["SEAT-KNOBS"]) + _pieces(layers["SEAT-LUMBARKNOBS"]))),
        Body("Chair_GasRod", tuple(_pieces(layers["SEAT-SHAFT"]))),
        Body("Chair_Cylinder", tuple(tube)),
        Body("Chair_Base", tuple(lower)),
        *_casters(layers["SEAT-CASTER"]),
    ]
    ref = {"seat_top_mm": round(seat_z, 2), "arm_pad_top_above_seat_mm": round(ARM_H_MAX, 2),
           "arm_raise_mm": round(dz, 2), "arm_back_mm": round(ARM_DEPTH_BACK, 2),
           "vendor_arm_pad_top_above_seat_mm": round(pad_top - seat_z, 2)}
    return bodies, ref


def _decimate(m: trimesh.Trimesh) -> trimesh.Trimesh:
    if len(m.faces) <= DECIMATE_ABOVE:
        return _clean(m)
    v, f = fast_simplification.simplify(m.vertices.astype(np.float32), m.faces.astype(np.int32),
                                        target_count=int(min(DECIMATE_KEEP * len(m.faces), DECIMATE_MAX)))
    return _clean(trimesh.Trimesh(vertices=v.astype(float), faces=f, process=True))


def _clean(m: trimesh.Trimesh) -> trimesh.Trimesh:
    """Drop slivers: SolidCraft's STEP export can't write faces thinner than ~MIN_HEIGHT."""
    m = m.copy()
    m.update_faces(m.nondegenerate_faces(height=MIN_HEIGHT))
    m.remove_unreferenced_vertices()
    return m


def convert(dwg: Path = DWG, step: Path = STEP, summary: Path = SUMMARY) -> dict[str, object]:
    layers = load_layers(dwg_to_dxf(dwg))
    bodies, ref = group_bodies(layers)
    meshes = {b.name: b.mesh(_clean if b.name in NO_DECIMATE else _decimate) for b in bodies}
    closed = {name: bool(m.is_watertight) for name, m in meshes.items()}
    write_step(step, {n: (m.vertices, m.faces) for n, m in meshes.items()}, closed, product="CHR-01_mirra2")
    info = {
        "source": dwg.relative_to(ROOT).as_posix(),
        "step": step.relative_to(ROOT).as_posix(),
        "step_sha256": hashlib.sha256(step.read_bytes()).hexdigest(),
        "triangles_source": int(sum(len(m.faces) for m in layers.values())),
        "triangles": int(sum(len(m.faces) for m in meshes.values())),
        "reference": ref,
        "bodies": {n: {"triangles": len(m.faces), "closed": closed[n],
                       "bbox": np.round(m.bounds, 1).tolist()} for n, m in meshes.items()},
    }
    summary.write_text(json.dumps(info, indent=1), encoding="utf-8")
    return info


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("ezdxf").setLevel(logging.WARNING)
    try:
        info = convert()
    except ConvertError as exc:
        log.error("%s", exc)
        return 1
    log.info("%s: %d -> %d triangles, %.1f MB", info["step"], info["triangles_source"], info["triangles"],
             STEP.stat().st_size / 1e6)
    return 0


if __name__ == "__main__":
    sys.exit(main())
