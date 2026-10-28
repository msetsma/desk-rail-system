"""Parameter sweep: rebuild the parts and the assembly for several skeleton variants, in parallel.

    python tools/sweep.py                    # default cases into build/sweep/
    python tools/sweep.py --cases cases.json # {"name": {"param": "expression", ...}, ...}

Each case builds its own frozen parts from the scripts with its own skeleton, so cases run side by side and the
repo's parts and skeleton are never touched. A case passes when every part rebuilds and the
assembly has no timeline errors or warnings. Exits non-zero if any case fails.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import build_assembly
import regen_parts

__all__ = ["CaseResult", "DEFAULT_CASES", "run_case", "main"]

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "sweep"
CLI = "solidcraft-cli"
DEFAULT_CASES: Mapping[str, Mapping[str, str]] = {
    "wide_78in": {"desk_w": "78 in"},
    "narrow_70in_deep_30in": {"desk_w": "70 in", "desk_d": "30 in"},
    "standing_45in": {"desk_h": "45 in"},
}


@dataclass(frozen=True)
class CaseResult:
    """Outcome of one sweep case."""

    name: str
    errors: tuple[str, ...]
    summary: str


def _write_skeleton(changes: Mapping[str, str], path: Path) -> None:
    rows = json.loads(regen_parts.SKELETON.read_text(encoding="utf-8"))
    unknown = set(changes) - {r["name"] for r in rows}
    if unknown:
        raise ValueError(f"unknown parameters: {sorted(unknown)}")
    path.write_text(json.dumps([{**r, "expression": changes.get(r["name"], r["expression"])} for r in rows]),
                    encoding="utf-8")


def _regen_copy(case_dir: Path, skeleton: Path) -> list[str]:
    _, errors = regen_parts.regen_all(regen_parts.part_sources(), skeleton, parts_dir=case_dir / "parts",
                                      hist=case_dir / "hist", force=True)
    return errors


def _summary(eval_json: Path) -> tuple[list[str], str]:
    data = json.loads(eval_json.read_text(encoding="utf-8"))
    errors = [f"{f['name']}: {f.get('error') or f.get('warning')}"
              for f in data["timeline"] if f.get("error") or f.get("warning")]
    boxes = {b["name"]: b["bbox"] for b in data["bodies"]}
    desk = boxes.get("Desktop")
    summary = (f"desk {desk['max'][0] - desk['min'][0]:.1f} x {desk['max'][1] - desk['min'][1]:.1f}, "
               f"top {desk['max'][2]:.1f}" if desk else "no Desktop body")
    return errors, summary


def run_case(name: str, changes: Mapping[str, str], out: Path = OUT) -> CaseResult:
    """Regenerate a private copy of the parts with the case's skeleton and build the assembly."""
    case_dir = out / name
    case_dir.mkdir(parents=True, exist_ok=True)
    skeleton = case_dir / "params.json"
    _write_skeleton(changes, skeleton)
    errors = _regen_copy(case_dir, skeleton)
    occurrences = [*build_assembly.OCCURRENCES, *build_assembly.load_hw_occurrences()]
    script = case_dir / "assembly.json"
    script.write_text(json.dumps(build_assembly.build_script(occurrences, case_dir / "parts", skeleton)),
                      encoding="utf-8")
    design, eval_json = case_dir / f"{name}.solidcraft", case_dir / "eval.json"
    for args in (["run", str(script), "--save", str(design), "--quiet"],
                 ["eval", str(design), "--json-out", str(eval_json)]):
        result = subprocess.run([CLI, *args], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return CaseResult(name, (*errors, (result.stderr or result.stdout).strip()[:300]), "build failed")
    timeline_errors, summary = _summary(eval_json)
    return CaseResult(name, (*errors, *timeline_errors), summary)


def main(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cases", type=Path, help="JSON file of {case: {param: expression}}")
    args = parser.parse_args(argv)
    cases = json.loads(args.cases.read_text(encoding="utf-8")) if args.cases else DEFAULT_CASES
    with ThreadPoolExecutor(len(cases)) as pool:
        results = list(pool.map(lambda kv: run_case(*kv), cases.items()))
    for r in results:
        log.info("%s: %s, %d error(s)", r.name, r.summary, len(r.errors))
        for e in r.errors[:8]:
            log.error("    %s", e)
    return 1 if any(r.errors for r in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
