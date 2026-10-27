/*
 * ASCENT scoring in the browser.
 *
 * A line-for-line port of scoring/one_ascent_v3_9.py and scoring/dwcs_ascent_v3_0.py.
 * The lookup tables are generated from those Python files (static/ascent_tables.js),
 * and scoring/test_parity.py runs this file under Node against the Python on
 * thousands of inputs. If they ever disagree, the test fails.
 *
 * ONE ASCENT and DWCS ASCENT are separate formulas built on separate data.
 * Nothing in this file adds, averages or compares the two.
 */
(function (root) {
  'use strict';
  var T = (typeof module !== 'undefined' && module.exports)
    ? require('./ascent_tables.js')
    : root.ASCENT_TABLES;

  // Python's round(): works on the exact binary value of x and breaks true ties
  // half-to-even, so round(0.35, 1) is 0.3 here exactly as it is in Python.
  function pyRound(x, nd) {
    nd = nd || 0;
    var neg = x < 0, s = Math.abs(x).toFixed(nd + 30);
    var dot = s.indexOf('.');
    var head = s.slice(0, dot + 1 + nd).replace('.', '');
    var tail = s.slice(dot + 1 + nd);
    var up;
    if (tail[0] > '5') up = true;
    else if (tail[0] < '5') up = false;
    else if (/[1-9]/.test(tail.slice(1))) up = true;
    else up = (Number(head[head.length - 1]) % 2) === 1;
    var n = Number(head) + (up ? 1 : 0);
    var r = n / Math.pow(10, nd);
    return neg ? -r : r;
  }
  function isNum(v) { return typeof v === 'number' && isFinite(v); }

  /* ------------------------------ ONE ASCENT v3.9 ------------------------------ */
  var O = T.ONE;

  // Promotion points and HQ-region bonus per promotion code, as worked out by the
  // Python from each promotion's share of ONE signings. Unlisted codes score 0.
  function has(obj, k) { return Object.prototype.hasOwnProperty.call(obj, k); }
  function onePromoPoints(code) { return has(O.PROMO_POINTS, code) ? O.PROMO_POINTS[code] : O.UNLISTED_PROMO; }
  function oneHqBonus(code) { return has(O.PROMO_HQ_BONUS, code) ? O.PROMO_HQ_BONUS[code] : 0; }
  function oneAgeMod(age) {
    if (!isNum(age)) return 0; // blank or "N/A" scores 0
    for (var i = 0; i < O.AGE_BANDS.length; i++) {
      if (age <= O.AGE_BANDS[i][0]) return O.AGE_BANDS[i][1];
    }
    return O.AGE_OLDER;
  }
  function oneTitleBonus(t) {
    var w = Math.trunc(t || 0);
    return w <= 0 ? 0 : O.TITLE_BASE + O.TITLE_PER_WIN * w;
  }

  /** ONE ASCENT v3.9. finishRate = finishes / wins x 100. */
  function scoreONE(f) {
    var wins = f.wins, losses = f.losses || 0, draws = f.draws || 0;
    var total = wins + losses + draws;
    var winRate = total ? pyRound(100 * wins / total, 1) : 0;
    var wcAvg = isNum(O.WC_AVG[f.weightClass]) ? O.WC_AVG[f.weightClass] : O.GLOBAL_FR_AVG;
    var frShrunk = (f.finishRate * wins + O.SHRINK_K * wcAvg) / (wins + O.SHRINK_K);
    var frNorm = Math.min(O.FR_NORM_CEILING, Math.max(0, frShrunk / wcAvg * O.GLOBAL_FR_AVG));
    var finish = frNorm * O.FR_WEIGHT;
    var winPts = winRate * O.WR_WEIGHT;
    var promo = onePromoPoints(f.promotion);
    var hq = oneHqBonus(f.promotion);
    var region = O.COUNTRY_REGION[f.country] || 'Unknown';
    var origin = isNum(O.ORIGIN_FIT[region]) ? O.ORIGIN_FIT[region] : O.UNKNOWN_ORIGIN;
    var age = oneAgeMod(f.age);
    var title = oneTitleBonus(f.titleWins);
    var unbeaten = (losses === 0 && wins >= O.UNDEFEATED_MIN_WINS) ? O.UNDEFEATED_BONUS : 0;
    var raw = finish + winPts + promo + hq + origin + age + title + unbeaten;
    return {
      system: 'ONE', version: O.version,
      score: pyRound(Math.max(0, raw), 1),
      winRate: winRate, wcAvg: wcAvg, frShrunk: frShrunk, frNorm: frNorm, region: region,
      parts: [
        { key: 'finish', label: 'Finish rate', value: finish, note: 'shrunk ' + frShrunk.toFixed(1) + '%, normalized ' + frNorm.toFixed(1) },
        { key: 'win', label: 'Win rate', value: winPts, note: winRate.toFixed(1) + '%' },
        { key: 'promo', label: 'Promotion', value: promo, note: 'share of ONE signings' },
        { key: 'hq', label: 'Promotion HQ region', value: hq },
        { key: 'origin', label: 'Origin region', value: origin, note: region },
        { key: 'age', label: 'Age', value: age },
        { key: 'title', label: 'Title wins', value: title },
        { key: 'unbeaten', label: 'Undefeated (5+ wins)', value: unbeaten }
      ]
    };
  }

  /* ------------------------------ DWCS ASCENT v3.0 ----------------------------- */
  var D = T.DWCS;
  var FR_NORM_CEILING_D = D.FR_RATIO_CAP * D.OVERALL_FR_AVG;

  function resolvePromotion(p) {
    p = (p || '').trim();
    return Object.prototype.hasOwnProperty.call(D.PROMO_ALIASES, p) ? D.PROMO_ALIASES[p] : p;
  }
  function dwcsPromoPoints(promotion) {
    var up = resolvePromotion(promotion).toUpperCase();
    var keys = Object.keys(D.PROMO_TIERS), i;
    for (i = 0; i < keys.length; i++) if (keys[i].toUpperCase() === up) return D.PROMO_TIERS[keys[i]];
    var bestKey = null, bestPts = 0;
    for (i = 0; i < keys.length; i++) {
      var ku = keys[i].toUpperCase();
      if (up.indexOf(ku) !== -1 && (bestKey === null || ku.length > bestKey.length)) {
        bestKey = ku; bestPts = D.PROMO_TIERS[keys[i]];
      }
    }
    return bestKey ? bestPts : D.UNLISTED_DEFAULT;
  }
  function dwcsAge(age) {
    if (age >= 26 && age <= 29) return D.AGE_CORE_BONUS;
    if (age >= 23 && age <= 31) return D.AGE_WINDOW_BONUS;
    return D.AGE_TAIL_PENALTY;
  }
  function dwcsStreak(s) {
    s = Math.max(0, Math.trunc(s || 0));
    return s === 0 ? 0 : Math.max(0, (5.5 * Math.sqrt(s) - 4.5) * D.STREAK_MULT);
  }
  function dwcsLoss(l) {
    var v = D.LOSS_BAND[String(Math.max(0, Math.trunc(l || 0)))];
    return isNum(v) ? v : D.LOSS_BAND_DEFAULT;
  }
  function dwcsTitle(t, promoPts) {
    t = Math.max(0, Math.trunc(t || 0));
    return t === 0 ? 0 : (1.5 + promoPts / 3) * Math.sqrt(t);
  }

  /** DWCS ASCENT Profile v3.0. weightClass is lower-case, e.g. "women's flyweight". */
  function scoreDWCS(f) {
    var wins = f.wins, losses = f.losses || 0, draws = f.draws || 0;
    var winPct = 100 * wins / (wins + losses + draws);
    var avg = D.WC_FR_AVG[(f.weightClass || '').trim().toLowerCase()];
    if (!isNum(avg)) avg = D.OVERALL_FR_AVG;
    var frNorm = Math.min(f.finishRate / avg, D.FR_RATIO_CAP) * D.OVERALL_FR_AVG;
    var promo = dwcsPromoPoints(f.promotion);
    var parts = [
      { key: 'finish', label: 'Finish rate', value: frNorm / FR_NORM_CEILING_D * D.FR_WEIGHT, note: 'normalized ' + frNorm.toFixed(1) },
      { key: 'win', label: 'Win rate', value: winPct / 100 * D.WIN_WEIGHT, note: winPct.toFixed(1) + '%' },
      { key: 'loss', label: 'Loss band', value: dwcsLoss(losses), note: losses + (losses === 1 ? ' loss' : ' losses') },
      { key: 'streak', label: 'Win streak', value: dwcsStreak(f.winStreak) },
      { key: 'promo', label: 'Promotion', value: promo, note: 'share of DWCS invitees' },
      { key: 'age', label: 'Age', value: dwcsAge(f.age) },
      { key: 'title', label: 'Title wins', value: dwcsTitle(f.titleWins, promo) },
      { key: 'elite', label: 'Elite finisher', value: frNorm >= 85 ? D.ELITE_FINISHER_BONUS : 0 },
      { key: 'hot', label: 'Hot streak (7+)', value: Math.trunc(f.winStreak || 0) >= D.HOT_STREAK_THRESHOLD ? D.HOT_STREAK_BONUS : 0 }
    ];
    var rawSum = parts.reduce(function (a, p) { return a + p.value; }, 0);
    var display = D.ANCHOR_SLOPE * rawSum + D.ANCHOR_INTERCEPT;
    // The published score is a linear rescale of the raw sum. Show each part in
    // display units so the parts plus the anchor add up to the published number.
    parts.forEach(function (p) { p.value = p.value * D.ANCHOR_SLOPE; });
    parts.push({ key: 'anchor', label: 'Scale anchor', value: D.ANCHOR_INTERCEPT, note: 'fixed offset, same for everyone' });
    return {
      system: 'DWCS', version: D.version,
      score: pyRound(Math.max(0, display), 1),
      frNorm: frNorm, promoPoints: promo, parts: parts
    };
  }

  var api = { scoreONE: scoreONE, scoreDWCS: scoreDWCS, pyRound: pyRound, tables: T };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.ASCENT = api;
})(this);
