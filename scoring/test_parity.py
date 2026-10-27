"""The website's JavaScript must give the same score as the Python formulas.

static/ascent.js is a port of the Python, and static/ascent_tables.js is
generated from it. This test:
  1. checks the generated tables are up to date with the Python, and
  2. scores a few thousand input combinations in Python and in Node, and
     requires every pair to match to the published decimal place.

Needs Node.js on the PATH (skipped with a message if it is missing).

Run:  python scoring/test_parity.py     (or: pytest scoring)
"""
import itertools
import json
import os
import random
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

import export_tables                                 # noqa: E402
import one_ascent_v3_9 as one                        # noqa: E402
import dwcs_ascent_v3_0 as dwcs                      # noqa: E402

NODE_RUNNER = r"""
const A = require(process.argv[1]);
let buf = '';
process.stdin.on('data', d => buf += d);
process.stdin.on('end', () => {
  const cases = JSON.parse(buf);
  const out = cases.map(c => c.system === 'ONE' ? A.scoreONE(c.f).score : A.scoreDWCS(c.f).score);
  process.stdout.write(JSON.stringify(out));
});
"""


def make_cases(n=4000, seed=7):
    rnd = random.Random(seed)
    one_divs = [k for k in one.WC_AVG if "(" not in k] + ["Flyweight (125)", "Women's Strawweight (115)", "Catchweight"]
    dwcs_divs = list(dwcs.WC_FR_AVG) + ["catchweight"]
    one_promos = list(export_tables.PROMO_CODES) + ["Not_A_Promotion"]
    dwcs_promos = list(dwcs.PROMO_TIERS) + list(dwcs.PROMO_ALIASES) + ["Inka MMA", "559 Fights", "LFA Brazil"]
    countries = [c for c, r in one.COUNTRY_REGION.items() if r] + ["Atlantis"]
    cases = []
    # Hand-picked edges first: zero wins, ages on every band boundary, round-half cases.
    for wins, losses, age in itertools.product([0, 1, 4, 5], [0, 1, 2, 3], [None, "N/A", 22, 23, 24, 27, 28, 30, 31, 33, 34]):
        f = dict(wins=wins, losses=losses, draws=0, finishRate=0.0 if wins == 0 else 60.0,
                 weightClass="Lightweight", age=age, promotion="LFA", titleWins=0, country="Brazil")
        if wins + losses > 0:
            cases.append({"system": "ONE", "f": f})
    for _ in range(n):
        wins = rnd.randint(1, 30)
        losses = rnd.choice([0, 0, 0, 1, 1, 2, 3, 5, 9])
        draws = rnd.choice([0, 0, 0, 0, 1, 2])
        fin = rnd.randint(0, wins)
        fr = round(100.0 * fin / wins, 1)
        age = rnd.randint(18, 40)
        titles = rnd.choice([0, 0, 0, 1, 2, 3, 6])
        cases.append({"system": "ONE", "f": dict(
            wins=wins, losses=losses, draws=draws, finishRate=fr, weightClass=rnd.choice(one_divs),
            age=rnd.choice([age, age, age, None]), promotion=rnd.choice(one_promos), titleWins=titles,
            country=rnd.choice(countries))})
        cases.append({"system": "DWCS", "f": dict(
            wins=wins, losses=losses, draws=draws, finishRate=fr, weightClass=rnd.choice(dwcs_divs),
            age=age, promotion=rnd.choice(dwcs_promos), titleWins=titles,
            winStreak=rnd.randint(0, wins))})
    return cases


def python_score(c):
    f = c["f"]
    if c["system"] == "ONE":
        return one.ascent_v39(wins=f["wins"], losses=f["losses"], draws=f["draws"],
                              finish_rate_pct=f["finishRate"], weight_class=f["weightClass"],
                              age=f["age"], main_promotion=f["promotion"],
                              title_wins=f["titleWins"], country=f["country"])
    total = f["wins"] + f["losses"] + f["draws"]
    return dwcs.calculate(win_pct=100.0 * f["wins"] / total, fr_raw=f["finishRate"],
                          weight_class=f["weightClass"], win_streak=f["winStreak"],
                          losses=f["losses"], age=f["age"], title_fight_wins=f["titleWins"],
                          promotion=f["promotion"])["ascent_profile"]


def test_tables_are_generated_from_python():
    path = os.path.join(ROOT, "static", "ascent_tables.js")
    with open(path, encoding="utf-8") as fh:
        committed = fh.read()
    assert committed == export_tables.build(), "static/ascent_tables.js is stale: run python scoring/export_tables.py"


def test_js_matches_python():
    node = shutil.which("node")
    if not node:
        print("SKIP: node not found, JS parity not checked")
        return
    cases = make_cases()
    js_path = os.path.abspath(os.path.join(ROOT, "static", "ascent.js"))
    run = subprocess.run([node, "-e", NODE_RUNNER, js_path], input=json.dumps(cases),
                         capture_output=True, text=True, check=True)
    js = json.loads(run.stdout)
    mismatches = []
    for c, j in zip(cases, js):
        p = python_score(c)
        if abs(p - j) > 1e-9:
            mismatches.append((c, p, j))
    assert not mismatches, f"{len(mismatches)} of {len(cases)} differ, e.g. {mismatches[:3]}"
    print(f"JS parity: {len(cases)} cases, 0 differences")


if __name__ == "__main__":
    test_tables_are_generated_from_python()
    test_js_matches_python()
    print("OK - browser scoring matches the Python formulas")
