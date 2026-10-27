"""Recompute every score published on the Both Systems page.

The page reads static/both_systems.json. Each fighter there carries the inputs
and the published scores. This test runs the inputs through the Python
formulas and fails if any published number would change, or if any fighter
no longer clears the threshold on both systems.

ONE and DWCS are scored by separate formulas and never combined.

Run:  python scoring/test_both_systems.py     (or: pytest scoring)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from one_ascent_v3_9 import ascent_v39             # noqa: E402
from dwcs_ascent_v3_0 import calculate as dwcs_v30  # noqa: E402

BOARD = os.path.join(HERE, "..", "static", "both_systems.json")


def load_board():
    with open(BOARD, encoding="utf-8") as f:
        return json.load(f)


def score_one(f):
    return ascent_v39(wins=f["wins"], losses=f["losses"], draws=f["draws"],
                      finish_rate_pct=f["finishRate"], weight_class=f["division"],
                      age=f["age"], main_promotion=f["onePromotion"],
                      title_wins=f["titleWins"], country=f["country"])


def score_dwcs(f):
    total = f["wins"] + f["losses"] + f["draws"]
    return dwcs_v30(win_pct=100.0 * f["wins"] / total, fr_raw=f["finishRate"],
                    weight_class=f["division"].lower(), win_streak=f["winStreak"],
                    losses=f["losses"], age=f["age"], title_fight_wins=f["titleWins"],
                    promotion=f["dwcsPromotion"])["ascent_profile"]


def test_published_scores_reproduce():
    board = load_board()
    assert board["versions"] == {"ONE": "3.9", "DWCS": "3.0"}
    for f in board["fighters"]:
        one, dw = score_one(f), score_dwcs(f)
        assert abs(one - f["expected"]["ONE"]) < 0.05, f"{f['name']}: ONE {one} != {f['expected']['ONE']}"
        assert abs(dw - f["expected"]["DWCS"]) < 0.05, f"{f['name']}: DWCS {dw} != {f['expected']['DWCS']}"


def test_everyone_clears_threshold_on_both():
    board = load_board()
    cut = board["threshold"]
    for f in board["fighters"]:
        assert f["expected"]["ONE"] >= cut and f["expected"]["DWCS"] >= cut, f"{f['name']} below {cut}"


def test_board_rules():
    """Board rules from RULES.md that can be checked from the data alone."""
    board = load_board()
    for f in board["fighters"]:
        assert f["wins"] + f["losses"] + f["draws"] >= 4, f"{f['name']}: under 4 pro fights"
        assert isinstance(f["age"], int), f"{f['name']}: no usable age"
        assert f["onePromotion"] != "KSW" and f["dwcsPromotion"] != "KSW", f"{f['name']}: KSW fighters never appear"
    ones = [f["expected"]["ONE"] for f in board["fighters"]]
    assert ones == sorted(ones, reverse=True), "board must be listed by ONE score"


if __name__ == "__main__":
    test_published_scores_reproduce()
    test_everyone_clears_threshold_on_both()
    test_board_rules()
    print(f"OK - {len(load_board()['fighters'])} fighters reproduce on both systems")
