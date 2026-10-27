"""Every score on the board must reproduce from its inputs.

data/board.json holds each fighter's public record and the published scores.
If a formula or a record changes a published number, this test fails, so no
score on the site changes without someone deciding it should.
Skipped in the public demo repo, which ships stand-in formulas.
"""
import json
import os

import pytest

from scoring import service

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
pytestmark = pytest.mark.skipif(not service.PRIVATE_FORMULAS, reason="scoring formulas are private")


def raw_board():
    with open(os.path.join(ROOT, "data", "board.json"), encoding="utf-8") as f:
        return json.load(f)


def test_published_scores_reproduce():
    for f in raw_board()["fighters"]:
        s = service.score_both(f)
        assert abs(s["one"]["score"] - f["expected"]["ONE"]) < 0.05, f["name"]
        assert abs(s["ufc"]["score"] - f["expected"]["DWCS"]) < 0.05, f["name"]


def test_everyone_clears_the_threshold():
    data = raw_board()
    for f in data["fighters"]:
        assert min(f["expected"]["ONE"], f["expected"]["DWCS"]) >= data["threshold"], f["name"]


def test_board_rules():
    for f in raw_board()["fighters"]:
        assert f["wins"] + f["losses"] + f["draws"] >= 4, f"{f['name']}: under 4 pro fights"
        assert isinstance(f["age"], int), f"{f['name']}: no usable age"
        assert "KSW" not in (f["onePromotion"], f["dwcsPromotion"]), f"{f['name']}: KSW fighters never appear"


def test_calculator_reproduces_board():
    """Loading a board fighter into the calculator gives the same scores."""
    for f in service.board()["fighters"]:
        s = service.score_both(service.parse_request(f["calculator"]))
        assert s["one"]["score"] == f["one"]["score"], f["name"]
        assert s["ufc"]["score"] == f["ufc"]["score"], f["name"]
