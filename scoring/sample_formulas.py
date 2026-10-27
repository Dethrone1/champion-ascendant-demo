"""Stand-in scoring formulas for the public repo.

The real ONE ASCENT and DWCS/UFC ASCENT formulas are private. This module has
the same interface (scoring/service.py imports it when the private files are
missing) so the site runs end to end, but its weights are simple placeholders
and its scores are NOT the ones published on championascendant.com.
"""
import math
from typing import Dict

# ---------------- ONE-style stand-in ----------------
FR_WEIGHT = 0.6
WR_WEIGHT = 0.2
PROMO_TABLE: Dict[str, tuple] = {
    "LFA": (8.0, "North America"), "Cage_Warriors": (6.0, "Western Europe"),
    "Pancrase": (6.0, "East Asia"), "Shooto": (6.0, "East Asia"), "CFFC": (4.0, "North America"),
    "UAEW": (4.0, "Middle East"), "Inka": (2.0, "South America"), "Unknown": (0.0, "Unknown"),
}
COUNTRY_REGION: Dict[str, str] = {
    "Brazil": "South America", "Peru": "South America", "Colombia": "South America", "Uruguay": "South America",
    "USA": "North America", "Canada": "North America", "Mexico": "North America",
    "Japan": "East Asia", "China": "East Asia", "South Korea": "East Asia",
    "Kazakhstan": "Central Asia", "Kyrgyzstan": "Central Asia", "Tajikistan": "Central Asia",
    "Russia": "Eastern Europe", "Poland": "Eastern Europe", "England": "Western Europe",
    "Ireland": "Western Europe", "Philippines": "Southeast Asia", "Thailand": "Southeast Asia",
    "Australia": "Oceania", "Nigeria": "Africa", "Turkey": "Middle East",
}


def ascent_v39(*, wins, losses, draws, finish_rate_pct, weight_class, age, main_promotion,
               title_wins=0, country="", breakdown=False):
    total = wins + losses + draws
    win_rate = round(100.0 * wins / total, 1) if total else 0.0
    fr_norm = min(100.0, finish_rate_pct)
    promo = PROMO_TABLE.get(main_promotion, (0.0, "Unknown"))[0]
    age_mod = 0.0 if not isinstance(age, int) else (2.0 if age <= 27 else -2.0 if age >= 32 else 0.0)
    title = 2.0 * (title_wins or 0)
    unbeaten = 3.0 if losses == 0 and wins >= 5 else 0.0
    origin = 2.0 if country in COUNTRY_REGION else 0.0
    score = round(max(0.0, fr_norm * FR_WEIGHT + win_rate * WR_WEIGHT + promo + origin + age_mod + title + unbeaten), 1)
    out = dict(score=score, win_rate=win_rate, fr_norm=fr_norm, promo_pts=promo, hq_bonus=0.0,
               origin_fit=origin, age_mod=age_mod, title_bonus=title, undefeated_bonus=unbeaten)
    return out if breakdown else score


# ---------------- DWCS/UFC-style stand-in ----------------
ANCHOR_SLOPE = 1.0
ANCHOR_INTERCEPT = 15.0
PROMO_TIERS: Dict[str, int] = {"LFA": 10, "Cage Warriors": 8, "Fury FC": 8, "CFFC": 6, "UAE Warriors": 6, "Lux Fight League": 3}


def get_promo_tier(promotion: str):
    pts = PROMO_TIERS.get((promotion or "").strip(), 2)
    return ("-", pts)


def calculate(win_pct, fr_raw, weight_class, win_streak, losses, age, title_fight_wins, promotion, **_):
    promo = get_promo_tier(promotion)[1]
    profile = {
        "fr": fr_raw * 0.4, "win_pct": win_pct * 0.05, "losses": 5.0 if losses <= 1 else 0.0,
        "streak": 2.0 * math.sqrt(max(0, win_streak)), "promo": float(promo),
        "age": 2.0 if 25 <= age <= 30 else 0.0, "title": 2.0 * (title_fight_wins or 0),
        "elite_finisher": 0.0, "hot_streak": 0.0,
    }
    display = ANCHOR_SLOPE * sum(profile.values()) + ANCHOR_INTERCEPT
    return {"ascent_profile": round(max(0.0, display), 1), "profile": profile}
