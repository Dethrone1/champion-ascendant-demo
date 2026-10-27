# Champion Ascendant

[![tests](https://github.com/Dethrone1/champion-ascendant-demo/actions/workflows/tests.yml/badge.svg)](https://github.com/Dethrone1/champion-ascendant-demo/actions/workflows/tests.yml)

**Live site:** [championascendant.com](https://championascendant.com)

An MMA analytics site that scores unsigned fighters against the record profile of fighters who actually got signed or invited. It covers two pathways, each with its own formula and its own data:

- **ONE ASCENT** (v3.9, in validation) benchmarks a fighter against ONE Championship's MMA signings since 2023.
- **DWCS ASCENT** (v3.0) benchmarks a fighter against Dana White's Contender Series invitees.

The two scores are never added, averaged or combined. Every score breaks down into its parts, and every published score is recomputed by tests on every commit.

![Homepage](static/home.png)

## What's in it

| Page | What it does |
|---|---|
| Calculator | Enter a pro record and get both scores, each broken into its parts |
| Board | Unsigned fighters scoring 85+ on both systems, with filters, sorting, CSV export and per-fighter breakdowns |
| Off the Board | Where board fighters ended up, Contender Series Season 10 results, and a public corrections log |
| Method | The formulas, how they were validated, what broke, and what they don't claim |
| How it's built | Architecture, tests and validation, for engineering reviewers |

![Board with a fighter's breakdown open](static/both-systems.png)

## How it fits together

```
scoring/one_ascent_v3_9.py     ONE ASCENT (public copy: promotion points, not the signing data behind them)
scoring/dwcs_ascent_v3_0.py    DWCS ASCENT
scoring/export_tables.py  -->  static/ascent_tables.js   (generated, never hand-edited)
static/ascent.js               Same formulas in the browser (calculator + board)
static/both_systems.json       Board inputs and the published scores
app.py                         Flask routes; deploys to Railway from GitHub
```

The Python decides every score. The browser reads lookup tables generated from the Python, so the site can't carry a second hand-copied version of any rule. The ONE file here is generated from a private master copy that also holds the signing data; a test in the private repo checks the two score identically.

## Tests

```
pytest scoring tests
```

| Test | Checks |
|---|---|
| `scoring/test_both_systems.py` | Every score on the board reproduces from its inputs; everyone still clears 85; board rules hold |
| `scoring/test_parity.py` | The browser code matches the Python on 8,165 generated inputs, exactly, including Python's rounding; generated tables are current |
| `tests/test_app.py` | Pages and data serve, old URLs redirect, no page shows raw code as text |

GitHub Actions runs all of them on every push and pull request. `test_parity.py` needs Node.js.

## What I learned building it

- **Pick the right outcome to validate against.** The DWCS score targets *getting invited*, not *winning a contract*. Win streak looked like the strongest signal until I tested it against invites, where it scored below chance (AUC 0.485) while finish rate scored 0.637. Rebuilding around the right target took the formula from AUC 0.628 (v2.8.5) to 0.686 (v3.0).
- **Retrodiction is not prediction.** Scoring a fighter after their booking is public proves nothing. Season 10 is logged as tracking, and the site says the number of clean prospective calls is zero.
- **No silent edits.** Every change to a published number is logged with a date, including a calculator bug that shipped and was caught.
- **Know your data's limits.** There's no control group of fighters who were looked at and passed over, so the scores describe what signees and invitees look like. They don't claim to predict who gets signed.

## Run locally

```
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000

## Stack

Python, Flask, vanilla JavaScript, HTML and CSS, GitHub Actions, Railway. Data work in Excel and Python (pandas, openpyxl). Fighter records cross-checked against Tapology and Sherdog.

## Credits

Conceived and directed by me, built using AI tools.
