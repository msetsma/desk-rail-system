"""Convert the Sketchfab Insta360 Link 2 glTF into the faceted STEP that MON-03 imports.

    python parts/src/MON-03_convert.py          # then: python parts/src/MON-03_gen.py; python tools/regen_parts.py MON-03

Source: "Insta360 Link 2 4K AI Webcam" by bswlife, CC BY 4.0 (refs/insta360_link2pro/sketchfab_bswlife/,
git-ignored, downloaded by the user). The Link 2 Pro has the same outer size (71.3 x 58.9 x 38 mm), so the Link 2
mesh stands in for it (refs/insta360_link2pro/README.md).

Pipeline:
1. Load the glTF (arbitrary units, Y up, camera faces +Z). Nodes are grouped per finish into bodies; decals
   (logo, label quads) are dropped.
2. Scale: one uniform factor fitting the official camera height (gimbal base bottom to head top = 58.9 mm).
   Width and depth then land within ~5 % of spec (summary JSON); the factor is an estimate (MEASURE).
3. The vendor mesh has the magnetic clip folded into its desk-stand pose. The rear leg is swung about its hinge
   until it rests on the back of the M32U top edge (m32u_slab_t, read from MON-01_gen.py), so the part sits
   clipped on the main monitor.
4. Turned into the desk frame, reduced by vertex clustering (GRID_MM; quadric decimation tore the shells open
   along the glTF's UV seams) and written with tools/mesh_step.py.

Local frame: X right (pan axis at 0), camera faces -Y, Z up. Origin = where the clip meets the monitor: the
inside face of the front lip (monitor front face, Y = 0) on the clip's underside (monitor top edge, Z = 0).

Needs: pip install trimesh scipy networkx.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.mesh_step import write_step

__all__ = ["ConvertError", "convert", "main"]

log = logging.getLogger("MON-03_convert")

REFS = ROOT / "refs/insta360_link2pro"
GLTF = REFS / "sketchfab_bswlife/scene.gltf"
OUT_DIR = REFS / "converted"
STEP = OUT_DIR / "MON-03_link2.step"
SUMMARY = OUT_DIR / "MON-03_link2.json"
MON01_GEN = ROOT / "parts/src/MON-01_gen.py"

CAM_H_MM = 58.9  # official Link 2 / Link 2 Pro height (Insta360 spec FAQ), gimbal base bottom to head top
SPEC_MM = {"w": 71.3, "h": 58.9, "d": 38.0}
GRID_MM = 0.7  # vertex-clustering cell: ~19k triangles (~3 s linked insert); 0.4 doubles it for little gain
MIN_HEIGHT = 0.01  # mm: thinner triangles are dropped (STEP export limit, see CHR-01_convert)

# glTF node -> body. Nodes not listed are dropped: decals (logo / label quads) and the six perforated grille
# sheets on the head top (Object_14..19, 330k triangles, flush with the head shell).
BODIES: Mapping[str, Sequence[str]] = {
    "Webcam_Body": ["Object_4", "Object_6", "Object_8", "Object_10", "Object_21", "Object_22", "Object_23", "Object_25",
                    "Object_39", "Object_41", "Object_42", "Object_44", "Object_46"],
    "Webcam_Lens": ["Object_12", "Object_54"],
    "Webcam_Mount": ["Object_27", "Object_29", "Object_31", "Object_33", "Object_35", "Object_37"],
}
BASE = "Object_39"  # gimbal base: its bottom is the camera's bottom, its x centre the pan axis
HEAD = ["Object_21", "Object_22"]
LENS = "Object_12"
CLIP_PLATE = "Object_37"  # thin sheet under the clip top: its underside rests on the monitor top edge
CLIP_FRAME = "Object_27"  # clip top with the front lip
REAR_LEG = ["Object_29", "Object_35"]
HINGE = "Object_33"  # rear hinge barrel, axis along x


class ConvertError(Exception):
    """The source mesh can't be converted."""


def slab_t_mm() -> float:
    """m32u_slab_t from MON-01_gen.py (single source for the monitor top-edge thickness)."""
    m = re.search(r'\("m32u_slab_t",\s*"([\d.]+) mm"', MON01_GEN.read_text(encoding="utf-8"))
    if not m:
        raise ConvertError(f"m32u_slab_t not found in {MON01_GEN}")
    return float(m.group(1))


def load_nodes(path: Path) -> dict[str, trimesh.Trimesh]:
    """Every scene node as a world-space mesh (source units)."""
    if not path.exists():
        raise ConvertError(f"{path} missing: unzip the Sketchfab download there (refs/insta360_link2pro/README.md)")
    scene = trimesh.load(path, force="scene")
    nodes = {}
    for node in scene.graph.nodes_geometry:
        tf, name = scene.graph[node]
        mesh = scene.geometry[name].copy()
        mesh.apply_transform(tf)
        nodes[node] = mesh
    wanted = {n for names in BODIES.values() for n in names}
    missing = wanted - nodes.keys()
    if missing:
        raise ConvertError(f"glTF nodes missing: {sorted(missing)}")
    return nodes


def _rot_x(mesh: trimesh.Trimesh, angle: float, y0: float, z0: float) -> trimesh.Trimesh:
    """Rotate about the x-parallel axis through (y0, z0); positive turns +y toward +z and +z toward -y."""
    out = mesh.copy()
    out.apply_transform(trimesh.transformations.rotation_matrix(angle, [1, 0, 0], [0, y0, z0]))
    return out


def unfold_leg(nodes: Mapping[str, trimesh.Trimesh], back_z: float) -> tuple[dict[str, trimesh.Trimesh], float]:
    """Swing the rear leg down about its hinge until its front-most point reaches back_z (monitor back face)."""
    lo, hi = nodes[HINGE].bounds
    y0, z0 = (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2
    leg = trimesh.util.concatenate([nodes[n] for n in REAR_LEG])
    for step in range(1800):
        angle = np.radians(step * 0.05)  # downward: the folded leg's free end (+z) swings toward -y
        if _rot_x(leg, angle, y0, z0).bounds[1][2] <= back_z:
            return {n: _rot_x(nodes[n], angle, y0, z0) for n in REAR_LEG}, float(np.degrees(angle))
    raise ConvertError("rear leg never reaches the monitor back face")


def _cluster(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Vertex clustering on a GRID_MM grid (mesh in mm): each cell's vertices merge to their mean, collapsed and
    repeated triangles go. Unlike quadric decimation it never opens the glTF's UV seams, so shells stay whole."""
    keys = np.round(mesh.vertices / GRID_MM).astype(np.int64)
    _, cell = np.unique(keys, axis=0, return_inverse=True)
    cell = cell.ravel()
    verts = np.zeros((cell.max() + 1, 3))
    np.add.at(verts, cell, mesh.vertices)
    verts /= np.bincount(cell)[:, None]
    faces = cell[mesh.faces]
    faces = faces[(faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 0] != faces[:, 2])]
    _, first = np.unique(np.sort(faces, axis=1), axis=0, return_index=True)
    out = trimesh.Trimesh(vertices=verts, faces=faces[np.sort(first)], process=False)
    out.remove_unreferenced_vertices()
    return out


def _clean(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Drop slivers thinner than MIN_HEIGHT mm (STEP export limit); mesh must already be in mm."""
    mesh = mesh.copy()
    mesh.update_faces(mesh.nondegenerate_faces(height=MIN_HEIGHT))
    mesh.remove_unreferenced_vertices()
    return mesh


def to_local(mesh: trimesh.Trimesh, origin: Sequence[float], scale: float) -> trimesh.Trimesh:
    """Source (x, y up, z front) -> desk part frame (X right, Y back, Z up) in mm, about the clip datum."""
    v = (mesh.vertices - np.asarray(origin)) * scale
    local = np.column_stack([v[:, 0], -v[:, 2], v[:, 1]])
    return trimesh.Trimesh(vertices=local, faces=mesh.faces, process=False)  # -z flip + swap keeps handedness


def _bounds(meshes: Iterable[trimesh.Trimesh]) -> np.ndarray:
    pts = np.vstack([m.bounds for m in meshes])
    return np.array([pts.min(axis=0), pts.max(axis=0)])


def datum(nodes: Mapping[str, trimesh.Trimesh]) -> tuple[list[float], float, float]:
    """Clip datum (source units) and the scale (mm per unit); also the lip's inner-face z."""
    base_lo, base_hi = nodes[BASE].bounds
    head_top = _bounds(nodes[n] for n in HEAD)[1][1]
    scale = CAM_H_MM / (head_top - base_lo[1])
    frame = nodes[CLIP_FRAME].vertices
    lip = frame[(frame[:, 1] < nodes[CLIP_PLATE].bounds[0][1] - 0.01) & (frame[:, 2] > 0.1)]
    if not len(lip):
        raise ConvertError("front lip of the clip not found")
    lip_z = float(lip[:, 2].min())
    origin = [(base_lo[0] + base_hi[0]) / 2, float(nodes[CLIP_PLATE].bounds[0][1]), lip_z]
    return origin, float(scale), lip_z


def build_bodies(nodes: Mapping[str, trimesh.Trimesh]) -> tuple[dict[str, trimesh.Trimesh], dict[str, object]]:
    origin, scale, lip_z = datum(nodes)
    legs, leg_deg = unfold_leg(nodes, lip_z - slab_t_mm() / scale)
    placed = {**nodes, **legs}
    bodies = {}
    for body, names in BODIES.items():
        parts = [_clean(_cluster(to_local(placed[n], origin, scale))) for n in names]
        bodies[body] = trimesh.util.concatenate(parts)  # pieces stay unwelded (mesh_step: no 3-face edges)
    camera = _bounds([bodies["Webcam_Body"], bodies["Webcam_Lens"]])
    lens = to_local(placed[LENS], origin, scale)
    ref = {
        "scale_mm_per_unit": round(scale, 3),
        "rear_leg_unfold_deg": round(leg_deg, 2),
        "slab_t_mm": slab_t_mm(),
        "camera_bbox_mm": camera.round(2).tolist(),
        "camera_size_mm": {"w": round(float(np.ptp(camera[:, 0])), 2), "h": round(float(np.ptp(camera[:, 2])), 2),
                           "d": round(float(np.ptp(camera[:, 1])), 2)},
        "spec_mm": SPEC_MM,
        "lens_centre_mm": np.round(lens.bounds.mean(axis=0), 2).tolist(),
        "lens_axis": [0, -1, 0],
        "overall_bbox_mm": _bounds(bodies.values()).round(2).tolist(),
    }
    return bodies, ref


def convert(gltf: Path = GLTF, step: Path = STEP, summary: Path = SUMMARY) -> dict[str, object]:
    bodies, ref = build_bodies(load_nodes(gltf))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    closed = {n: bool(m.is_watertight) for n, m in bodies.items()}
    write_step(step, {n: (m.vertices, m.faces) for n, m in bodies.items()}, closed, product="MON-03_link2")
    info = {
        "source": "https://sketchfab.com/3d-models/insta360-link-2-4k-ai-webcam-b6e5aa185a95459a923acabaf4e48005",
        "credit": "Insta360 Link 2 4K AI Webcam by bswlife, CC BY 4.0",
        "step": step.relative_to(ROOT).as_posix(),
        "step_sha256": hashlib.sha256(step.read_bytes()).hexdigest(),
        "triangles": sum(len(m.faces) for m in bodies.values()),
        "bodies": {n: {"triangles": len(m.faces), "closed": closed[n]} for n, m in bodies.items()},
        "reference": ref,
    }
    summary.write_text(json.dumps(info, indent=1), encoding="utf-8")
    return info


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        info = convert()
    except ConvertError as exc:
        log.error("MON-03 convert failed: %s", exc)
        return 1
    log.info("wrote %s (%d triangles)\n%s", info["step"], info["triangles"], json.dumps(info["reference"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
