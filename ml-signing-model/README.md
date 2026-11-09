# DWCS/UFC Ascent: can a fight record predict a UFC call-up?

**Fighters a machine-learning model ranks in its top 20% got a DWCS/UFC call-up 51% of the time. In its bottom 20%, it was 6%.**
From the fight record alone (no film, no management, no opponent data), a learned model ranks prospects better than a rule of thumb and slightly better than my hand-built scouting score, but record-only prediction tops out at around 0.70 AUC.

![AUC comparison](charts/1_auc_comparison.png)

## The question
Every year, hundreds of regional fighters headline cards at feeder promotions like LFA, Cage Warriors and Fury FC. A few get a call from Dana White's Contender Series or the UFC. **How much of that call is visible in the fight record?**

## The data
- **172 fighters** who fought on LFA, Cage Warriors, Fury FC, UAE Warriors, Brave CF and OKTAGON cards in 2024–25. **54 (31%)** later appeared on DWCS, in the UFC, on TUF or on Road to UFC (through 31 Oct 2026).
- **Every record was hand-verified.** Each fighter's full Sherdog fight list was counted bout by bout in code, and conflicts were settled with Tapology, promotion sites and press releases. Along the way this caught a cancelled bout, records missing up to 8 wins, and several fighters whose listed fight was actually amateur.
- **No future data leaks in.** Every stat is taken *before* the fighter's listed regional bout, never after.
- Dataset: [`dwcs_prospects_172.csv`](dwcs_prospects_172.csv)

## Results
| Approach | AUC | 95% range |
|---|---|---|
| Coin flip | 0.50 | — |
| Rule of thumb (undefeated + age ≤ 27 + finishes 60%+) | 0.67 | 0.58–0.75 |
| Ascent score (hand-built scouting formula) | 0.68 | 0.60–0.76 |
| **Logistic regression (learned)** | **0.70** | 0.62–0.78 |

*AUC = the chance the model ranks a randomly chosen signed fighter above a randomly chosen unsigned one. Out-of-fold, 5-fold cross-validation repeated 20×.*

![Signed rate by model score](charts/2_signed_rate_by_score.png)

### What the model learned
Win % and youth matter most. Once win % is known, finish rate adds almost nothing, and a long win streak counts slightly *against* a fighter (long streaks often come against weaker regional opposition).

![Model weights](charts/3_model_weights.png)

### Learned model vs hand-built score
The two scores agree only moderately (rank correlation 0.54; 15 of their top 30 overlap), but both find about 15–16 signees in their top 30, versus about 9 by chance. They disagree in a telling way: the hand-built score rewards **high-finish-rate veterans** (e.g. 18-9 knockout artists), while the learned model prefers **young fighters with few losses** Neither side clearly wins those disagreements in this sample, which suggests combining them is worth testing.

![Ascent vs model](charts/4_ascent_vs_model.png)

### Adding an AI-extracted feature: gym / team
Records miss a lot, so I added one feature a record can't show: **where the fighter trains**. Each fighter's gym (from Sherdog) was classified by a language model (Claude, fixed rubric, [`extract_gym_tier.py`](extract_gym_tier.py)) as **elite** (e.g. American Top Team, Kill Cliff, Xtreme Couture), **established** or **regional**.

![Gym tier](charts/5_gym_tier.png)

| Model | AUC |
|---|---|
| Record only | 0.70 |
| Record + elite gym (AI-classified) | 0.70 |

**It didn't help.** Elite-camp fighters were signed a bit more often (42% vs 34%), but once the record is in the model, gym tier adds nothing, perhaps because elite camps mostly take fighters who already have strong records. One trap I caught: "no gym listed" looks hugely predictive (0 of 11 signed), but that's probably **leakage**. Sherdog profiles get filled in *after* a fighter is signed, so a blank field partly reflects the outcome. I left it out.

## Limits (read before quoting a number)
- **Small sample.** 172 fighters; the 95% ranges overlap, so no approach is *proven* better than another.
- **Uneven follow-up time.** 2024 fighters had about 2 years to get the call, late-2025 fighters about 1. Some current "not signed" fighters will be signed later.
- **Record-only inputs.** Opponent quality, management, weight-class needs and market fit all drive signings, and none of them is in here.
- **Win streak and win % overlap**, so read individual model weights for direction, not exact size.
- Gym affiliation is the *current* one, not as of the snapshot date; a few fighters may have moved camps after signing.
- The Ascent score was partly calibrated on DWCS rosters that overlap with some fighters here, and it uses promotion tier, which the model doesn't. Its formula is not published.

## Next
Add opponent quality (the strongest signal still missing): the records of the fighters each prospect beat, and test the model *out of time*: train on 2024, predict 2025.

## Run it
```
pip install -r requirements.txt
jupyter notebook dwcs_ascent_ml.ipynb   # full analysis + charts
python retrain.py                       # retrain the model in one command
```

## Keeping it current
The model doesn't change on its own. It **retrains with one command** when new outcomes come in:
1. Re-check "not signed" fighters after each DWCS season and flip any who got the call (0 → 1).
2. Add new verified fighters (stats as of their snapshot bout).
3. Run `python retrain.py`. Each run is logged in [`retrain_log.csv`](retrain_log.csv) and compared with the last kept model. If accuracy drops by more than 0.02, the new model is **not** saved, so bad data can't silently make it worse.

Part of [Champion Ascendant](https://championascendant.com).
