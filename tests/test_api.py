"""The JSON API behind the calculator and the board."""
from app import app

GOOD = {"wins": 8, "losses": 1, "draws": 0, "finishes": 6, "age": 24, "title_wins": 0,
        "win_streak": 5, "division": "Lightweight", "country": "Brazil", "promotion": "lfa"}


def post(body):
    return app.test_client().post("/api/score", json=body)


def test_score_returns_both_systems_separately():
    r = post(GOOD)
    assert r.status_code == 200
    j = r.get_json()
    assert j["one"]["name"] == "ONE ASCENT" and j["ufc"]["name"] == "DWCS/UFC ASCENT"
    for s in (j["one"], j["ufc"]):
        assert isinstance(s["score"], float)
        assert {g["label"] for g in s["groups"]} >= {"Finish rate", "Record", "Promotion", "Titles"}


def test_no_age_still_scores_one():
    r = post({**GOOD, "age": ""})
    assert r.status_code == 200 and r.get_json()["ufc"] is None


def test_bad_input_is_rejected_with_a_message():
    for bad, msg in [({"wins": 0}, "Wins"), ({"finishes": 9}, "Finishes"), ({"age": 70}, "Age"),
                     ({"division": "Catchweight"}, "division"), ({"promotion": "nope"}, "promotion"),
                     ({"wins": "eight"}, "whole number")]:
        r = post({**GOOD, **bad})
        assert r.status_code == 400 and msg.lower() in r.get_json()["error"].lower(), bad


def test_options_and_board():
    c = app.test_client()
    o = c.get("/api/options").get_json()
    assert {"value": "Lightweight", "label": "Lightweight (155)"} in o["divisions"] and o["countries"] and o["promotions"]
    assert all("Featherweight" not in d["value"] or not d["value"].startswith("Women") for d in o["divisions"])
    assert all(set(p) == {"id", "name"} for p in o["promotions"]), "options must not expose formula data"
    b = c.get("/api/board").get_json()
    assert b["fighters"] and all("expected" not in f for f in b["fighters"])
