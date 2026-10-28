"""Bodies of the linked assembly from a ``solidcraft-cli eval --json-out`` report.

The eval lists every placed body. Extra placements of a part carry an occurrence path suffix
("Leg (DSK-00 Desk frame:1/DSK-04 Leg:3)") and multi-lump bodies a lump suffix
("PC_FrontSlats (2)"). Each body is mapped back to its part body name, its component occurrence
and that occurrence's placement label from tools/build_assembly.py ("Leg_LB", "HW-07 Gusset side
rail L"), so callers select bodies by stable names instead of parsing legacy body names.

    python tools/eval_bodies.py build/report.json   # list bodies with their labels
"""

from __future__ import annotations

import json
import logging
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from build_assembly import OCCURRENCES, BuildError, component_name, load_hw_occurrences

__all__ = ["Body", "ReportError", "bbox", "load_bodies", "load_params", "main", "occurrence_labels"]

log = logging.getLogger(__name__)

_OCCURRENCE = re.compile(r"^(?P<body>.*) \((?P<path>[^()]*/[^()]*)\)$")
_LUMP = re.compile(r"^(?P<body>.*) \(\d+\)$")
_LEAF = re.compile(r"^(?P<component>.*):(?P<index>\d+)$")

Vec = tuple[float, float, float]


class ReportError(Exception):
    """The eval report is missing or malformed."""


@dataclass(frozen=True)
class Body:
    """One placed body: eval geometry plus where it came from."""

    name: str              # full eval name
    part_body: str         # body name inside its part file (no suffixes)
    component: str | None  # component definition ("DSK-04 Leg"); None for single-placement parts
    index: int             # occurrence number within that component (1 = first placement)
    label: str             # placement label from build_assembly, else part_body
    lo: Vec
    hi: Vec
    com: Vec               # centre of mass (real material, uniform density)
    kg: float
    volume_mm3: float
    material: str

    @property
    def center(self) -> Vec:
        return tuple((a + b) / 2 for a, b in zip(self.lo, self.hi))  # type: ignore[return-value]

    @property
    def size(self) -> Vec:
        return tuple(b - a for a, b in zip(self.lo, self.hi))  # type: ignore[return-value]


def occurrence_labels() -> dict[tuple[str, int], str]:
    """(component definition, occurrence number) -> placement label, in build order."""
    try:
        occurrences = [*OCCURRENCES, *load_hw_occurrences()]
    except BuildError as exc:
        raise ReportError(f"cannot read placements: {exc}") from exc
    counts: dict[str, int] = {}
    labels: dict[tuple[str, int], str] = {}
    for occ in occurrences:
        component = component_name(occ.part)
        counts[component] = counts.get(component, 0) + 1
        labels[(component, counts[component])] = occ.label
    return labels


def _split(name: str) -> tuple[str, str | None, int]:
    match = _OCCURRENCE.match(name)
    body, component, index = name, None, 1
    if match:
        body = match["body"]
        leaf = _LEAF.match(match["path"].split("/")[-1])
        if leaf:
            component, index = leaf["component"], int(leaf["index"])
    lump = _LUMP.match(body)
    return (lump["body"] if lump else body), component, index


def _read(report: Path) -> Mapping[str, object]:
    try:
        return json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportError(f"cannot read eval report {report}: {exc}") from exc


def _vec(raw: object) -> Vec:
    return tuple(float(v) for v in raw)  # type: ignore[union-attr, return-value]


def load_bodies(report: Path) -> list[Body]:
    """Every placed body in the report, labelled with its placement."""
    raw = _read(report)
    labels = occurrence_labels()
    try:
        rows = [(r, *_split(str(r["name"]))) for r in raw["bodies"]]  # type: ignore[union-attr]
        # First placements have no occurrence suffix: take the component from a sibling that has one.
        owner = {part: comp for _, part, comp, _ in rows if comp is not None}
        return [
            Body(str(r["name"]), part, comp or owner.get(part), index,
                 labels.get((comp or owner.get(part, ""), index), part),
                 _vec(r["bbox"]["min"]), _vec(r["bbox"]["max"]), _vec(r["center_of_mass"]),
                 float(r.get("mass_g", 0.0)) / 1000, float(r.get("volume_mm3", 0.0)),
                 str(r.get("material", "")))
            for r, part, comp, index in rows
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise ReportError(f"unexpected body record in {report}: {exc}") from exc


def load_params(report: Path) -> dict[str, float]:
    """User parameter values (mm / rad) from the report."""
    try:
        return {str(p["name"]): float(p["value"]) for p in _read(report)["params"]}  # type: ignore[union-attr]
    except (KeyError, TypeError, ValueError) as exc:
        raise ReportError(f"unexpected parameter record in {report}: {exc}") from exc


def bbox(bodies: Iterable[Body]) -> tuple[Vec, Vec]:
    """Union bounding box of several bodies."""
    items = list(bodies)
    if not items:
        raise ReportError("bounding box of no bodies")
    lo = tuple(min(b.lo[i] for b in items) for i in range(3))
    hi = tuple(max(b.hi[i] for b in items) for i in range(3))
    return lo, hi  # type: ignore[return-value]


def main(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(argv) != 2:
        log.error(__doc__)
        return 2
    try:
        bodies = load_bodies(Path(argv[1]))
    except ReportError as exc:
        log.error("%s", exc)
        return 1
    for b in bodies:
        log.info("%-24s %-28s %-20s %7.3f kg", b.label, b.part_body, b.material, b.kg)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
