"""Generate parts/src/MON-03_Insta360Link2Pro.json (Insta360 Link 2 Pro webcam on its magnetic clip).

Reference model of the user's webcam, clipped on the top edge of the main monitor (MON-01). The geometry is the
Sketchfab "Insta360 Link 2 4K AI Webcam" mesh by bswlife (CC BY 4.0), a Link 2, which has the Pro's outer size;
MON-03_convert.py scales it, unfolds the clip onto the M32U edge and writes a faceted STEP
(refs/insta360_link2pro/converted/, git-ignored like the download). Run the converter first on a fresh checkout:

    python parts/src/MON-03_convert.py && python parts/src/MON-03_gen.py && python tools/regen_parts.py MON-03

Finish: Graphite Black (the user's colour is assumed; Arctic White also exists).

Local frame: X right (pan axis at 0), camera faces -Y, Z up. Origin = inside face of the clip's front lip
(the monitor front face) on the clip underside (the monitor top edge).
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["build", "main"]

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
OUT = ROOT / "parts/src/MON-03_Insta360Link2Pro.json"
SUMMARY = ROOT / "refs/insta360_link2pro/converted/MON-03_link2.json"

# bodies, material, colour
FINISHES: list[tuple[list[str], str, str]] = [
    (["Webcam_Body", "Webcam_Mount"], "ABS", "#1b1c1e"),  # Graphite Black (estimate from store photos)
    (["Webcam_Lens"], "ABS", "#0a0c10"),  # lens glass, dark
]


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def summary() -> dict:
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


def finish(info: dict) -> list[dict]:
    ref = info["reference"]
    size = ref["camera_size_mm"]
    desc = ("Insta360 Link 2 Pro 4K gimbal webcam on its magnetic clip, Graphite Black; Link 2 mesh stand-in "
            f"(same outer size), camera {size['w']} x {size['h']} x {size['d']} mm. "
            "Origin: clip front-lip inner face on the clip underside (monitor front face / top edge); faces -Y, Z up")
    cmds: list[dict] = []
    for bodies, material, color in FINISHES:
        cmds += [c("material.assign", bodies=bodies, material=material),
                 c("appearance.assign", bodies=bodies, color=color)]
    cmds.append(c("document.metadata.set", values={
        "part_number": "MON-03", "description": desc, "revision": "A", "project": "desk",
        "com.setsma.desk": {
            "Material": "ABS (stand-in for PC/ABS housing, aluminium gimbal, glass lens)",
            "ReleaseState": "WIP",
            "Source": (f"{info['credit']} ({info['source']}) -> parts/src/MON-03_convert.py -> {info['step']} "
                       f"({info['triangles']} triangles, sha256 {info['step_sha256'][:12]}); scaled "
                       f"{ref['scale_mm_per_unit']} mm/unit to the official 58.9 mm height (MEASURE); clip rear "
                       f"leg unfolded {ref['rear_leg_unfold_deg']} deg onto the {ref['slab_t_mm']} mm M32U edge"),
        },
    }))
    return cmds


def build() -> dict:
    info = summary()
    return {"input": info["step"], "commands": [*TEMPLATE, *finish(info)]}


def main() -> None:
    OUT.write_text(json.dumps({"generated_by": "parts/src/MON-03_gen.py", **build()}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
