"""Bill of materials from the assembly's part-number metadata (``assembly.bom``).

Runs ``assembly.bom`` headless on desk_rails.solidcraft (read only, nothing is saved): one call
for the group components under the root, then one per group. Each row is a part number with its
count, description and revision from the part file and the Material property set in the
assembly. Adds end-machining notes for the extrusions and a slot-fastener estimate from the
catalog bolt counts per part number. Writes BOM.md. Rule and decision IDs refer to
docs/EXTRUSION_GUIDE.md.

    python tools/bom.py                       # BOM.md from desk_rails.solidcraft
    python tools/bom.py path/to/design.solidcraft
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

__all__ = ["BomError", "BomRow", "Group", "main", "query", "render"]

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
DESIGN = ROOT / "desk_rails.solidcraft"
OUT = ROOT / "BOM.md"
CLI = "solidcraft-cli"
SPARE_TNUTS_PER_MEMBER = 2  # F2: preload spares in every member you might use later

# End machining per extrusion part number (D8: end anchors need tapped ends + access holes).
MACHINING: Mapping[str, str] = {
    "FRM-01": "access holes for the crossbar and side-rail / speaker-arm anchors (M2)",
    "FRM-02": "both ends tapped M5 for end anchors (M1, D8)",
    "FRM-03L": "rear end tapped M5 (M1, D8)",
    "FRM-03R": "rear end tapped M5 (M1, D8)",
    "FRM-04": "both ends tapped M5 for end anchors into the crossbar slots (M1, D7)",
}
# (bolts into T-nuts, other screws) per piece. Misumi counts from the catalog
# (refs/misumi_brackets/p2259.pdf); the -SET suffix ships them with each part.
FASTENERS: Mapping[str, tuple[int, int]] = {
    "HBLFSN5": (2, 0),             # 1 bolt per leg
    "HPTTD5": (8, 0),              # 8 x M5
    "HPTLD5": (8, 0),              # 8 x M5
    "Standoff M5x12 d10": (1, 1),  # into a T-nut, + 1 screw through the panel
    "MON-01": (2, 4),              # VESA adapter: 2 into the stile T-nuts, 4 M4 into the monitor
    "MON-02": (2, 4),
    "SPK-02": (2, 0),              # flange: 2 into the upright front slot
}
END_ANCHORS: Mapping[str, int] = {"FRM-02": 2, "FRM-04": 2, "FRM-03L": 1, "FRM-03R": 1}


class BomError(Exception):
    """The BOM query failed or returned something unexpected."""


@dataclass(frozen=True)
class BomRow:
    part_number: str
    description: str
    revision: str
    material: str
    count: int


@dataclass(frozen=True)
class Group:
    part_number: str
    name: str
    rows: tuple[BomRow, ...]

    @property
    def items(self) -> int:
        return sum(r.count for r in self.rows)


def _cmd(**params: object) -> dict[str, object]:
    return {"command": "assembly.bom", "params": params}


def _run_bom(design: Path, commands: Sequence[dict[str, object]], tag: str) -> list[Mapping[str, object]]:
    script, out = BUILD / f"bom_{tag}_cmd.json", BUILD / f"bom_{tag}.json"
    script.write_text(json.dumps({"commands": list(commands)}), encoding="utf-8")
    cmd = [CLI, "run", str(script), "--in", str(design), "--results", "--quiet", "--json-out", str(out)]
    log.info("$ %s", " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)
        return json.loads(out.read_text(encoding="utf-8"))
    except subprocess.CalledProcessError as exc:
        raise BomError(f"solidcraft-cli failed: {exc.stderr.strip() or exc.stdout.strip()}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise BomError(f"cannot read {out}: {exc}") from exc


def _short(description: str) -> str:
    """First clause of a part description (drops the origin / frame notes)."""
    text = description.split(" Origin:")[0]
    for sep in ("; ", ": "):
        text = text.split(sep)[0]
    return text.strip().rstrip(".").replace("|", "/")


def _row(raw: Mapping[str, object]) -> BomRow:
    props = raw.get("properties") or {}
    return BomRow(str(raw["part_number"]), _short(str(raw.get("description", ""))),
                  str(raw.get("revision", "")), str(props.get("Material", "")),  # type: ignore[union-attr]
                  int(raw["count"]))  # type: ignore[arg-type]


def query(design: Path = DESIGN) -> list[Group]:
    """Group components under the root, each with its flat part-number rows."""
    BUILD.mkdir(exist_ok=True)
    try:
        top = _run_bom(design, [_cmd(levels="top")], "top")[0]["rows"]
        groups = [(str(r["part_number"]), str(r["definition"])) for r in top]  # type: ignore[union-attr]
        results = _run_bom(design, [_cmd(component=name) for _, name in groups], "groups")
        return [Group(pn, name, tuple(_row(r) for r in res["rows"]))  # type: ignore[union-attr]
                for (pn, name), res in zip(groups, results, strict=True)]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise BomError(f"unexpected assembly.bom result: {exc}") from exc


def _group_table(group: Group) -> list[str]:
    lines = [f"## {group.name}", "", "| Qty | Part number | Description | Material | Rev | Notes |",
             "|---|---|---|---|---|---|"]
    lines += [f"| {r.count} | {r.part_number} | {r.description} | {r.material} | {r.revision} "
              f"| {MACHINING.get(r.part_number, '')} |" for r in group.rows]
    return [*lines, ""]


def _fastener_table(counts: Mapping[str, int]) -> list[str]:
    slot = sum(FASTENERS[pn][0] * n for pn, n in counts.items() if pn in FASTENERS)
    other = sum(FASTENERS[pn][1] * n for pn, n in counts.items() if pn in FASTENERS)
    members = sum(n for pn, n in counts.items() if pn in MACHINING)
    anchors = sum(END_ANCHORS.get(pn, 0) * n for pn, n in counts.items())
    return ["## Slot fasteners (estimate)", "",
            "Not modelled; counts from the catalog per placed part.", "", "| Qty | Item |", "|---|---|",
            f"| {slot} | M5 bolt + T-nut pairs into slots (resin-coated / locking nuts, F4; 6.8 N*m, F3) |",
            (f"| {SPARE_TNUTS_PER_MEMBER * members} | spare pre-assembly T-nuts, "
             f"{SPARE_TNUTS_PER_MEMBER} per member (F2) |"),
            f"| {anchors} | end anchors / end-tap screws (D8) |",
            f"| {other} | other screws (VESA M4, panel) |", ""]


def render(groups: Sequence[Group]) -> str:
    rows = [r for g in groups for r in g.rows]
    counts: dict[str, int] = {}
    for r in rows:
        counts[r.part_number] = counts.get(r.part_number, 0) + r.count
    lines = ["# Bill of materials", "",
             ("Generated by `tools/bom.py` from the part-number metadata in `desk_rails.solidcraft` "
              "(`assembly.bom`). Do not hand-edit; rebuild."), "",
             f"{len(rows)} part numbers, {sum(counts.values())} items.", "",
             "| Group | Part numbers | Items |", "|---|---|---|"]
    lines += [f"| {g.name} | {len(g.rows)} | {g.items} |" for g in groups if g.rows]
    lines.append("")
    for group in groups:
        if group.rows:
            lines += _group_table(group)
    return "\n".join(lines + _fastener_table(counts))


def main(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(argv) > 2:
        log.error(__doc__)
        return 2
    design = Path(argv[1]) if len(argv) == 2 else DESIGN
    try:
        groups = query(design)
    except BomError as exc:
        log.error("bom: %s", exc)
        return 1
    OUT.write_text(render(groups), encoding="utf-8")
    log.info("wrote %s (%d part numbers, %d items)", OUT, sum(len(g.rows) for g in groups),
             sum(g.items for g in groups))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
