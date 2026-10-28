"""Rebuild part files from their scripts and freeze them for fast linking.

    python tools/regen_parts.py              # rebuild parts whose script or skeleton changed
    python tools/regen_parts.py --force      # rebuild everything
    python tools/regen_parts.py FRM-03 DSK   # only parts whose file name starts with these prefixes

The build scripts (`parts/src/*.json`, `parts/lib/src/HW-*.json`) are the source of truth. Each part
is built with its history into `build/parts_hist/<stem>.solidcraft` (open that one to inspect or edit
interactively). It's then exported to STEP and re-imported as a single feature, with materials,
colours and metadata replayed, into `parts/<stem>.solidcraft`, the file the assembly links. Inserting or
refreshing a frozen part costs ~1 s instead of re-running its history.

Afterwards, refresh only the changed links in the assembly: `component.update_links {component: X}`
for each component printed. A bare `{}` re-evaluates every link (~40 s).
Exits non-zero if any part fails to build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import subprocess
import sys
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

__all__ = ["RegenError", "PartSource", "part_sources", "regen_part", "regen_all", "main"]

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PARTS = ROOT / "parts"
SKELETON = ROOT / "skeleton" / "params.json"
HIST = ROOT / "build" / "parts_hist"
CACHE = HIST / "hashes.json"
CLI = "solidcraft-cli"
REPLAYED = ("material.assign", "appearance.assign", "document.metadata.set")


class RegenError(Exception):
    """A part failed to build or freeze."""


@dataclass(frozen=True)
class PartSource:
    """A part's build script and the frozen file it produces (relative to the parts folder)."""

    script: Path
    rel_out: Path

    @property
    def stem(self) -> str:
        return self.script.stem

    @property
    def component(self) -> str:
        number, _, name = self.stem.partition("_")
        return f"{number} {name.replace('_', ' ')}"


def part_sources() -> list[PartSource]:
    """Every part script: assembly parts and the hardware library."""
    parts = [PartSource(s, Path(f"{s.stem}.solidcraft")) for s in sorted((PARTS / "src").glob("*.json"))]
    lib = [PartSource(s, Path("lib") / f"{s.stem}.solidcraft") for s in sorted((PARTS / "lib" / "src").glob("HW-*.json"))]
    return parts + lib


def _load(script: Path) -> dict[str, object]:
    try:
        data = json.loads(script.read_text(encoding="utf-8"))
        data["commands"]
        return data
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise RegenError(f"cannot read {script}: {exc}") from exc


def _commands(script: Path) -> list[dict[str, object]]:
    return _load(script)["commands"]


def _input_args(script: Path) -> list[str]:
    """A script may start from a vendor file: {"input": "<repo-relative path>", "commands": [...]}."""
    source = _load(script).get("input")
    return ["--in", str(ROOT / source)] if source else []


def _with_skeleton(commands: list[dict[str, object]], skeleton: Path) -> list[dict[str, object]]:
    return [{**c, "params": {**c["params"], "path": skeleton.as_posix()}} if c["command"] == "parameters.import" else c
            for c in commands]


def _uses_skeleton(commands: Sequence[dict[str, object]]) -> bool:
    return any(c["command"] == "parameters.import" for c in commands)


def _digest(source: PartSource, skeleton: Path) -> str:
    text = source.script.read_bytes()
    if _uses_skeleton(_commands(source.script)):
        text += skeleton.read_bytes()
    return hashlib.sha256(text).hexdigest()


def _run(script: dict[str, object], path: Path, args: Sequence[str]) -> None:
    path.write_text(json.dumps(script), encoding="utf-8")
    result = subprocess.run([CLI, "run", str(path), *args, "--quiet"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RegenError(f"{path.name}: {(result.stderr or result.stdout).strip()[:400]}")


def regen_part(source: PartSource, skeleton: Path = SKELETON, parts_dir: Path = PARTS, hist: Path = HIST) -> Path:
    """Build one part with history, then freeze it into `parts_dir`; returns the frozen file."""
    hist.mkdir(parents=True, exist_ok=True)
    commands = _with_skeleton(_commands(source.script), skeleton)
    built, step = hist / f"{source.stem}.solidcraft", hist / f"{source.stem}.step"
    _run({"commands": commands}, hist / f"{source.stem}.build.json",
         [*_input_args(source.script), "--save", str(built)])
    _run({"commands": [{"command": "file.export", "params": {"path": step.as_posix()}}]},
         hist / f"{source.stem}.export.json", ["--in", str(built), "--save", str(hist / f"{source.stem}.tmp.solidcraft")])
    frozen = [c for c in commands if c["command"] == "material.create"]
    frozen.append({"command": "file.insert_step", "params": {"path": step.as_posix(), "name": source.stem, "names": "solid"}})
    frozen += [c for c in commands if c["command"] in REPLAYED]
    out = parts_dir / source.rel_out
    out.parent.mkdir(parents=True, exist_ok=True)
    _run({"commands": frozen}, hist / f"{source.stem}.freeze.json", ["--save", str(out)])
    return out


def _load_cache() -> dict[str, str]:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def regen_all(sources: Sequence[PartSource], skeleton: Path = SKELETON, parts_dir: Path = PARTS,
              hist: Path = HIST, force: bool = False, workers: int = 8) -> tuple[list[PartSource], list[str]]:
    """Rebuild the sources that changed (all with `force`) in parallel; returns (rebuilt, errors)."""
    use_cache = parts_dir == PARTS and skeleton == SKELETON
    cache = _load_cache() if use_cache else {}
    digests = {s.stem: _digest(s, skeleton) for s in sources}
    todo = [s for s in sources if force or not use_cache or cache.get(s.stem) != digests[s.stem]
            or not (parts_dir / s.rel_out).is_file()]
    errors: list[str] = []

    def one(source: PartSource) -> PartSource | None:
        try:
            regen_part(source, skeleton, parts_dir, hist)
            return source
        except RegenError as exc:
            errors.append(str(exc))
            return None

    with ThreadPoolExecutor(workers) as pool:
        rebuilt = [s for s in pool.map(one, todo) if s is not None]
    if use_cache:
        cache.update({s.stem: digests[s.stem] for s in rebuilt})
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    return rebuilt, errors


def main(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("prefixes", nargs="*", help="only part files starting with these")
    parser.add_argument("--force", action="store_true", help="rebuild even if unchanged")
    args = parser.parse_args(argv)
    sources = [s for s in part_sources() if not args.prefixes or s.stem.startswith(tuple(args.prefixes))]
    rebuilt, errors = regen_all(sources, force=args.force)
    for e in errors:
        log.error("%s", e)
    log.info("%d rebuilt, %d unchanged, %d failed", len(rebuilt), len(sources) - len(rebuilt) - len(errors), len(errors))
    if rebuilt:
        log.info("refresh in the assembly (one call each):")
        for s in rebuilt:
            log.info('  component.update_links {"component": "%s"}', s.component)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
