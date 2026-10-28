"""Scoring service used by the website.

The formulas run on the server only. Pages get a score and a breakdown by
broad group (finishing, record, promotion, profile, titles), never the
individual weights or lookup tables.

ONE ASCENT and DWCS/UFC ASCENT are separate formulas on separate data.
Nothing here adds, averages or compares them.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Dict, List, Optional

try:  # private formulas
    from scoring import one_ascent_v3_9 as one
    from scoring import dwcs_ascent_v3_0 as dwcs
    PRIVATE_FORMULAS = True
except ImportError:  # public demo repo: stand-in formulas with the same interface
    from scoring import sample_formulas as one  # type: ignore
    from scoring import sample_formulas as dwcs  # type: ignore
    PRIVATE_FORMULAS = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD_PATH = os.path.join(ROOT, "data", "board.json")

ONE_NAME = "ONE ASCENT"
UFC_NAME = "DWCS/UFC ASCENT"

DIVISIONS = [
    "Flyweight", "Bantamweight", "Featherweight", "Lightweight", "Welterweight", "Middleweight",
    "Light Heavyweight", "Heavyweight", "Strawweight", "Women's Atomweight", "Women's Strawweight",
    "Women's Flyweight", "Women's Bantamweight",
]
WEIGHT_LIMIT = {  # pounds, UFC division names
    "Strawweight": 115, "Flyweight": 125, "Bantamweight": 135, "Featherweight": 145, "Lightweight": 155,
    "Welterweight": 170, "Middleweight": 185, "Light Heavyweight": 205, "Heavyweight": 265,
    "Women's Atomweight": 105, "Women's Strawweight": 115, "Women's Flyweight": 125, "Women's Bantamweight": 135,
}


def division_label(d: str) -> str:
    return f"{d} ({WEIGHT_LIMIT[d]})" if d in WEIGHT_LIMIT else d

# Promotions that sign fighters away from both pathways; not offered as a fighter's current home.
DESTINATIONS = {"UFC", "ONE", "KSW", "RIZIN", "PFL", "Road_To_UFC", "Brave FC", "Shooto_Brasil", "Hex"}

ONE_DISPLAY = {
    "ONE_Friday_Fights": "ONE Friday Fights", "OLMMA": "Octagon League", "SFH": "Samurai Fight House",
    "FNG": "Fight Night Global", "WEF": "World Ertaymash Federation", "UAEW": "UAE Warriors",
    "CFN": "Canggu Fight Night", "JCK": "Jue Cheng King", "GTC": "Golden Team Championship",
    "EFCA": "EFC Africa", "Inka": "Inka FC", "BRAVE_CF": "Brave CF", "ARES_FC": "Ares FC",
    "Shooto_Brazil": "Shooto Brasil", "Hex_Fight_Series": "HEX Fight Series", "Mr. Cage": "Mr. Cage",
    "SFT": "SFT Combat", "AMC_Fight_Nights": "AMC Fight Nights",
}
# ONE code -> DWCS name where the two lists spell the same promotion differently.
SAME_PROMOTION = {"UAEW": "UAE Warriors", "OLMMA": "Octagon", "Shooto_Brazil": "Shooto Brasil"}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


@lru_cache(maxsize=1)
def promotions() -> List[Dict[str, str]]:
    """One list of promotions for the calculator, each mapped to both formulas."""
    one_codes = list(getattr(one, "PROMOTIONS", None) or getattr(one, "PROMO_TABLE", {}))
    dwcs_names = list(getattr(dwcs, "PROMO_TIERS", {}))
    by_norm = {_norm(n): n for n in dwcs_names}
    used = set()
    out = []
    for code in one_codes:
        if code in DESTINATIONS or code == "Unknown":
            continue
        display = ONE_DISPLAY.get(code, code.replace("_", " "))
        d = SAME_PROMOTION.get(code) or by_norm.get(_norm(code)) or by_norm.get(_norm(display)) or ""
        used.add(d)
        out.append({"id": _norm(display), "name": display, "one": code, "dwcs": d})
    for name in dwcs_names:
        if name in used or name in DESTINATIONS:
            continue
        out.append({"id": _norm(name), "name": name, "one": "Unknown", "dwcs": name})
    out.sort(key=lambda p: p["name"].lower())
    out.append({"id": "other", "name": "Other or regional show", "one": "Unknown", "dwcs": ""})
    return out


def promotion(pid: str) -> Optional[Dict[str, str]]:
    return next((p for p in promotions() if p["id"] == pid), None)


@lru_cache(maxsize=1)
def countries() -> List[str]:
    skip = re.compile(r"^(American|Argentine|Armenian|Australian|Azerbaijani|Brazilian|British|Canadian|English|"
                      r"Filipino|French|Georgian|Indian|Indonesian|Irish|Italian|Kazakh|Kyrgyz|Kyrgystan|Mexican|"
                      r"Mongolian|Russian|Thai|Turkish|Tajik|Uzbek|Vietnamese|Bosnia and Herzegovnia|Czechia|"
                      r"Democratic Republic of Congo|Great Britain|UK|United States|Korea)$|/")
    names = [c for c, r in getattr(one, "COUNTRY_REGION", {}).items() if r and c == c.strip() and not skip.search(c)]
    return sorted(names)


def _groups(parts: Dict[str, float], spec: Dict[str, List[str]]) -> List[Dict[str, object]]:
    return [{"label": label, "value": round(sum(parts.get(k, 0.0) for k in keys), 1)}
            for label, keys in spec.items()]


ONE_GROUPS = {"Finishing": ["finish"], "Record": ["win", "unbeaten"], "Promotion": ["promo", "hq"],
              "Profile": ["origin", "age"], "Titles": ["title"]}
UFC_GROUPS = {"Baseline": ["anchor"], "Finishing": ["fr", "elite_finisher"],
              "Record": ["win_pct", "losses", "streak", "hot_streak"], "Promotion": ["promo"],
              "Profile": ["age"], "Titles": ["title"]}


def score_one(f: Dict) -> Dict:
    b = one.ascent_v39(wins=f["wins"], losses=f["losses"], draws=f["draws"],
                       finish_rate_pct=f["finishRate"], weight_class=f["division"], age=f["age"],
                       main_promotion=f["onePromotion"], title_wins=f["titleWins"],
                       country=f["country"], breakdown=True)
    parts = {"finish": b["fr_norm"] * one.FR_WEIGHT, "win": b["win_rate"] * one.WR_WEIGHT,
             "promo": b["promo_pts"], "hq": b["hq_bonus"], "origin": b["origin_fit"],
             "age": b["age_mod"], "title": b["title_bonus"], "unbeaten": b["undefeated_bonus"]}
    return {"name": ONE_NAME, "score": b["score"], "groups": _groups(parts, ONE_GROUPS)}


def score_ufc(f: Dict) -> Optional[Dict]:
    if not isinstance(f.get("age"), int):
        return None
    total = f["wins"] + f["losses"] + f["draws"]
    r = dwcs.calculate(win_pct=100.0 * f["wins"] / total, fr_raw=f["finishRate"],
                       weight_class=f["division"].lower(), win_streak=f["winStreak"],
                       losses=f["losses"], age=f["age"], title_fight_wins=f["titleWins"],
                       promotion=f["dwcsPromotion"])
    parts = {k: v * dwcs.ANCHOR_SLOPE for k, v in r["profile"].items()}
    parts["anchor"] = dwcs.ANCHOR_INTERCEPT
    return {"name": UFC_NAME, "score": r["ascent_profile"], "groups": _groups(parts, UFC_GROUPS)}


class InputError(ValueError):
    pass


def parse_request(data: Dict) -> Dict:
    """Validate calculator input. Raises InputError with a message a person can act on."""
    def num(key, lo, hi, required=True):
        v = data.get(key)
        if v in (None, ""):
            if required:
                raise InputError(f"Enter {key.replace('_', ' ')}.")
            return None
        try:
            v = int(v)
        except (TypeError, ValueError):
            raise InputError(f"{key.replace('_', ' ').capitalize()} must be a whole number.")
        if not lo <= v <= hi:
            raise InputError(f"{key.replace('_', ' ').capitalize()} must be between {lo} and {hi}.")
        return v

    wins = num("wins", 1, 99)
    losses = num("losses", 0, 99)
    draws = num("draws", 0, 99)
    finishes = num("finishes", 0, 99)
    if finishes > wins:
        raise InputError("Finishes can't be more than wins.")
    age = num("age", 16, 50, required=False)
    titles = num("title_wins", 0, 30)
    streak = min(num("win_streak", 0, 99), wins)
    division = data.get("division")
    if division not in DIVISIONS:
        raise InputError("Choose a division.")
    country = data.get("country") or ""
    if country and country not in countries():
        raise InputError("Choose a country from the list.")
    promo = promotion(str(data.get("promotion") or "other"))
    if promo is None:
        raise InputError("Choose a promotion from the list.")
    return {"wins": wins, "losses": losses, "draws": draws,
            "finishRate": round(100.0 * finishes / wins, 1),
            "age": age, "titleWins": titles, "winStreak": streak, "division": division, "country": country,
            "onePromotion": promo["one"], "dwcsPromotion": promo["dwcs"]}


def score_both(f: Dict) -> Dict:
    return {"one": score_one(f), "ufc": score_ufc(f)}


@lru_cache(maxsize=1)
def board() -> Dict:
    with open(BOARD_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    fighters = []
    for f in data["fighters"]:
        s = score_both(f)
        same_one = [p for p in promotions() if p["one"] == f["onePromotion"]]
        exact = [p for p in same_one if p["dwcs"] == f["dwcsPromotion"]]
        close = [p for p in same_one if _same_ufc_promo(p["dwcs"], f["dwcsPromotion"])]
        pid = (exact or close or [{"id": "other"}])[0]["id"]
        fighters.append({
            "name": f["name"], "country": f["country"], "age": f["ageLabel"], "division": f["division"],
            "divisionLabel": division_label(f["division"]),
            "record": f"{f['wins']}-{f['losses']}-{f['draws']}", "wins": f["wins"],
            "finishes": round(f["finishRate"] / 100 * f["wins"]), "promotion": f["promotionName"],
            "lastFight": f.get("lastFight"), "notes": f["notes"], "checking": f.get("flag", False),
            "tapology": f["tapology"], "one": s["one"], "ufc": s["ufc"],
            "calculator": {"wins": f["wins"], "losses": f["losses"], "draws": f["draws"],
                           "finishes": round(f["finishRate"] / 100 * f["wins"]), "age": f["age"],
                           "title_wins": f["titleWins"], "win_streak": f["winStreak"],
                           "division": f["division"], "country": f["country"], "promotion": pid},
        })
    fighters.sort(key=lambda x: -x["one"]["score"])
    return {"scored": data["scored"], "threshold": data["threshold"], "fighters": fighters,
            "held": data.get("held", []), "justMissed": data.get("justMissed", [])}


def _same_ufc_promo(a: str, b: str) -> bool:
    """Two DWCS promotion names that score the same."""
    tier = getattr(dwcs, "get_promo_tier", None)
    return a == b or (tier is not None and tier(a)[1] == tier(b)[1])


def options() -> Dict:
    return {"divisions": [{"value": d, "label": division_label(d)} for d in DIVISIONS], "countries": countries(),
            "promotions": [{"id": p["id"], "name": p["name"]} for p in promotions()]}
