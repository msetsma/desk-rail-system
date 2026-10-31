"""Laid-speaker geometry: frame vectors and placement expressions agree with the solver's maths."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build_variant
import spk_laid

V = {"spk_mount_frac": 0.75, "spk_h": 298.5, "spk_w": 147.6, "spk_d": 214.3, "desk_h": 673.1}
LAYOUT = spk_laid.LaidLayout(x=554.9, y=228.1, yaw=math.radians(30), tilt=math.radians(8), st_w=300, st_d=220, st_h=12)


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


@pytest.mark.parametrize("side", [spk_laid.LEFT, spk_laid.RIGHT])
def test_frame_vectors_are_a_right_handed_basis_keeping_the_front(side: int) -> None:
    zl, xl = spk_laid.frame_vectors(side, LAYOUT.tilt)
    assert sum(a * a for a in zl) == pytest.approx(1) and sum(a * b for a, b in zip(zl, xl)) == pytest.approx(0)
    yl = _cross(zl, xl)  # local direction landing on world +Y
    assert yl[1] == pytest.approx(math.cos(LAYOUT.tilt))  # local +Y (back) stays mostly world +Y


@pytest.mark.parametrize("side", [spk_laid.LEFT, spk_laid.RIGHT])
def test_tweeter_end_points_outboard_and_front_tilts_up(side: int) -> None:
    m = spk_laid.frame_matrix(side, LAYOUT.tilt)
    tweeter = [m[i][2] for i in range(3)]  # image of local +Z
    front = [-m[i][1] for i in range(3)]  # image of local -Y
    assert tweeter[0] == pytest.approx(side)
    assert front[2] > 0


def _eval(expr: str, values: dict[str, float]) -> float:
    env = {"sin": math.sin, "cos": math.cos, **values}
    return eval(expr.replace(" mm", ""), {"__builtins__": {}}, env)


@pytest.mark.parametrize("side", [spk_laid.LEFT, spk_laid.RIGHT])
def test_occurrence_expressions_match_solver(side: int) -> None:
    values = {**V, "spk_lay_x": LAYOUT.x, "spk_lay_y": LAYOUT.y, "spk_lay_yaw": LAYOUT.yaw,
              "spk_st_d": LAYOUT.st_d, "spk_st_h": LAYOUT.st_h, "spk_st_tilt": LAYOUT.tilt}
    tag = "L" if side == spk_laid.LEFT else "R"
    occ = {o.label: o for o in build_variant.laid_occurrences(LAYOUT.tilt)}
    spk, stand = occ[f"Speaker_{tag}"], occ[f"SpkStand_{tag}"]
    ox, oy, oz = spk_laid.speaker_origin(side, LAYOUT, V)
    assert _eval(spk.x, values) == pytest.approx(ox)
    assert _eval(spk.y, values) == pytest.approx(oy)
    assert _eval(spk.z, values) == pytest.approx(oz + V["desk_h"])
    sx, sy, _ = spk_laid.stand_origin(side, LAYOUT)
    assert (_eval(stand.x, values), _eval(stand.y, values)) == pytest.approx((sx, sy))
    assert _eval(spk.yaw, values) == pytest.approx(-side * LAYOUT.yaw)
