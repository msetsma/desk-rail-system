"""Narrow clearance check: changed bodies against only the bodies near them.

    python tools/near_check.py Leg Foot                  # bodies whose names start with these
    python tools/near_check.py PC_Strap --margin 10      # neighbours within 10 mm (bbox)
    python tools/near_check.py HBLFSD5 --print-params    # print the inspect.clearance commands to run
                                                         # in the live app (MCP execute) instead

Neighbours come from bounding boxes in an eval of the design (reused while it's newer than the
design file), so a check covers tens of pairs instead of hundreds. Runs headless with a capped
thread count so it doesn't saturate the machine. Exits non-zero if any pair overlaps.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

__all__ = ["CheckError", "near_pairs", "main"]

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / "desk_rails.solidcraft"
BUILD = ROOT / "build"
CLI = "solidcraft-cli"

Box = tuple[list[float], list[float]]
# Catalog hardware bolted flat onto HFS5 extrusions: the face-to-face contact makes the exact check
# very slow (~25 s per pair on the detailed DXF profile). Their seating is verified at placement
# (skeleton/hw_placements.json), so these pairs are skipped unless --include-mating is given.
MATING = (("HBLFSD5", "HBLFSN5", "HPTTD5", "HPTLD5", "Standoff_M5x12", "M6x20_SHCS"),
          ("Upright_4040", "SideRail_", "Crossbar_2040", "Stile_2040"))


class CheckError(Exception):
    """The eval or the clearance run failed."""


def _cli(args: Sequence[str], threads: int) -> None:
    env = {**os.environ, "RAYON_NUM_THREADS": str(threads)}
    result = subprocess.run([CLI, *args], capture_output=True, text=True, check=False, env=env)
    if result.returncode != 0:
        raise CheckError((result.stderr or result.stdout).strip()[:400])


def _boxes(design: Path, threads: int) -> dict[str, Box]:
    cached = BUILD / f"{design.stem}_near_eval.json"
    if not cached.is_file() or cached.stat().st_mtime < design.stat().st_mtime:
        _cli(["eval", str(design), "--json-out", str(cached)], threads)
    bodies = json.loads(cached.read_text(encoding="utf-8"))["bodies"]
    return {b["name"]: (b["bbox"]["min"], b["bbox"]["max"]) for b in bodies}


def _gap(a: Box, b: Box) -> float:
    """Largest axis separation between two boxes (<= 0 when they touch or overlap)."""
    return max(max(a[0][i] - b[1][i], b[0][i] - a[1][i]) for i in range(3))


def _mating(a: str, b: str) -> bool:
    hw, hosts = MATING
    return (a.startswith(hw) and b.startswith(hosts)) or (b.startswith(hw) and a.startswith(hosts))


def near_pairs(boxes: Mapping[str, Box], prefixes: Sequence[str], margin: float,
               include_mating: bool = False) -> dict[str, list[str]]:
    """Each changed body (name matches a prefix) -> the other bodies within `margin` mm of it."""
    changed = [n for n in boxes if n.startswith(tuple(prefixes))]
    return {c: [n for n in boxes if n not in changed and _gap(boxes[n], boxes[c]) <= margin
                and (include_mating or not _mating(n, c))] for c in changed}


def _commands(pairs: Mapping[str, list[str]], near: float) -> list[dict[str, object]]:
    """One clearance command per changed body, so each is checked only against its own neighbours."""
    return [{"command": "inspect.clearance", "params": {"bodies": [c], "against": against,
                                                        "skip_within": "component", "clearance": near}}
            for c, against in pairs.items() if against]


def _report(result_json: Path) -> int:
    data = json.loads(result_json.read_text(encoding="utf-8"))
    results = data if isinstance(data, list) else data["results"]
    overlaps = checked = 0
    for result in results:
        for o in result["overlaps"]:
            log.error("OVERLAP %s | %s  %.2f mm3", o["a"], o["b"], o["volume_mm3"])
        for n in result.get("near", []):
            log.info("near    %s | %s  %.3f mm", n["a"], n["b"], n["distance_mm"])
        for u in result.get("unchecked", []):
            log.warning("unchecked %s | %s: %s", u.get("a"), u.get("b"), u.get("reason"))
        overlaps += len(result["overlaps"])
        checked += result.get("pairs_checked", 0)
    log.info("%d overlap(s), %d pair(s) checked", overlaps, checked)
    return 1 if overlaps else 0


def main(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("prefixes", nargs="+", help="body-name prefixes of the changed parts")
    parser.add_argument("--design", type=Path, default=DESIGN)
    parser.add_argument("--margin", type=float, default=5.0, help="neighbour bbox margin, mm")
    parser.add_argument("--near", type=float, default=0.5, help="report gaps below this, mm")
    parser.add_argument("--threads", type=int, default=max(2, (os.cpu_count() or 4) // 2))
    parser.add_argument("--include-mating", action="store_true", help="also check hardware vs its extrusion")
    parser.add_argument("--print-params", action="store_true", help="print params for the live app")
    args = parser.parse_args(argv)

    pairs = near_pairs(_boxes(args.design, args.threads), args.prefixes, args.margin, args.include_mating)
    if not pairs:
        log.error("no bodies start with %s", args.prefixes)
        return 2
    commands = _commands(pairs, args.near)
    log.info("%d changed body(ies), %d candidate pair(s)", len(pairs), sum(len(v) for v in pairs.values()))
    if args.print_params:
        sys.stdout.write("\n".join(json.dumps(c) for c in commands) + "\n")
        return 0
    if not commands:
        log.info("no neighbours within %.1f mm", args.margin)
        return 0
    script, out = BUILD / "near_check_cmd.json", BUILD / "near_check.json"
    script.write_text(json.dumps({"commands": commands}), encoding="utf-8")
    _cli(["run", str(script), "--in", str(args.design), "--results", "--json-out", str(out), "--quiet"], args.threads)
    return _report(out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
