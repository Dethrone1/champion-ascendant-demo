/* Champion Ascendant — shared page behaviour. Needs static/ascent.js for scoring. */
(function () {
  'use strict';

  var SHADES = [1, 0.8, 0.64, 0.52, 0.43, 0.36, 0.3, 0.25, 0.21];
  var RGB = { ONE: '226,181,63', DWCS: '59,183,196' };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function signed(v) {
    var r = Math.round(v * 10) / 10;
    if (r === 0) return '0';
    return (r > 0 ? '+' : '−') + Math.abs(r).toFixed(1);
  }

  /**
   * Draw a score as a bar of its parts, with a legend underneath.
   * result: output of ASCENT.scoreONE / ASCENT.scoreDWCS.
   */
  function anatomy(result, opts) {
    opts = opts || {};
    var sys = result.system;
    var max = Math.max(110, Math.ceil((result.score + 5) / 10) * 10);
    var pos = [], negTotal = 0, shade = 0;
    // The DWCS scale anchor is a fixed offset; draw it first, in grey, so the coloured
    // segments are the parts that actually differ between fighters.
    var parts = result.parts.slice().sort(function (a, b) {
      return (b.key === 'anchor') - (a.key === 'anchor');
    });
    parts.forEach(function (p) {
      if (p.value > 0.0001) {
        var color = p.key === 'anchor' ? 'rgba(163,174,191,0.28)' : 'rgba(' + RGB[sys] + ',' + SHADES[Math.min(shade++, SHADES.length - 1)] + ')';
        pos.push({ p: p, color: color });
      } else if (p.value < -0.0001) {
        negTotal += p.value;
      }
    });
    var posSum = pos.reduce(function (a, s) { return a + s.p.value; }, 0);
    var html = '<div class="anatomy ' + sys.toLowerCase() + (opts.animate ? ' animate' : '') + '">';
    html += '<div class="anatomy-top"><span class="anatomy-name">' + sys + ' ASCENT <span class="v">v' + esc(result.version) + '</span></span>'
      + '<span class="anatomy-score" aria-label="' + sys + ' ASCENT score ' + result.score.toFixed(1) + '">' + result.score.toFixed(1) + '</span></div>';
    html += '<div class="bar" role="img" aria-label="' + sys + ' score parts: '
      + esc(result.parts.filter(function (p) { return Math.abs(p.value) > 0.05; }).map(function (p) { return p.label + ' ' + signed(p.value); }).join(', ')) + '">';
    pos.forEach(function (s, i) {
      html += '<span class="seg" title="' + esc(s.p.label + ' ' + signed(s.p.value)) + '" style="width:' + (s.p.value / max * 100).toFixed(3)
        + '%;background:' + s.color + (opts.animate ? ';animation-delay:' + (i * 60) + 'ms' : '') + '"></span>';
    });
    if (negTotal < 0) {
      var left = Math.max(0, posSum + negTotal) / max * 100;
      html += '<span class="neg" title="Deductions ' + signed(negTotal) + '" style="left:' + left.toFixed(3) + '%;width:' + (-negTotal / max * 100).toFixed(3) + '%"></span>';
    }
    html += '<span class="mark" style="left:' + (100 / max * 100).toFixed(3) + '%" aria-hidden="true"></span></div>';
    html += '<div class="scale" aria-hidden="true"><span>0</span><span>100 mark</span></div>';
    if (opts.legend !== false) {
      html += '<ul class="legend">';
      var shadeIx = 0, zeros = [];
      parts.forEach(function (p) {
        if (Math.abs(p.value) < 0.05) { zeros.push(p.label); if (p.value > 0.0001) shadeIx++; return; }
        var cls = p.value < 0 ? 'neg' : '';
        var sw = p.key === 'anchor' ? 'rgba(163,174,191,0.4)'
          : p.value > 0 ? 'rgba(' + RGB[sys] + ',' + SHADES[Math.min(shadeIx++, SHADES.length - 1)] + ')'
          : 'var(--neg)';
        html += '<li class="' + cls + '"><span><span class="swatch" style="background:' + sw + '"></span>' + esc(p.label)
          + (p.note && opts.notes ? '<span class="note">' + esc(p.note) + '</span>' : '') + '</span><b>' + signed(p.value) + '</b></li>';
      });
      html += '</ul>';
      if (zeros.length) html += '<p class="zeros">No points from: ' + esc(zeros.join(', ').toLowerCase()) + '.</p>';
    }
    return html + '</div>';
  }

  // Board division names (UFC names) -> the keys each formula expects.
  function forONE(f) {
    return { wins: f.wins, losses: f.losses, draws: f.draws, finishRate: f.finishRate, weightClass: f.division,
      age: f.age, promotion: f.onePromotion, titleWins: f.titleWins, country: f.country };
  }
  function forDWCS(f) {
    return { wins: f.wins, losses: f.losses, draws: f.draws, finishRate: f.finishRate, weightClass: f.division.toLowerCase(),
      age: f.age, promotion: f.dwcsPromotion, titleWins: f.titleWins, winStreak: f.winStreak };
  }

  window.CA = { anatomy: anatomy, esc: esc, signed: signed, forONE: forONE, forDWCS: forDWCS };

  document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
