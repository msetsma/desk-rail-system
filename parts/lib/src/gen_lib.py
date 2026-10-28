"""Generate solidcraft-cli build scripts for the hardware library (parts/lib)."""
import json
from pathlib import Path

HERE = Path(__file__).parent
TEMPLATE = json.loads((HERE.parent.parent / "_template.json").read_text())["commands"]


def finish(body: str, pn: str, desc: str, material: str, color: str, label: str) -> list[dict]:
    return [
        {"command": "material.assign", "params": {"bodies": [body], "material": material}},
        {"command": "appearance.assign", "params": {"bodies": [body], "color": color}},
        {"command": "document.metadata.set", "params": {"values": {
            "part_number": pn, "description": desc, "revision": "A", "project": "desk",
            "com.setsma.desk": {"lib_id": label, "Material": material, "ReleaseState": "Released"},
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
    return {"input": INPUT[label], "commands": cmds + finish(new, pn, desc, mat, col, label)}


def screw() -> dict:
    b = "M6x20_SHCS"
    cmds = list(TEMPLATE) + [
        {"command": "solid.cylinder", "params": {"diameter": 10, "height": 6, "base": [0, 0, 0], "name": "Head", "body_name": b}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 20.05, "base": [0, 0, -20], "operation": "join", "targets": [b], "name": "Shank"}},
        {"command": "sketch.create", "params": {"plane": "XY", "offset": 6.1, "name": "HexSocketSketch"}},
        {"command": "sketch.polygon.circumscribed", "params": {"center": [0, 0], "radius": 2.5, "sides": 6}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"distance": 3.1, "direction": "negative", "operation": "cut", "targets": [b], "name": "HexSocket"}},
    ]
    return {"commands": cmds + finish(b, "ISO 4762 M6x20", "Socket head cap screw M6x20, black-oxide steel (simplified, no thread)", "Steel black-oxide", "#2b2b2b", "HW-L10_M6x20_SHCS")}


def standoff() -> dict:
    b = "Standoff_M5x12"
    cmds = list(TEMPLATE) + [
        {"command": "solid.cylinder", "params": {"diameter": 10, "height": 12, "base": [0, 0, 0], "name": "Standoff", "body_name": b}},
        {"command": "solid.cylinder", "params": {"diameter": 5, "height": 12.2, "base": [0, 0, -0.1], "operation": "cut", "targets": [b], "name": "BoreM5"}},
    ]
    return {"commands": cmds + finish(b, "Standoff M5x12 d10", "Round standoff d10 x 12, M5 through bore (simplified), zinc-plated steel", "Steel zinc-plated", "#c4c9d0", "HW-L11_Standoff_M5x12")}


if __name__ == "__main__":
    for lab in STEP:
        (HERE / f"{lab}.json").write_text(json.dumps(step_script(lab), indent=1))
    (HERE / "HW-L10_M6x20_SHCS.json").write_text(json.dumps(screw(), indent=1))
    (HERE / "HW-L11_Standoff_M5x12.json").write_text(json.dumps(standoff(), indent=1))
