# Champion Ascendant

**Live site:** [championascendant.com](https://championascendant.com)

An MMA analytics site that scores unsigned fighters against the measured profile of fighters who actually got signed or invited. It covers two pathways, each with its own formula and its own dataset:

- **ONE ASCENT Score:** benchmarks a fighter against ONE Championship signings since 2023.
- **DWCS ASCENT Score:** benchmarks a fighter against Dana White's Contender Series invitees.

The two scores are never added, averaged, or combined. The **Both Systems** page lists the fighters who score 85 or higher on both.

![Both Systems page](static/both-systems.png)

## What I learned building it

- **Pick the right outcome to validate against.** The DWCS score targets *getting invited*, not *winning a contract*. Win streak looked like the strongest signal until I tested it against invites instead of contracts. Against invites it scored below chance (AUC 0.485), while finish rate scored 0.637. Rebuilding around the correct target took the model from AUC 0.628 (v2.8.5) to 0.686 (v3.0).
- **Retrodiction is not prediction.** Scoring a fighter after their invite is announced proves nothing. I pre-registered DWCS Season 10 predictions before the season started and log hits and misses publicly on the site's Off the Board page.
- **No silent edits.** Every correction to a published score is logged on the site.
- **Know your data's limits.** There is no control group of fighters who were never invited, so the DWCS score describes what invitees look like. It does not claim to predict who gets invited.

## Scoring code

Both formulas are in [`scoring/`](scoring/) and run without the website.

| File | What it is |
|---|---|
| `one_ascent_v3_8_1.py` | ONE ASCENT v3.8.1 (in validation) |
| `dwcs_ascent_v3_0.py` | DWCS ASCENT v3.0 (live) |
| `test_both_systems.py` | Reproduces the scores published on the Both Systems page |

```
python scoring/test_both_systems.py
```

Core ideas used in both formulas:
- **Finish rate normalized by weight class.** Heavyweights finish more often than flyweights, so raw finish rate is compared to each division's global average (FightMatrix data).
- **Shrinkage for small samples (ONE).** A 3-0 fighter's finish rate is pulled toward the division average until they have more fights.
- **Promotion and region weights derived from real signing shares**, not hand-picked.

## Stack

- Python / Flask, serving static HTML pages
- HTML, CSS, vanilla JavaScript (the calculator runs in the browser)
- Hosted on Railway, deployed automatically from GitHub
- Data work in Excel and Python (pandas, openpyxl); fighter records cross-checked against Tapology and Sherdog

## Structure

```
app.py                 Flask routes (/page and /page.html)
templates/
  index.html           Calculator
  both.html            Both Systems board
  receipts.html        Off the Board: public prediction and correction log
  methodology.html     How each formula works
scoring/               Standalone scoring formulas and tests
static/                Images
```

## Run locally

```
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000

## Credits

Conceived and directed by me, built using AI tools.
