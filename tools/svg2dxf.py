"""Convert closed SVG profile paths (lines + circular arcs) to an R12 DXF of LINE/ARC entities.

The profile is scaled so its outer bounding box matches ``--size`` (mm), centered on the origin,
with SVG's downward Y flipped to DXF's upward Y. Only path commands M/L/H/V/A/Z (absolute and
relative) are supported, which covers Inkscape exports of extrusion cross-sections.
"""

from __future__ import annotations

import argparse
import logging
import math
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Arc", "Line", "parse_path", "convert"]

log = logging.getLogger(__name__)

SVG_NS = "{http://www.w3.org/2000/svg}"
TOKEN = re.compile(r"[MmLlHhVvAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


class SvgPathError(ValueError):
    """Raised for path data this converter does not support."""


@dataclass(frozen=True)
class Line:
    start: tuple[float, float]
    end: tuple[float, float]


@dataclass(frozen=True)
class Arc:
    start: tuple[float, float]
    end: tuple[float, float]
    radius: float
    large: bool
    sweep: bool


Segment = Line | Arc


def _numbers(tokens: list[str], i: int, count: int) -> tuple[list[float], int]:
    vals = [float(t) for t in tokens[i : i + count]]
    if len(vals) != count:
        raise SvgPathError("truncated path data")
    return vals, i + count


def parse_path(d: str) -> list[Segment]:
    """Parse SVG path data into absolute line/arc segments."""
    tokens = TOKEN.findall(d)
    segs: list[Segment] = []
    i, cmd = 0, ""
    cur = start = (0.0, 0.0)
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                if cur != start:
                    segs.append(Line(cur, start))
                cur = start
                continue
        rel = cmd.islower()
        c = cmd.upper()
        if c in "ML":
            (x, y), i = _numbers(tokens, i, 2)
            nxt = (cur[0] + x, cur[1] + y) if rel else (x, y)
            if c == "M":
                start = nxt
                cmd = "l" if rel else "L"
            else:
                segs.append(Line(cur, nxt))
            cur = nxt
        elif c == "H":
            (x,), i = _numbers(tokens, i, 1)
            nxt = (cur[0] + x if rel else x, cur[1])
            segs.append(Line(cur, nxt))
            cur = nxt
        elif c == "V":
            (y,), i = _numbers(tokens, i, 1)
            nxt = (cur[0], cur[1] + y if rel else y)
            segs.append(Line(cur, nxt))
            cur = nxt
        elif c == "A":
            (rx, ry, _rot, large, sweep, x, y), i = _numbers(tokens, i, 7)
            if not math.isclose(rx, ry, rel_tol=1e-6):
                raise SvgPathError("elliptical arcs are not supported")
            nxt = (cur[0] + x, cur[1] + y) if rel else (x, y)
            segs.append(Arc(cur, nxt, rx, bool(large), bool(sweep)))
            cur = nxt
        else:
            raise SvgPathError(f"unsupported path command {cmd!r}")
    return segs


def _profile_paths(svg: Path) -> Iterator[str]:
    """Yield path data of drawn (non-defs) paths."""
    root = ET.parse(svg).getroot()
    defs = {id(e) for d in root.iter(f"{SVG_NS}defs") for e in d.iter()}
    for el in root.iter(f"{SVG_NS}path"):
        if id(el) not in defs:
            yield el.attrib["d"]


def _arc_center(a: Arc) -> tuple[float, float]:
    """Center of an SVG endpoint arc (SVG coordinates, Y down)."""
    (x1, y1), (x2, y2), r = a.start, a.end, a.radius
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    d2 = dx * dx + dy * dy
    h = math.sqrt(max(r * r / d2 - 1.0, 0.0))
    sign = -1.0 if a.large == a.sweep else 1.0
    return mx + sign * h * dy, my - sign * h * dx


def _bbox(segs: Sequence[Segment]) -> tuple[float, float, float, float]:
    pts = [p for s in segs for p in (s.start, s.end)]
    for s in segs:
        if isinstance(s, Arc):
            cx, cy = _arc_center(s)
            pts += [(cx - s.radius, cy), (cx + s.radius, cy), (cx, cy - s.radius), (cx, cy + s.radius)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _dxf_entities(segs: Sequence[Segment], scale: float, cx: float, cy: float) -> Iterator[str]:
    def tf(p: tuple[float, float]) -> tuple[float, float]:
        return (p[0] - cx) * scale, -(p[1] - cy) * scale

    for s in segs:
        if isinstance(s, Line):
            (x1, y1), (x2, y2) = tf(s.start), tf(s.end)
            if math.hypot(x2 - x1, y2 - y1) < 1e-9:
                continue
            yield f"0\nLINE\n8\n0\n10\n{x1:.6f}\n20\n{y1:.6f}\n30\n0\n11\n{x2:.6f}\n21\n{y2:.6f}\n31\n0\n"
        else:
            ccx, ccy = tf(_arc_center(s))
            (sx, sy), (ex, ey) = tf(s.start), tf(s.end)
            a0 = math.degrees(math.atan2(sy - ccy, sx - ccx))
            a1 = math.degrees(math.atan2(ey - ccy, ex - ccx))
            # SVG sweep=1 is clockwise on screen; after the Y flip it is counter-clockwise.
            if not s.sweep:
                a0, a1 = a1, a0
            yield (
                f"0\nARC\n8\n0\n10\n{ccx:.6f}\n20\n{ccy:.6f}\n30\n0\n40\n{s.radius * scale:.6f}\n"
                f"50\n{a0 % 360:.6f}\n51\n{a1 % 360:.6f}\n"
            )


def convert(svg: Path, out: Path, size: float) -> tuple[float, float]:
    """Write ``out`` from ``svg``; return the profile's final (width, height) in mm."""
    segs = [seg for d in _profile_paths(svg) for seg in parse_path(d)]
    if not segs:
        raise SvgPathError(f"no drawable paths in {svg}")
    x0, y0, x1, y1 = _bbox(segs)
    scale = size / max(x1 - x0, y1 - y0)
    body = "".join(_dxf_entities(segs, scale, (x0 + x1) / 2, (y0 + y1) / 2))
    header = "0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n"
    out.write_text(f"{header}0\nSECTION\n2\nENTITIES\n{body}0\nENDSEC\n0\nEOF\n", encoding="ascii")
    log.info("wrote %s: %d segments, scale %.6f", out, len(segs), scale)
    return (x1 - x0) * scale, (y1 - y0) * scale


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("svg", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--size", type=float, required=True, help="outer size of the profile's larger side, mm")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    w, h = convert(args.svg, args.out, args.size)
    log.info("profile %.3f x %.3f mm", w, h)


if __name__ == "__main__":
    main()
