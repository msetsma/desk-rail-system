"""Generate solidcraft-cli build scripts for the hardware library (parts/lib)."""
import json
from pathlib import Path

HERE = Path(__file__).parent
TEMPLATE = json.loads((HERE.parent.parent / "_template.json").read_text())["commands"]


def finish(body: str, pn: str, desc: str, material: str, color: str, label: str, source: str) -> list[dict]:
    return [
        {"command": "material.assign", "params": {"bodies": [body], "material": material}},
        {"command": "appearance.assign", "params": {"bodies": [body], "color": color}},
        {"command": "document.metadata.set", "params": {"values": {
            "part_number": pn, "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {"lib_id": label, "Material": material, "ReleaseState": "Released", "Source": source},
        }}},
        {"command": "document.metadata", "params": {}},
    ]


STEP = {
    "HW-L01_HPTTD5": ("HPTTD5-SET_b", "HPTTD5", "HPTTD5", "Misumi HPTTD5 T-joint plate, 5 series, 2.3 mm", "Steel zinc-plated", "#c4c9d0"),
    "HW-L02_HPTLD5": ("HPTLD5-SET_b", "HPTLD5", "HPTLD5", "Misumi HPTLD5 L-joint plate, 5 series, 2.3 mm", "Steel zinc-plated", "#c4c9d0"),
    "HW-L03_HBLFSN5": ("Diameter Hole3", "HBLFSN5", "HBLFSN5", "Misumi HBLFSN5 cast bracket, 5 series", "Al ADC12 cast", "#a9adb2"),
    "HW-L04_HBLFSD5": ("HBLFSD5-SETh5", "HBLFSD5", "HBLFSD5", "Misumi HBLFSD5 cast bracket, 5 series, 2 slots (40 wide)", "Al ADC12 cast", "#a9adb2"),
}


# Vendor STEP each library script starts from (repo-relative; regen_parts opens it with --in).
INPUT = {
    "HW-L01_HPTTD5": "refs/misumi_brackets/HPTTD5/HPTTD5_plate.stp",
    "HW-L02_HPTLD5": "refs/misumi_brackets/HPTLD5/HPTLD5_plate.stp",
    "HW-L03_HBLFSN5": "refs/misumi_brackets/HBLFSN5/HBLFSN5_bracket.stp",
    "HW-L04_HBLFSD5": "refs/misumi_brackets/HBLFSD5/HBLFSD5_bracket.stp",
}


def step_script(label: str) -> dict:
    old, new, pn, desc, mat, col = STEP[label]
    cmds = list(TEMPLATE)
    if old:
        cmds.append({"command": "body.rename", "params": {"body": old, "name": new}})
    source = f"Misumi vendor STEP {INPUT[label]}"
    return {"input": INPUT[label], "commands": cmds + finish(new, pn, desc, mat, col, label, source)}


SIMPLIFIED = "Modelled (simplified)"


def screw() -> dict:
    b = "M6x55_SHCS"
    cmds = list(TEMPLATE) + [
        {"command": "solid.cylinder", "params": {"diameter": 10, "height": 6, "base": [0, 0, 0], "name": "Head", "body_name": b}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 55.05, "base": [0, 0, -55], "operation": "join", "targets": [b], "name": "Shank"}},
        {"command": "sketch.create", "params": {"plane": "XY", "offset": 6.1, "name": "HexSocketSketch"}},
        {"command": "sketch.polygon.circumscribed", "params": {"center": [0, 0], "radius": 2.5, "sides": 6}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"distance": 3.1, "direction": "negative", "operation": "cut", "targets": [b], "name": "HexSocket"}},
    ]
    return {"commands": cmds + finish(b, "ISO 4762 M6x55", "Socket head cap screw M6x55, black-oxide steel (simplified, no thread)", "Steel black-oxide", "#2b2b2b", "HW-L10_M6x55_SHCS", SIMPLIFIED)}


def standoff() -> dict:
    b = "Standoff_M5x12"
    cmds = list(TEMPLATE) + [
        {"command": "solid.cylinder", "params": {"diameter": 10, "height": 12, "base": [0, 0, 0], "name": "Standoff", "body_name": b}},
        {"command": "solid.cylinder", "params": {"diameter": 5, "height": 12.2, "base": [0, 0, -0.1], "operation": "cut", "targets": [b], "name": "BoreM5"}},
    ]
    return {"commands": cmds + finish(b, "Standoff M5x12 d10", "Round standoff d10 x 12, M5 through bore (simplified), zinc-plated steel", "Steel zinc-plated", "#c4c9d0", "HW-L11_Standoff_M5x12", SIMPLIFIED)}


TS5_STEP = "refs/misumi_brackets/HBL45T5/HBL45TS5-SET.stp"
TD5_HALF_PITCH = 10.0  # 2 slots on the 20 mm HFS5 pitch
TD5_HOLE_D = 5.5
TD5_BASE_HOLE_Z = 72.12  # vendor HBL45TS5 STEP: base-face hole, 72.12 from the vertex
TD5_ANGLED_HOLE = 51.0   # angled-face hole at (y, z) = (51, 51)


def angle_bracket_2slot() -> dict:
    """HBL45TD5: the vendor HBL45TS5 extruded profile (14 wide) widened to 34, with 2 holes per face at x = +/-10.

    Catalog p2255: same section, 34 wide, 4 x d5.5 on the 20 mm pitch. The profile is taken from the TS5 STEP's
    end face (x = +7), extruded 34 as a new body (no holes) and centred, then the 4 holes are cut.
    """
    b = "HBL45TD5"
    hole_cmds = []
    for x in (-TD5_HALF_PITCH, TD5_HALF_PITCH):
        hole_cmds += [
            {"command": "solid.cylinder", "params": {"diameter": TD5_HOLE_D, "height": 15, "base": [x, -1, TD5_BASE_HOLE_Z],
                                                     "axis": "Y", "operation": "cut", "targets": [b], "name": f"Hole_Base_{'L' if x < 0 else 'R'}"}},
            {"command": "solid.cylinder", "params": {"diameter": TD5_HOLE_D, "height": 15,
                                                     "base": [x, TD5_ANGLED_HOLE + 0.7071, TD5_ANGLED_HOLE - 0.7071],
                                                     "axis": [0, -1, 1], "operation": "cut", "targets": [b], "name": f"Hole_Angled_{'L' if x < 0 else 'R'}"}},
        ]
    cmds = list(TEMPLATE) + [
        {"command": "solid.extrude", "params": {"face": [7, 2, 30], "face_body": "HBL45TS5_b", "distance": 34,
                                                "operation": "new", "body_name": b, "name": "Extrude_TD5_Profile"}},
        {"command": "solid.remove", "params": {"bodies": ["HBL45TS5_b", "CBM5-14_b", "HNTT5-5_1",
                                                          "CBM5-14_b (HBL45TS5-SET:1/CBM5-14_b:2)",
                                                          "HNTT5-5_1 (HBL45TS5-SET:1/HNTT5-5_1:2)"]}},
        {"command": "solid.move", "params": {"bodies": [b], "translate": [-24, 0, 0]}},
    ] + hole_cmds
    source = f"Modelled from Misumi vendor STEP {TS5_STEP} (HBL45TS5 section) + catalog p2255 (HBL45TD5: 34 wide, 4 holes)"
    return {"input": TS5_STEP, "commands": cmds + finish(
        b, "HBL45TD5", "Misumi HBL45TD5 45 deg angled bracket, 5 series, 2 slots (34 wide), 4 x M5, 1470 N",
        "Al 6063-T5", "#c8ccd1", "HW-L05_HBL45TD5", source)}


def _write(name: str, script: dict) -> None:
    (HERE / f"{name}.json").write_text(json.dumps({"generated_by": "parts/lib/src/gen_lib.py", **script}, indent=1))


if __name__ == "__main__":
    for lab in STEP:
        _write(lab, step_script(lab))
    _write("HW-L05_HBL45TD5", angle_bracket_2slot())
    _write("HW-L10_M6x55_SHCS", screw())
    _write("HW-L11_Standoff_M5x12", standoff())
