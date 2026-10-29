"""Generate parts/src/INP-01_MousePad.json (16.5 in square mouse pad).

Layout-driven: imports the skeleton (pad_size, pad_t, pad_r). The corner fillet picks its edges by point,
so the points come from the evaluated skeleton (tools/skeleton_values.py) and follow pad_size / pad_t.

Local frame: origin = bottom face centre (on the desktop); X right, +Y toward the wall, Z up.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/2015m/DEV/CAD/desk")
sys.path.insert(0, str(ROOT / "tools"))
import skeleton_values  # noqa: E402

__all__ = ["build", "main"]

TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
SKEL = {"command": "parameters.import", "params": {"path": f"{ROOT.as_posix()}/skeleton/params.json"}}
OUT = ROOT / "parts/src/INP-01_MousePad.json"
BODY = "MousePad"
MATERIAL = "ABS"
COLOR = "#232323"


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def pad(v: dict[str, float]) -> list[dict]:
    h = v["pad_size"] / 2
    corners = [[sx * h, sy * h, v["pad_t"] / 2] for sx in (-1, 1) for sy in (-1, 1)]  # vertical corner edges
    return [
        c("solid.box", name="MousePad_Slab", body_name=BODY, length="pad_size", width="pad_size", height="pad_t",
          corner=["-pad_size/2", "-pad_size/2", "0 mm"], operation="new"),
        c("solid.fillet", name="MousePad_Corners", body=BODY, radius="pad_r", edges=corners),
    ]


def finish() -> list[dict]:
    return [
        c("material.assign", bodies=[BODY], material=MATERIAL),
        c("appearance.assign", bodies=[BODY], color=COLOR),
        c("document.metadata.set", values={
            "part_number": "INP-01", "revision": "A", "project": "desk",
            "description": "Mouse pad 16.5in square. Origin: bottom face centre (on the desktop); X right, "
                           "+Y toward wall, Z up",
            "com.setsma.desk": {"Material": MATERIAL, "ReleaseState": "WIP", "Source": "Skeleton pad_* params"},
        }),
    ]


def build() -> list[dict]:
    return [*TEMPLATE, SKEL, *pad(skeleton_values.values()), *finish()]


def main() -> None:
    OUT.write_text(json.dumps({"generated_by": "parts/src/INP-01_gen.py", "commands": build()}, indent=1),
                   encoding="utf-8")


if __name__ == "__main__":
    main()
