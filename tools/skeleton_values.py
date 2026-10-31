"""Evaluated skeleton parameter values (mm / rad) for part generators.

skeleton/params.json holds expressions only (no stored values), so generators that need numbers (edge and
face pick points, which SolidCraft takes as plain coordinates) get them here: the skeleton is imported into
an empty design with solidcraft-cli and evaluated (~0.2 s). Results are cached in build/ by the file's hash.

    import skeleton_values
    v = skeleton_values.values()      # {"ts_h": 50.8, ...}
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

__all__ = ["SkeletonError", "values"]

ROOT = Path(__file__).resolve().parent.parent
PARAMS = ROOT / "skeleton" / "params.json"
CACHE = ROOT / "build" / "skeleton_values.json"
CLI = "solidcraft-cli"


class SkeletonError(Exception):
    """The skeleton could not be evaluated."""


def _evaluate(params: Path) -> dict[str, float]:
    with tempfile.TemporaryDirectory() as tmp:
        script, design, report = (Path(tmp) / n for n in ("skel.json", "skel.solidcraft", "eval.json"))
        cmd = {"command": "parameters.import", "params": {"path": params.as_posix()}}
        script.write_text(json.dumps({"commands": [cmd]}), encoding="utf-8")
        for args in (["run", str(script), "--save", str(design)], ["eval", str(design), "--json-out", str(report)]):
            result = subprocess.run([CLI, *args], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                raise SkeletonError((result.stderr or result.stdout).strip()[:400])
        rows = json.loads(report.read_text(encoding="utf-8"))["params"]
    bad = [r["name"] for r in rows if r.get("error")]
    if bad:
        raise SkeletonError(f"skeleton parameters failed to evaluate: {', '.join(bad)}")
    return {r["name"]: float(r["value"]) for r in rows if isinstance(r.get("value"), (int, float))}


def values(params: Path = PARAMS) -> dict[str, float]:
    """Every parameter's evaluated value in `params` (default: the shared skeleton), cached by the file's hash."""
    digest = hashlib.sha256(params.read_bytes()).hexdigest()
    cache = CACHE if params == PARAMS else CACHE.with_name(f"skeleton_values_{digest[:12]}.json")
    if cache.is_file():
        cached = json.loads(cache.read_text(encoding="utf-8"))
        if cached.get("sha256") == digest:
            return cached["values"]
    result = _evaluate(params)
    cache.parent.mkdir(exist_ok=True)
    cache.write_text(json.dumps({"sha256": digest, "values": result}, indent=1), encoding="utf-8")
    return result
