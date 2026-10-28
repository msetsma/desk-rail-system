"""Push the shared skeleton parameters into every layout-driven part file.

    python tools/regen_parts.py            # all parts listed in parts/layout_parts.json
    python tools/regen_parts.py FRM-03     # only parts whose file name starts with these prefixes

SolidCraft linked parts can't read assembly parameters, so layout-driven parts import
skeleton/params.json and rebuild headless. Afterwards run `component.update_links {}` in the
assembly (or reopen it) to pick up the new geometry.
Exits non-zero if any part fails to rebuild.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

__all__ = ["RegenError", "load_part_list", "regen_part", "main"]

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SKELETON = ROOT / "skeleton" / "params.json"
PART_LIST = ROOT / "parts" / "layout_parts.json"
CLI = "solidcraft-cli"


class RegenError(Exception):
    """A part file failed to rebuild with the skeleton parameters."""


def load_part_list(path: Path = PART_LIST) -> list[Path]:
    """Read the list of layout-driven part files (paths relative to the repo root)."""
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegenError(f"cannot read part list {path}: {exc}") from exc
    if not isinstance(entries, list) or not all(isinstance(e, str) for e in entries):
        raise RegenError(f"{path} must be a JSON list of part file paths")
    return [ROOT / e for e in entries]


def _import_script(skeleton: Path) -> dict[str, object]:
    return {"commands": [{"command": "parameters.import", "params": {"path": skeleton.as_posix()}}]}


def regen_part(part: Path, skeleton: Path = SKELETON) -> None:
    """Import the skeleton parameters into one part file and save it in place."""
    if not part.is_file():
        raise RegenError(f"missing part file {part}")
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "regen.json"
        script.write_text(json.dumps(_import_script(skeleton)), encoding="utf-8")
        result = subprocess.run(
            [CLI, "run", str(script), "--in", str(part), "--save", str(part), "--quiet"],
            capture_output=True, text=True, check=False,
        )
    if result.returncode != 0:
        raise RegenError(f"{part.name}: {result.stderr.strip() or result.stdout.strip()}")
    log.info("rebuilt %s", part.relative_to(ROOT))


def main(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    prefixes = tuple(argv)
    parts = [p for p in load_part_list() if not prefixes or p.name.startswith(prefixes)]
    failures = 0
    for part in parts:
        try:
            regen_part(part)
        except RegenError as exc:
            log.error("%s", exc)
            failures += 1
    log.info("%d part(s) rebuilt, %d failed", len(parts) - failures, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
