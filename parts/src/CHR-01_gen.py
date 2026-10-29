"""Generate parts/src/CHR-01_HermanMillerMirra2.json (Herman Miller Mirra 2 work chair, Butterfly back).

Reference model of the user's chair, so the seated eye point can be placed against the desk. The geometry
is Herman Miller's own 3D DWG (Suspension Back, adjustable arms), converted by CHR-01_convert.py into a
faceted STEP (refs/herman_miller_mirra2/converted/, git-ignored like raw/). The script starts from that
STEP (`"input"`), so run the converter first on a fresh checkout:

    python parts/src/CHR-01_convert.py && python parts/src/CHR-01_gen.py && python tools/regen_parts.py CHR

User settings: seat all the way down (`chr_seat_h`, parametric: a move of everything above the gas
cylinder), arms all the way up and slid fully back (baked in by the converter).
Finish: Studio White frame, Fog base and mechanism, Graphite AireWeave seat and back.

Local frame: origin = floor at the gas-cylinder axis. The chair faces +Y, X to the user's right, Z up.
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["build", "main"]

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = json.loads((ROOT / "parts/_template.json").read_text(encoding="utf-8"))["commands"]
OUT = ROOT / "parts/src/CHR-01_HermanMillerMirra2.json"
SUMMARY = ROOT / "refs/herman_miller_mirra2/converted/CHR-01_mirra2.json"

CASTERS = [f"Chair_Caster_{i + 1}" for i in range(5)]
FIXED = ["Chair_Base", "Chair_Cylinder", *CASTERS]  # everything else rides on the gas spring
MOVING = ["Chair_Frame", "Chair_BackFabric", "Chair_Seat", "Chair_Arm_R", "Chair_Arm_L", "Chair_ArmPad_R",
          "Chair_ArmPad_L", "Chair_Mechanism", "Chair_Controls", "Chair_GasRod"]

# bodies, material, colour
FINISHES: list[tuple[list[str], str, str]] = [
    (["Chair_Frame", "Chair_Arm_R", "Chair_Arm_L"], "ABS", "#e8e6e1"),  # Studio White
    (["Chair_BackFabric", "Chair_Seat"], "ABS", "#2d2e30"),  # Graphite AireWeave
    (["Chair_ArmPad_R", "Chair_ArmPad_L"], "ABS", "#262729"),  # Graphite arm pads
    (["Chair_Base", "Chair_Mechanism"], "ABS", "#bdbfbe"),  # Fog (vendor layer SEAT-BASE holds both)
    (["Chair_Controls"], "ABS", "#1f2022"),  # black paddles and lumbar knobs
    (["Chair_Cylinder", "Chair_GasRod"], "Steel powder-coated", "#1c1d1f"),  # black gas cylinder
    (CASTERS, "ABS", "#1f2022"),  # black twin-wheel casters
]

SEAT_MIN = "16 in"  # spec: standard cylinder 16-20.5 in


def c(cmd: str, **params: object) -> dict:
    return {"command": cmd, "params": params}


def summary() -> dict:
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


def params_cmds(ref: dict) -> list[dict]:
    seat = ref["seat_top_mm"]
    return [
        c("parameters.add", name="chr_seat_h", expression=SEAT_MIN,
          comment="Seat top (suspension peak) above floor: user setting all the way down (spec 16-20.5 in)"),
        c("parameters.add", name="chr_seat_h_vendor", expression=f"{seat} mm",
          comment="Seat top in the vendor model (fixed; the upper group moves by chr_seat_h - this)"),
    ]


def seat_move() -> list[dict]:
    return [c("solid.move", bodies=MOVING, translate=[0, 0, "chr_seat_h - chr_seat_h_vendor"], name="CHR_SeatHeight")]


def finish(info: dict) -> list[dict]:
    ref = info["reference"]
    desc = ("Herman Miller Mirra 2 work chair, Butterfly (Suspension) back, adjustable arms; vendor 3D DWG mesh. "
            "Seat down, arms fully up and back. Studio White frame, Fog base, Graphite AireWeave. "
            "Origin: floor at the gas-cylinder axis; chair faces +Y, X right, Z up")
    cmds: list[dict] = []
    for bodies, material, color in FINISHES:
        cmds += [c("material.assign", bodies=bodies, material=material),
                 c("appearance.assign", bodies=bodies, color=color)]
    cmds.append(c("document.metadata.set", values={
        "part_number": "CHR-01", "description": desc, "revision": "A", "project": "desk",
        "com.setsma.desk": {
            "Material": "ABS (stand-in for glass-filled nylon frame/base and polyester textile); steel cylinder",
            "ReleaseState": "WIP",
            "Source": (f"Herman Miller 3D library DWG ({info['source']}) -> LibreDWG dwg2dxf -> "
                       f"parts/src/CHR-01_convert.py -> {info['step']} ({info['triangles']} triangles, "
                       f"sha256 {info['step_sha256'][:12]}); arms +{ref['arm_raise_mm']} mm (pad top "
                       f"{ref['arm_pad_top_above_seat_mm']} mm above the seat), pads {ref['arm_back_mm']} mm back"),
        },
    }))
    return cmds


def build() -> dict:
    info = summary()
    commands = [*TEMPLATE, *params_cmds(info["reference"]), *seat_move(), *finish(info)]
    return {"input": info["step"], "commands": commands}


def main() -> None:
    OUT.write_text(json.dumps(build(), indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
