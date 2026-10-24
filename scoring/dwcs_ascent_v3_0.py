"""
DWCS ASCENT Profile v3.0
======================
Benchmarks an unsigned fighter against the measured profile of Dana White's
Contender Series invitees.

TARGET: invitation likelihood. Not fight outcome, not contract.

WHAT CHANGED FROM v2.8.5 AND WHY
--------------------------------
1. Split into PROFILE + CONTEXT. Profile is the tested core (everything v2.8.5
   had, cleaned). Context holds new, untested variables. They are reported
   separately so a bad Context variable can never quietly corrupt the board,
   and so the Profile-only score stays comparable to v2.8.5.

2. PERFECT_FINISHER_BONUS deleted. It could never fire independently:
   FR_raw=100 implies FR_norm >= 100/80.6*70.9 = 88.0, which is always above
   the 85 Elite threshold. It was a hardcoded +3 to a subset of Elite.

3. FR normalization no longer clamps at 100. Ratio now caps at 1.55
   (FR_norm ceiling ~110) and the component divides by that ceiling, so 45 is
   still the max but ordering survives at the top of the board.

4. Win% weight 15 -> 6. Every invitee wins; a continuous percentage cannot
   separate a population selected on winning. Freed weight moves to LOSS_BAND.

5. LOSS_BAND replaces UNDEFEATED_BONUS. Invitee share: 0L and 1L are near-equal;
   2L falls off a cliff. The data puts the step between 1 and 2 losses.

6. Streak weight NOT raised. Against INVITE - the actual target - streak scores
   AUC 0.485, below chance, while finish rate scores 0.637. Weights for an
   invitation-profile score must be justified against invitation data.

7. Age collapsed to three bands. Invite-share says older, outcome says younger.
   When two signals disagree, near-flat is the honest answer.

8. Title bonus tier-scaled and concave, still uncapped.

9. Score is NOT capped. 100 is anchored to the ceiling of an invitee-quality
   field, in the manner of OPS+ or passer rating.

10. STREAK_CAP removed. Padding is already discounted by PROMO_TIERS, and sqrt
    already flattens the curve.

RESULT: invite AUC 0.686 (v3.0) vs 0.628 (v2.8.5).

KNOWN LIMITATIONS - READ BEFORE PUBLISHING ANY CLAIM
----------------------------------------------------
* There is no non-invitee control group. PROMO_TIERS is calibrated on invitees
  only, so it measures "what invitees look like", not "what predicts an invite".
* The CONTEXT block is UNTESTED. Defaults are neutral.
* Supportable public claim: "benchmarks a fighter against the measured profile
  of DWCS invitees." NOT "predicts who gets invited."

Author: Champion Ascendant
Version: 3.0
"""

import math
from typing import Dict, Optional, Tuple

# =============================================================================
# PROFILE WEIGHTS
# =============================================================================
FR_WEIGHT      = 45.0   # finish rate, weight-class normalized
WIN_WEIGHT     = 6.0    # was 15.0 - see change note 4
STREAK_MULT    = 1.0    # v2.8.5 level - see change note 6
PROMO_CAP      = 15
ELITE_FINISHER_BONUS = 4.0
HOT_STREAK_BONUS     = 3.0
HOT_STREAK_THRESHOLD = 7

# Loss bands (replaces UNDEFEATED_BONUS). See change note 5.
LOSS_BAND = {0: 8.0, 1: 7.0, 2: 2.0}
LOSS_BAND_DEFAULT = 0.0

# =============================================================================
# WEIGHT CLASS FINISH RATE AVERAGES
# SOURCE: FightMatrix global MMA finish rates (retrieved Apr 2026), ~262,000 fights.
# =============================================================================
WC_FR_AVG = {
    "heavyweight": 80.6, "light heavyweight": 77.5, "middleweight": 75.6,
    "welterweight": 73.4, "lightweight": 70.6, "featherweight": 68.8,
    "bantamweight": 66.9, "flyweight": 64.3, "strawweight": 62.6,
    "women's featherweight": 65.5, "women's bantamweight": 62.7,
    "women's flyweight": 59.2, "women's strawweight": 55.0,
    "women's atomweight": 51.5,
}
OVERALL_FR_AVG = 70.9
FR_RATIO_CAP = 1.55                     # see change note 3

# =============================================================================
# SCALE ANCHOR - a stated calibration choice, not a measured probability.
# Two-point linear map fitted on the pooled S9 + S10 invitee field:
#   raw median (63.73) -> 78 ; raw 97th percentile (87.90) -> 100
# Rescaling changes no rankings. It is a change of units, like C to F.
# =============================================================================
ANCHOR_SLOPE = 0.9104
ANCHOR_INTERCEPT = 19.9752
FR_NORM_CEILING = FR_RATIO_CAP * OVERALL_FR_AVG   # 109.9

# =============================================================================
# PROMOTION TIERS - share of Season 9 verified invitees.
# Bands: >=15% -> 15 | 6-15% -> 11 | 3-6% -> 8 | 2-3% -> 6 | listed <2% -> 4
#        unlisted -> 3
# =============================================================================
UNLISTED_DEFAULT = 3
PROMO_TIERS = {
    'LFA': 15,
    'Fury FC': 11, 'Cage Warriors': 11,
    'CFFC': 8, 'Ares FC': 8, 'UAE Warriors': 8,
    'Octagon': 6, 'PFL': 6, 'Jungle Fight': 6, 'Combate Global': 6,
    'Tuff-N-Uff': 6, 'Brave FC': 6, 'Brave CF': 6, 'HEX Fight Series': 6, 'FCC': 6,
    'Invicta FC': 4, 'Shooto Brasil': 4, 'FNC': 4, 'Samourai MMA': 4,
    'Eternal MMA': 4, 'XFC': 4, 'Lux Fight League': 4, 'CES': 4,
    'Ring of Combat': 4, 'Titan FC': 4, 'Shooto': 4, 'RIZIN': 4, 'KSW': 4,
    'ACA': 4, 'AMC Fight Nights': 4, 'Babilon MMA': 4, 'BFL': 4,
    'Flex Fights': 4, 'Fury Challenger Series': 4, 'Unified MMA': 4,
    'Island Fights': 4, 'MMA Mexico Fight Night': 4, 'OKTAGON MMA': 4,
}

# Naming aliases only - no promotion is re-tiered here.
PROMO_ALIASES = {
    'Fury_FC': 'Fury FC', 'Fury': 'Fury FC', 'Ares_FC': 'Ares FC',
    'LUX': 'Lux Fight League', 'Lux Fighting League': 'Lux Fight League',
    'Cage_Warriors': 'Cage Warriors', 'Shooto_Brasil': 'Shooto Brasil',
    'OKTAGON': 'OKTAGON MMA', 'Oktagon MMA': 'OKTAGON MMA',
    'Legacy Fighting Alliance': 'LFA',
}

# Availability is a flag, not a gate: the score measures the fighter, not the market.
UNAVAILABLE_PROMOTIONS = {'UFC', 'ONE', 'ONE Championship'}

# Soft flag: a reigning champion at a promotion that pays may not take a DWCS slot.
ANCHOR_RISK_PROMOTIONS = {'KSW', 'ACA', 'RIZIN', 'Brave CF', 'PFL', 'OKTAGON MMA'}


def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def resolve_promotion(promotion: str) -> str:
    p = (promotion or "").strip()
    return PROMO_ALIASES.get(p, p)


def _tier_letter(pts: int) -> str:
    return 'S' if pts >= 15 else 'A' if pts >= 11 else 'B' if pts >= 8 else 'C' if pts >= 6 else 'D' if pts >= 4 else 'E'


def get_promo_tier(promotion: str) -> Tuple[str, int]:
    """Exact match first, then longest-substring. Add an alias rather than
    relying on substring matching for any new promotion."""
    promo = resolve_promotion(promotion)
    up = promo.upper()
    for key, pts in PROMO_TIERS.items():
        if key.upper() == up:
            return (_tier_letter(pts), pts)
    best_key, best_pts = None, 0
    for key, pts in PROMO_TIERS.items():
        ku = key.upper()
        if ku in up and (best_key is None or len(ku) > len(best_key)):
            best_key, best_pts = ku, pts
    if best_key:
        return (_tier_letter(best_pts), best_pts)
    return ('E', UNLISTED_DEFAULT)


def normalize_finish_rate(fr_raw: float, weight_class: str) -> float:
    """Finish rate relative to divisional average, rescaled to the global mean.
    Ratio capped at FR_RATIO_CAP so ordering survives above 100."""
    avg = WC_FR_AVG.get((weight_class or "").strip().lower(), OVERALL_FR_AVG)
    return min(fr_raw / avg, FR_RATIO_CAP) * OVERALL_FR_AVG


def streak_bonus(win_streak: int) -> float:
    s = max(0, int(win_streak))
    if s == 0:
        return 0.0
    return max(0.0, (5.5 * math.sqrt(s) - 4.5) * STREAK_MULT)


def loss_bonus(losses: int) -> float:
    return LOSS_BAND.get(max(0, int(losses)), LOSS_BAND_DEFAULT)


AGE_CORE_BONUS   =  3.0   # ages 26-29
AGE_WINDOW_BONUS =  0.0   # ages 23-25 and 30-31
AGE_TAIL_PENALTY = -3.0   # under 23, over 31


def age_modifier(age: int) -> float:
    """Smooth, monotonic, three bands. Shape matters more than magnitude:
    invite AUC is flat (0.673-0.677) across spreads of 4 to 12 points."""
    if 26 <= age <= 29:
        return AGE_CORE_BONUS
    if 23 <= age <= 31:
        return AGE_WINDOW_BONUS
    return AGE_TAIL_PENALTY


def title_bonus(title_fight_wins: int, promo_pts: int) -> float:
    """Uncapped, concave, continuous in promotion tier."""
    t = max(0, int(title_fight_wins))
    if t == 0:
        return 0.0
    return (1.5 + promo_pts / 3.0) * math.sqrt(t)


# =============================================================================
# CONTEXT BLOCK - UNTESTED. All defaults neutral. Reported separately.
# =============================================================================
def activity_modifier(months_since_last_fight: Optional[float]) -> float:
    if months_since_last_fight is None:
        return 0.0
    m = float(months_since_last_fight)
    if m <= 9:   return 0.0
    if m <= 15:  return -3.0
    if m <= 24:  return -8.0
    return -15.0


def division_demand_modifier(demand_index: Optional[float]) -> float:
    if demand_index is None:
        return 0.0
    return clamp(3.0 * math.log(max(demand_index, 0.25)), -3.0, 3.0)


def management_modifier(prior_dwcs_placements: Optional[int]) -> float:
    if prior_dwcs_placements is None:
        return 0.0
    n = int(prior_dwcs_placements)
    return 0.0 if n == 0 else min(2.0 * math.sqrt(n), 6.0)


# =============================================================================
# MAIN
# =============================================================================
def calculate(win_pct: float, fr_raw: float, weight_class: str, win_streak: int,
              losses: int, age: int, title_fight_wins: int, promotion: str,
              contracted_to: Optional[str] = None,
              months_since_last_fight: Optional[float] = None,
              division_demand: Optional[float] = None,
              manager_prior_placements: Optional[int] = None) -> Dict:

    available = not contracted_to or (contracted_to or "").strip() not in UNAVAILABLE_PROMOTIONS
    promo_resolved = resolve_promotion(promotion)
    anchor_risk = (promo_resolved in ANCHOR_RISK_PROMOTIONS and int(title_fight_wins) > 0)

    fr_norm = normalize_finish_rate(fr_raw, weight_class)
    tier, promo_pts = get_promo_tier(promotion)

    profile = {
        'fr':      fr_norm / FR_NORM_CEILING * FR_WEIGHT,
        'win_pct': win_pct / 100.0 * WIN_WEIGHT,
        'losses':  loss_bonus(losses),
        'streak':  streak_bonus(win_streak),
        'promo':   float(promo_pts),
        'age':     age_modifier(age),
        'title':   title_bonus(title_fight_wins, promo_pts),
        'elite_finisher': ELITE_FINISHER_BONUS if fr_norm >= 85.0 else 0.0,
        'hot_streak':     HOT_STREAK_BONUS if int(win_streak) >= HOT_STREAK_THRESHOLD else 0.0,
    }
    context = {
        'activity':   activity_modifier(months_since_last_fight),
        'demand':     division_demand_modifier(division_demand),
        'management': management_modifier(manager_prior_placements),
    }

    profile_raw = sum(profile.values())
    display = ANCHOR_SLOPE * profile_raw + ANCHOR_INTERCEPT

    return {
        'ascent_profile': round(max(0.0, display), 1),
        'context_adjustment': round(sum(context.values()), 1),
        'experimental_total': round(max(0.0, display + sum(context.values())), 1),
        'available': available,
        'anchor_risk_flag': anchor_risk,
        'fr_normalized': round(fr_norm, 1),
        'promo_tier': tier,
        'profile': {k: round(v, 2) for k, v in profile.items()},
        'context': {k: round(v, 2) for k, v in context.items()},
    }


if __name__ == "__main__":
    # Eduardo Dutra, 9-0, 8 finishes, featherweight, LFA, age 22 (24 Oct 2026)
    r = calculate(win_pct=100.0, fr_raw=88.9, weight_class="featherweight", win_streak=9,
                  losses=0, age=22, title_fight_wins=0, promotion="LFA")
    print("Eduardo Dutra  DWCS ASCENT v3.0 =", r['ascent_profile'])
