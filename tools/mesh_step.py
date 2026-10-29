"""Write triangle meshes to a STEP AP214 file of planar B-rep faces, one named body per mesh.

SolidCraft imports STL/OBJ/3MF/glTF only as mesh bodies, and a design with mesh bodies can't be linked
(`component.insert_design`: "no solid bodies to link") or exported to STEP. A STEP made of planar
triangle faces imports as ordinary (open or closed) B-rep bodies, so a vendor mesh can go through the
normal part pipeline (build -> STEP -> frozen part -> linked insert). Coplanar neighbours are merged by
SolidCraft on import. Every shell is written as one body, so a body may hold disconnected pieces.

    from tools.mesh_step import write_step
    write_step(path, {"Body_Name": (vertices_mm, faces)}, closed={"Body_Name": False}, product="PART")
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import numpy as np

__all__ = ["MeshStepError", "write_step"]

_HEADER = (
    "ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('faceted mesh'),'2;1');\n"
    "FILE_NAME('{name}','',(''),(''),'tools/mesh_step.py','','');\n"
    "FILE_SCHEMA(('AUTOMOTIVE_DESIGN {{ 1 0 10303 214 1 1 1 1 }}'));\nENDSEC;\nDATA;\n"
)
_MIN_AREA2 = 1e-9  # |cross| below this: degenerate triangle, skipped


class MeshStepError(Exception):
    """The meshes can't be written as STEP."""


def _num(x: float) -> str:
    s = f"{x:.4f}".rstrip("0")
    return s + "0" if s.endswith(".") else s


def _vec(p: np.ndarray) -> str:
    return "(" + ",".join(_num(float(c)) for c in p) + ")"


class _Entities:
    """STEP entity list; `add` returns the new entity's #id."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def add(self, text: str) -> int:
        self.lines.append(text)
        return len(self.lines)


def _context(e: _Entities) -> tuple[int, int, int]:
    """Units, representation context, product context and the world placement."""
    length = e.add("( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) )")
    angle = e.add("( NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.) )")
    solid_angle = e.add("( NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT() )")
    unc = e.add(f"UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-04),#{length},'distance_accuracy_value','')")
    ctx = e.add(f"( GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#{unc})) "
                f"GLOBAL_UNIT_ASSIGNED_CONTEXT((#{length},#{angle},#{solid_angle})) REPRESENTATION_CONTEXT('',''))")
    app = e.add("APPLICATION_CONTEXT('automotive design')")
    e.add(f"APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#{app})")
    origin = e.add("CARTESIAN_POINT('',(0.,0.,0.))")
    dz, dx = e.add("DIRECTION('',(0.,0.,1.))"), e.add("DIRECTION('',(1.,0.,0.))")
    world = e.add(f"AXIS2_PLACEMENT_3D('',#{origin},#{dz},#{dx})")
    return ctx, app, world


def _body(e: _Entities, name: str, verts: np.ndarray, faces: np.ndarray, closed: bool) -> int:
    """One shell of planar triangle faces with shared vertices and edges; returns the body entity."""
    vp = [e.add(f"VERTEX_POINT('',#{e.add(f'CARTESIAN_POINT({chr(39) * 2},{_vec(p)})')})") for p in verts]
    edges: dict[tuple[int, int], int] = {}

    def oriented(a: int, b: int) -> int:
        key = (min(a, b), max(a, b))
        if key not in edges:
            pa, pb = verts[key[0]], verts[key[1]]
            d = pb - pa
            ln = float(np.linalg.norm(d))
            cp = e.add(f"CARTESIAN_POINT('',{_vec(pa)})")
            vec = e.add(f"VECTOR('',#{e.add(f'DIRECTION({chr(39) * 2},{_vec(d / ln)})')},{_num(ln)})")
            edges[key] = e.add(f"EDGE_CURVE('',#{vp[key[0]]},#{vp[key[1]]},#{e.add(f'LINE({chr(39) * 2},#{cp},#{vec})')},.T.)")
        return e.add(f"ORIENTED_EDGE('',*,*,#{edges[key]},{'.T.' if a < b else '.F.'})")

    ids = []
    for tri in faces:
        p0, p1, p2 = verts[tri[0]], verts[tri[1]], verts[tri[2]]
        n = np.cross(p1 - p0, p2 - p0)
        if float(np.linalg.norm(n)) < _MIN_AREA2 or np.allclose(p1, p0):
            continue
        n, xd = n / np.linalg.norm(n), (p1 - p0) / np.linalg.norm(p1 - p0)
        place = e.add(f"AXIS2_PLACEMENT_3D('',#{e.add(f'CARTESIAN_POINT({chr(39) * 2},{_vec(p0)})')},"
                      f"#{e.add(f'DIRECTION({chr(39) * 2},{_vec(n)})')},#{e.add(f'DIRECTION({chr(39) * 2},{_vec(xd)})')})")
        plane = e.add(f"PLANE('',#{place})")
        loop = e.add("EDGE_LOOP('',(" + ",".join(f"#{oriented(int(tri[i]), int(tri[(i + 1) % 3]))}" for i in range(3)) + "))")
        ids.append(e.add(f"ADVANCED_FACE('',(#{e.add(f'FACE_OUTER_BOUND({chr(39) * 2},#{loop},.T.)')}),#{plane},.T.)"))
    if not ids:
        raise MeshStepError(f"{name}: no non-degenerate triangles")
    refs = ",".join(f"#{i}" for i in ids)
    if closed:
        return e.add(f"MANIFOLD_SOLID_BREP('{name}',#{e.add(f'CLOSED_SHELL({chr(39) * 2},({refs}))')})")
    return e.add(f"SHELL_BASED_SURFACE_MODEL('{name}',(#{e.add(f'OPEN_SHELL({chr(39) * 2},({refs}))')}))")


def write_step(path: Path | str, meshes: Mapping[str, tuple[np.ndarray, np.ndarray]],
               closed: Mapping[str, bool] | None = None, product: str = "mesh") -> None:
    """Write `meshes` ({body name: (vertices in mm, triangle indices)}) to `path` as one STEP product."""
    e = _Entities()
    ctx, app, world = _context(e)
    bodies = [_body(e, name, np.asarray(v, float), np.asarray(f, int), bool((closed or {}).get(name)))
              for name, (v, f) in meshes.items()]
    rep = e.add(f"ADVANCED_BREP_SHAPE_REPRESENTATION('',(#{world}," + ",".join(f"#{b}" for b in bodies) + f"),#{ctx})")
    pctx = e.add(f"PRODUCT_CONTEXT('',#{app},'mechanical')")
    pdctx = e.add(f"PRODUCT_DEFINITION_CONTEXT('part definition',#{app},'design')")
    prod = e.add(f"PRODUCT('{product}','{product}','',(#{pctx}))")
    pd = e.add(f"PRODUCT_DEFINITION('design','',#{e.add(f'PRODUCT_DEFINITION_FORMATION({chr(39) * 2},{chr(39) * 2},#{prod})')},#{pdctx})")
    e.add(f"SHAPE_DEFINITION_REPRESENTATION(#{e.add(f'PRODUCT_DEFINITION_SHAPE({chr(39) * 2},{chr(39) * 2},#{pd})')},#{rep})")
    out = Path(path)
    with out.open("w", encoding="ascii", newline="\n") as fh:
        fh.write(_HEADER.format(name=out.name))
        fh.writelines(f"#{i}={s};\n" for i, s in enumerate(e.lines, 1))
        fh.write("ENDSEC;\nEND-ISO-10303-21;\n")
