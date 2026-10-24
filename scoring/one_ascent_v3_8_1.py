"""
ONE ASCENT v3.8.1 (in validation)
=================================
Benchmarks an unsigned fighter against the measured profile of fighters ONE
Championship signed from 2023 onward. Targets signing potential, not results
after signing.

v3.8 base: finish-rate shrinkage (k=5 pseudo-fights at the division average),
per-win weight-class averages, global anchor 73.0,
Base80 = 0.65 * FR_norm + 0.15 * WinRate, plus promotion points, origin fit,
age modifier and title bonus.

v3.8.1 changes:
  1. HQ bonus recalibrated by share of ONE MMA signings since 2023:
     >=15% -> 2, >=10% -> 1, >=5% -> 0.5, <5% -> 0
  2. Undefeated bonus: +5 if 0 losses and at least 5 wins.
  3. Uncapped: floored at 0, no longer capped at 100.

Lookup tables below are exported from the ONE ASCENT master workbook.
Author: Champion Ascendant
"""
from __future__ import annotations
from typing import Optional, Dict, Any

FR_WEIGHT = 0.65
WR_WEIGHT = 0.15
GLOBAL_FR_AVG = 73.0
FR_NORM_CEILING = 100.0
SCORE_FLOOR = 0.0
UNDEFEATED_BONUS = 5.0
UNDEFEATED_MIN_WINS = 5
UNKNOWN_ORIGIN = 2.0
SHRINK_K = 5.0
AGE_BANDS = [(23, 3.0), (27, 2.0), (30, 0.0), (33, -2.0)]
AGE_OLDER = -4.0
TITLE_BASE = 3.0
TITLE_PER_WIN = 1.0

# Weight-class finish-rate averages, per WIN (FightMatrix)
WC_AVG = {
    "heavyweight": 83.6, "light heavyweight": 79.8, "middleweight": 77.9,
    "welterweight": 75.5, "lightweight": 72.8, "featherweight": 70.9,
    "bantamweight": 68.9, "flyweight": 66.4, "strawweight": 66.1,
    "women's featherweight": 67.2, "women's bantamweight": 63.9,
    "women's flyweight": 60.2, "women's strawweight": 55.9,
    "women's atomweight": 52.4, "atomweight": 52.4,
}

# Promotion HQ region bonus (v3.8.1 share rule)
HQ_BONUS = {
    'Africa': 0,
    'Caucasus': 0,
    'Central Asia': 1,
    'East Asia': 2,
    'Eastern Europe': 0.5,
    'Middle East': 0,
    'North America': 1,
    'Oceania': 0,
    'South America': 1,
    'South Asia': 0,
    'Southeast Asia': 2,
    'Unknown': 0,
    'Western Europe': 0,
}

# Fighter origin-region fit
ORIGIN_FIT = {
    'Africa': 2,
    'Caucasus': 2,
    'Central Asia': 4,
    'East Asia': 6,
    'Eastern Europe': 4,
    'Middle East': 4,
    'North America': 4,
    'Oceania': 2,
    'South America': 6,
    'South Asia': 2,
    'Southeast Asia': 2,
    'Unknown': 2,
    'Western Europe': 2,
}

# Promotion code -> (base points, HQ region)
PROMOTIONS = {
    'ACA': (4.0, 'Eastern Europe'),
    'AMC_Fight_Nights': (2.0, 'Eastern Europe'),
    'ARES_FC': (2.0, 'Western Europe'),
    'Attitude MMA': (0.0, 'North America'),
    'Attitude_MMA': (2.0, 'North America'),
    'BFL': (0.0, 'North America'),
    'BRAVE_CF': (2.0, 'Middle East'),
    'CFC': (0.0, 'Africa'),
    'CFFC': (0.0, 'North America'),
    'CFN': (0.0, 'Southeast Asia'),
    'Cage_Warriors': (2.0, 'Western Europe'),
    'Clearwater_Combat': (0.0, 'North America'),
    'Combate_Global': (2.0, 'North America'),
    'Core_FC': (0.0, 'Middle East'),
    'DEEP': (2.0, 'East Asia'),
    'EFC': (0.0, 'Central Asia'),
    'EFCA': (2.0, 'Africa'),
    'EMMA': (0.0, 'Oceania'),
    'Eagle_FC': (2.0, 'Caucasus'),
    'Ermak': (0.0, 'Africa'),
    'Eternal_MMA': (2.0, 'Oceania'),
    'FNC': (0.0, 'Eastern Europe'),
    'FNG': (2.0, 'Eastern Europe'),
    'Fury_FC': (0.0, 'North America'),
    'Fusion_FC': (0.0, 'South America'),
    'GFC': (0.0, 'Eastern Europe'),
    'GTC': (2.0, 'Eastern Europe'),
    'Grachan': (0.0, 'East Asia'),
    'HCMMA': (0.0, 'Eastern Europe'),
    'Hardcore_MMA': (2.0, 'Eastern Europe'),
    'Heat': (2.0, 'East Asia'),
    'Hex': (0.0, 'Oceania'),
    'Hex_Fight_Series': (0.0, 'Oceania'),
    'IMMAF': (0.0, 'Unknown'),
    'JCK': (0.0, 'East Asia'),
    'JFC': (0.0, 'South America'),
    'Jungle_Fight': (0.0, 'South America'),
    'KSW': (2.0, 'Eastern Europe'),
    'Khan_Fight': (2.0, 'Middle East'),
    'Kunlun_Fight': (2.0, 'East Asia'),
    'LFA': (12.0, 'North America'),
    'Longsan_Fight': (0.0, 'East Asia'),
    'MFN': (0.0, 'South Asia'),
    'MMATC': (0.0, 'Western Europe'),
    'MMA_Sanda_Combat': (2.0, 'South America'),
    'MMA_Series': (2.0, 'Eastern Europe'),
    'Magic_Arena': (2.0, 'South America'),
    'Mr. Cage': (0.0, 'South America'),
    'NAFC': (0.0, 'Central Asia'),
    'NFC': (2.0, 'Central Asia'),
    'Naiza_FC': (2.0, 'Central Asia'),
    'OKMMA': (0.0, 'Western Europe'),
    'OLMMA': (2.0, 'Central Asia'),
    'ONE_Friday_Fights': (12.0, 'Southeast Asia'),
    'ONE_Warrior_Series': (2.0, 'Southeast Asia'),
    'One_Pride_MMA': (0.0, 'Southeast Asia'),
    'Pancrase': (6.0, 'East Asia'),
    'Peak_Fighting': (2.0, 'North America'),
    'RCC': (0.0, 'Eastern Europe'),
    'RIZIN': (2.0, 'East Asia'),
    'RUF': (0.0, 'North America'),
    'Rizen_FC': (0.0, 'East Asia'),
    'Road_FC': (2.0, 'East Asia'),
    'Road_To_UFC': (0.0, 'North America'),
    'SFH': (2.0, 'South America'),
    'SFL': (2.0, 'Oceania'),
    'SFS': (0.0, 'Middle East'),
    'SFT': (0.0, 'South America'),
    'SOMA': (0.0, 'Southeast Asia'),
    'Shooto': (4.0, 'East Asia'),
    'Shooto_Brasil': (0.0, 'South America'),
    'Shooto_Brazil': (2.0, 'South America'),
    'TFC': (0.0, 'East Asia'),
    'TTF': (0.0, 'East Asia'),
    'UAEW': (0.0, 'Middle East'),
    'UFC': (2.0, 'North America'),
    'UMMA': (0.0, 'North America'),
    'Unknown': (0.0, 'Unknown'),
    'Venum_Fight': (0.0, 'Middle East'),
    'WEF': (2.0, 'Central Asia'),
    'WOW': (0.0, 'Western Europe'),
    'Wu_Lin_Feng': (0.0, 'East Asia'),
    'ZFL': (0.0, 'Southeast Asia'),
    '^ add new promotions ABOVE this line; roster lookup formulas currently extend through row 100': (0.0, None),
}

# Country -> origin region
COUNTRY_REGION = {
    'Afghanistan': 'South Asia',
    'Algeria': 'Africa',
    'American': 'North America',
    'Angola': 'Africa',
    'Argentina': 'South America',
    'Argentine': 'South America',
    'Armenia': 'Caucasus',
    'Armenian': 'Caucasus',
    'Australia': 'Oceania',
    'Australian': 'Oceania',
    'Austria': 'Western Europe',
    'Azerbaijan': 'Caucasus',
    'Azerbaijani': 'Caucasus',
    'Bahrain': 'Middle East',
    'Bangladesh': 'South Asia',
    'Belarus': 'Eastern Europe',
    'Belgium': 'Western Europe',
    'Bolivia': 'South America',
    'Bosnia and Herzegovina': 'Eastern Europe',
    'Bosnia and Herzegovnia': 'Eastern Europe',
    'Brazil': 'South America',
    'Brazilian': 'South America',
    'British': 'Western Europe',
    'Brunei': 'Southeast Asia',
    'Bulgaria': 'Eastern Europe',
    'Cambodia': 'Southeast Asia',
    'Cameroon': 'Africa',
    'Canada': 'North America',
    'Canadian': 'North America',
    'Chile': 'South America',
    'China': 'East Asia',
    'Colombia': 'South America',
    'Croatia': 'Eastern Europe',
    'Czech Republic': 'Eastern Europe',
    'Czechia': 'Eastern Europe',
    'DR Congo': 'Africa',
    'Democratic Republic of Congo': 'Africa',
    'Denmark': 'Western Europe',
    'Ecuador': 'South America',
    'Egypt': 'Middle East',
    'England': 'Western Europe',
    'English': 'Western Europe',
    'Estonia': 'Eastern Europe',
    'Ethiopia': 'Africa',
    'Fiji': 'Oceania',
    'Filipino': 'Southeast Asia',
    'Finland': 'Western Europe',
    'France': 'Western Europe',
    'France/Thailand': 'Western Europe',
    'French': 'Western Europe',
    'Georgia': 'Caucasus',
    'Georgian': 'Caucasus',
    'Germany': 'Western Europe',
    'Ghana': 'Africa',
    'Great Britain': 'Western Europe',
    'Greece': 'Western Europe',
    'Guam': 'Oceania',
    'Hong Kong': 'East Asia',
    'Hungary': 'Eastern Europe',
    'Iceland': 'Western Europe',
    'India': 'South Asia',
    'Indian': 'South Asia',
    'Indonesia': 'Southeast Asia',
    'Indonesia / USA': 'Southeast Asia',
    'Indonesian': 'Southeast Asia',
    'Iran': 'Middle East',
    'Iraq': 'Middle East',
    'Ireland': 'Western Europe',
    'Irish': 'Western Europe',
    'Israel': 'Middle East',
    'Italian': 'Western Europe',
    'Italy': 'Western Europe',
    'Ivory Coast': 'Africa',
    'Japan': 'East Asia',
    'Jordan': 'Middle East',
    'Kazakh': 'Central Asia',
    'Kazakhstan': 'Central Asia',
    'Kenya': 'Africa',
    'Korea': 'East Asia',
    'Kurdistan': 'Middle East',
    'Kuwait': 'Middle East',
    'Kyrgystan': 'Central Asia',
    'Kyrgyz': 'Central Asia',
    'Kyrgyzstan': 'Central Asia',
    'Laos': 'Southeast Asia',
    'Latvia': 'Eastern Europe',
    'Lebanon': 'Middle East',
    'Lithuania': 'Eastern Europe',
    'Malaysia': 'Southeast Asia',
    'Mexican': 'North America',
    'Mexico': 'North America',
    'Moldova': 'Eastern Europe',
    'Mongolia': 'Central Asia',
    'Mongolia/Russia': 'Central Asia',
    'Mongolian': 'Central Asia',
    'Morocco': 'Africa',
    'Myanmar': 'Southeast Asia',
    'Nepal': 'South Asia',
    'Netherlands': 'Western Europe',
    'New Zealand': 'Oceania',
    'Nigeria': 'Africa',
    'Northern Ireland': 'Western Europe',
    'Norway': 'Western Europe',
    'Oman': 'Middle East',
    'Pakistan': 'South Asia',
    'Palestine': 'Middle East',
    'Papua New Guinea': 'Oceania',
    'Paraguay': 'South America',
    'Peru': 'South America',
    'Philippines': 'Southeast Asia',
    'Poland': 'Eastern Europe',
    'Portugal': 'Western Europe',
    'Qatar': 'Middle East',
    'Romania': 'Eastern Europe',
    'Russia': 'Eastern Europe',
    'Russian': 'Eastern Europe',
    'Samoa': 'Oceania',
    'Saudi Arabia': 'Middle East',
    'Scotland': 'Western Europe',
    'Senegal': 'Africa',
    'Serbia': 'Eastern Europe',
    'Singapore': 'Southeast Asia',
    'Slovakia': 'Eastern Europe',
    'Slovenia': 'Eastern Europe',
    'South Africa': 'Africa',
    'South Korea': 'East Asia',
    'Spain': 'Western Europe',
    'Sri Lanka': 'South Asia',
    'Sweden': 'Western Europe',
    'Switzerland': 'Western Europe',
    'Syria': 'Middle East',
    'Taiwan': 'East Asia',
    'Tajik': 'Central Asia',
    'Tajikistan': 'Central Asia',
    'Tanzania': 'Africa',
    'Thai': 'Southeast Asia',
    'Thailand': 'Southeast Asia',
    'Thailand / USA': 'Southeast Asia',
    'Tonga': 'Oceania',
    'Tunisia': 'Africa',
    'Turkey': 'Middle East',
    'Turkish': 'Middle East',
    'Turkmenistan': 'Central Asia',
    'UAE': 'Middle East',
    'UK': 'Western Europe',
    'USA': 'North America',
    'Uganda': 'Africa',
    'Ukraine': 'Eastern Europe',
    'United Arab Emirates': 'Middle East',
    'United Kingdom': 'Western Europe',
    'United States': 'North America',
    'Uruguay': 'South America',
    'Uzbek': 'Central Asia',
    'Uzbekistan': 'Central Asia',
    'Venezuela': 'South America',
    'Vietnam': 'Southeast Asia',
    'Vietnam / New Zealand': 'Southeast Asia',
    'Vietnamese': 'Southeast Asia',
    'Wales': 'Western Europe',
    'Zambia': 'Africa',
    'Zimbabwe': 'Africa',
}


def age_mod(age: Optional[float]) -> float:
    if age is None:
        return 0.0
    for upper, mod in AGE_BANDS:
        if age <= upper:
            return mod
    return AGE_OLDER


def title_bonus(title_wins: Optional[int]) -> float:
    w = int(title_wins or 0)
    return 0.0 if w <= 0 else TITLE_BASE + TITLE_PER_WIN * w


def ascent_v381(*, wins: int, losses: int, draws: int, finish_rate_pct: float,
                weight_class: str, age: Optional[float], main_promotion: str,
                title_wins: int = 0, country: str = "",
                breakdown: bool = False) -> float | Dict[str, Any]:
    """finish_rate_pct = finishes / wins x 100. weight_class like 'Lightweight' or
    'Lightweight (155)'. main_promotion = promotion of the most recent fight."""
    total = wins + losses + draws
    win_rate = round(100.0 * wins / total, 1) if total else 0.0

    wc_key = weight_class.split(" (")[0].strip().lower()
    wc_avg = WC_AVG.get(wc_key, GLOBAL_FR_AVG)
    fr_shrunk = (finish_rate_pct * wins + SHRINK_K * wc_avg) / (wins + SHRINK_K)
    fr_norm = min(FR_NORM_CEILING, max(0.0, fr_shrunk / wc_avg * GLOBAL_FR_AVG))
    base80 = fr_norm * FR_WEIGHT + win_rate * WR_WEIGHT

    base, hq_region = PROMOTIONS.get(main_promotion, (0.0, "Unknown"))
    promo_pts = base + HQ_BONUS.get(hq_region, 0.0)

    region = COUNTRY_REGION.get(country.strip(), "Unknown")
    origin = ORIGIN_FIT.get(region, UNKNOWN_ORIGIN)
    a_mod = age_mod(age)
    t_bonus = title_bonus(title_wins)
    unbeaten = UNDEFEATED_BONUS if (losses == 0 and wins >= UNDEFEATED_MIN_WINS) else 0.0

    score = round(max(SCORE_FLOOR, base80 + promo_pts + origin + a_mod + t_bonus + unbeaten), 1)
    if not breakdown:
        return score
    return dict(score=score, win_rate=win_rate, wc_avg=wc_avg, fr_shrunk=round(fr_shrunk, 2),
                fr_norm=round(fr_norm, 2), base80=round(base80, 2), promo_pts=promo_pts,
                origin_region=region, origin_fit=origin, age_mod=a_mod,
                title_bonus=t_bonus, undefeated_bonus=unbeaten)


if __name__ == "__main__":
    # Eduardo Dutra, 9-0, 8 finishes, featherweight, LFA, age 22 (24 Oct 2026)
    s = ascent_v381(wins=9, losses=0, draws=0, finish_rate_pct=88.9,
                    weight_class="Featherweight", age=22, main_promotion="LFA", country="Brazil")
    print("Eduardo Dutra  ONE ASCENT v3.8.1 =", s)
