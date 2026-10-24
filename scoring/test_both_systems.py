"""Reproduces every score on the live Both Systems page (24 Oct 2026).

Run:  python scoring/test_both_systems.py     (or: pytest scoring)
ONE and DWCS are scored by separate formulas and never combined.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from one_ascent_v3_8_1 import ascent_v381          # noqa: E402
from dwcs_ascent_v3_0 import calculate as dwcs_v30  # noqa: E402

# name, W, L, D, finish rate %, weight class, win streak, age, title wins,
# ONE promo code, DWCS promotion, country, expected ONE, expected DWCS
FIGHTERS = [
    ("Gian Maurente",      9, 2, 0, 100.0, "Lightweight",          5, 23, 2, "LFA",           "LFA",              "Uruguay",    98.1, 96.5),
    ("Eduardo Dutra",      9, 0, 0,  88.9, "Featherweight",        9, 22, 0, "LFA",           "LFA",              "Brazil",     97.2, 95.1),
    ("Wendrio Chaves",     6, 0, 0, 100.0, "Flyweight",            6, 21, 0, "LFA",           "LFA",              "Brazil",    102.5, 96.4),
    ("Thalyta Silva",      5, 0, 0,  80.0, "Women's Bantamweight", 5, 27, 0, "LFA",           "LFA",              "Brazil",     94.4, 93.6),
    ("Gabi McComb",        5, 0, 0, 100.0, "Women's Flyweight",    5, 29, 1, "Unknown",       "559 Fights",       "Brazil",     93.1, 92.2),
    ("Kevin Navarro",     12, 0, 0, 100.0, "Bantamweight",        12, 27, 0, "Inka",          "Inka MMA",         "Peru",       90.6, 97.3),
    ("Kaisar Zhaugashar",  8, 0, 0, 100.0, "Bantamweight",         8, 22, 0, "OLMMA",         "Octagon",          "Kazakhstan", 90.6, 91.4),
    ("Qosim Sardorov",     7, 0, 0, 100.0, "Middleweight",         7, 25, 0, "Pancrase",      "Pancrase",         "Tajikistan", 89.3, 85.9),
    ("Ullubiy Amirzhanov", 7, 0, 0, 100.0, "Bantamweight",         7, 23, 0, "UAEW",          "UAE Warriors",     "Russia",     86.9, 95.0),
    ("Nicolas Bojaca",     6, 0, 0, 100.0, "Flyweight",            6, 28, 0, "Unknown",       "Lux Fight League", "Colombia",   86.5, 91.9),
    ("Busurman Zhumagul",  5, 0, 0, 100.0, "Welterweight",         5, 21, 1, "CFFC",          "CFFC",             "Kyrgyzstan", 87.1, 87.8),
]


def test_both_systems():
    for (name, w, l, d, fr, wc, ws, age, tw, one_p, dw_p, country, exp_one, exp_dw) in FIGHTERS:
        one = ascent_v381(wins=w, losses=l, draws=d, finish_rate_pct=fr, weight_class=wc,
                          age=age, main_promotion=one_p, title_wins=tw, country=country)
        dw = dwcs_v30(win_pct=100.0 * w / (w + l + d), fr_raw=fr, weight_class=wc,
                      win_streak=ws, losses=l, age=age, title_fight_wins=tw,
                      promotion=dw_p)["ascent_profile"]
        assert abs(one - exp_one) < 0.05, f"{name}: ONE {one} != {exp_one}"
        assert abs(dw - exp_dw) < 0.05, f"{name}: DWCS {dw} != {exp_dw}"
        assert one >= 85 and dw >= 85, f"{name} no longer clears 85 on both"


if __name__ == "__main__":
    test_both_systems()
    print(f"OK - {len(FIGHTERS)} fighters reproduce on both systems")
