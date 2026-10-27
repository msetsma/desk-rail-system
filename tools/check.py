"""One command: report, overlap check, audit, BOM (and optional renders) on desk_rails.solidcraft.

    python tools/check.py            # checks + BOM
    python tools/check.py --renders  # also refresh renders/*.png

The saved design file is the source of truth; nothing is regenerated or overwritten.
Exits non-zero if the report fails or any bodies overlap.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import audit
import bom

__all__ = ["CheckError", "main"]

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
DESIGN = ROOT / "desk_rails.solidcraft"
REPORT = BUILD / "report.json"
VIEWS = ("iso", "front", "back", "right", "top")
NEAR_MM, TOUCH_MM = 10.0, 0.01
# Designed gaps, not warnings: speaker bracket parts, panel on standoffs past the plates,
# mouse resting on the pad.
EXPECTED_NEAR = (("Speaker_", "SpkMount_"), ("SpkMount_", "Upright_"), ("ModestyPanel", "Plate_Bar"),
                 ("Plate_SideRail", "Standoff_Post"), ("Mouse_", "Desktop"))


class CheckError(Exception):
    """A build or check step failed."""


def _cli(*args: str) -> None:
    cmd = ["solidcraft-cli", *args]
    log.info("$ %s", " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=ROOT, check=True)
    except subprocess.CalledProcessError as exc:
        raise CheckError(f"solidcraft-cli failed: {' '.join(args[:2])}") from exc


def report() -> None:
    """Body report (bboxes, masses) from the saved design via an empty command run."""
    script = BUILD / "report_cmd.json"
    script.write_text(json.dumps({"commands": []}), encoding="utf-8")
    _cli("run", str(script), "--in", str(DESIGN), "--quiet", "--json-out", str(REPORT))


def interference() -> list[tuple[str, str]]:
    script, out = BUILD / "interference_cmd.json", BUILD / "interference.json"
    script.write_text(json.dumps({"commands": [{"command": "inspect.interference",
                                                "params": {"budget_s": 600}}]}), encoding="utf-8")
    _cli("run", str(script), "--in", str(DESIGN), "--results", "--quiet", "--json-out", str(out))
    result = json.loads(out.read_text())[0]
    if result.get("unchecked"):
        log.warning("interference: %d pairs not checked", len(result["unchecked"]))
    return [(i["a"], i["b"]) for i in result["interferences"]]


def near_misses(gap_mm: float = NEAR_MM) -> list[tuple[str, str, float]]:
    """Pairs closer than ``gap_mm`` but not touching (touching = bolted joints, expected)."""
    script, out = BUILD / "clearance_cmd.json", BUILD / "clearance.json"
    script.write_text(json.dumps({"commands": [{"command": "inspect.clearance",
                                                "params": {"clearance": gap_mm}}]}), encoding="utf-8")
    _cli("run", str(script), "--in", str(DESIGN), "--results", "--quiet", "--json-out", str(out))
    near = json.loads(out.read_text())[0].get("near", [])
    return [(n["a"], n["b"], n["distance_mm"]) for n in near
            if n["distance_mm"] > TOUCH_MM and not _expected(n["a"], n["b"])]


def _expected(a: str, b: str) -> bool:
    return any((a.startswith(p) and b.startswith(q)) or (a.startswith(q) and b.startswith(p))
               for p, q in EXPECTED_NEAR)


def renders() -> None:
    for view in VIEWS:
        _cli("snapshot", "--in", str(DESIGN), "--out", f"renders/{view}.png", "--view", view)


def main(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    BUILD.mkdir(exist_ok=True)
    try:
        report()
        overlaps = interference()
        close = near_misses()
    except CheckError as exc:
        log.error("%s", exc)
        return 1
    bodies = json.loads(REPORT.read_text())["body_count"]
    log.info("checked %d bodies; overlaps: %d", bodies, len(overlaps))
    for a, b in overlaps:
        log.error("  OVERLAP %s <-> %s", a, b)
    for a, b, d in close:
        log.warning("  NEAR %s <-> %s: %.1f mm", a, b, d)
    audit.main(["audit", str(REPORT)])
    bom.main(["bom", str(REPORT)])
    if "--renders" in argv:
        renders()
    return 1 if overlaps else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
