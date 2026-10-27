/* Champion Ascendant — shared page behaviour. Scores come from the server (/api). */
(function () {
  'use strict';

  var SHADES = [1, 0.74, 0.54, 0.4, 0.3];
  var RGB = { one: '226,181,63', ufc: '59,183,196' };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /** Draw a score as a bar of broad groups. No point values are shown. */
  function anatomy(result, sys, opts) {
    opts = opts || {};
    var max = Math.max(110, Math.ceil((result.score + 5) / 10) * 10);
    var pos = [], neg = 0, shade = 0;
    result.groups.forEach(function (g) {
      if (g.value > 0.05) {
        var color = g.label === 'Baseline' ? 'rgba(163,174,191,0.28)' : 'rgba(' + RGB[sys] + ',' + SHADES[Math.min(shade++, SHADES.length - 1)] + ')';
        pos.push({ g: g, color: color });
      } else if (g.value < -0.05) {
        neg += g.value;
      }
    });
    var posSum = pos.reduce(function (a, s) { return a + s.g.value; }, 0);
    var html = '<div class="anatomy ' + sys + (opts.animate ? ' animate' : '') + '">'
      + '<div class="anatomy-top"><span class="anatomy-name">' + esc(result.name) + '</span>'
      + '<span class="anatomy-score">' + result.score.toFixed(1) + '</span></div>'
      + '<div class="bar" role="img" aria-label="' + esc(result.name) + ' ' + result.score.toFixed(1) + ', built from '
      + esc(pos.map(function (s) { return s.g.label.toLowerCase(); }).join(', ')) + '">';
    pos.forEach(function (s, i) {
      html += '<span class="seg" title="' + esc(s.g.label) + '" style="width:' + (s.g.value / max * 100).toFixed(2)
        + '%;background:' + s.color + (opts.animate ? ';animation-delay:' + (i * 70) + 'ms' : '') + '"></span>';
    });
    if (neg < 0) {
      html += '<span class="neg" title="Deductions" style="left:' + (Math.max(0, posSum + neg) / max * 100).toFixed(2)
        + '%;width:' + (-neg / max * 100).toFixed(2) + '%"></span>';
    }
    html += '<span class="mark" style="left:' + (100 / max * 100).toFixed(2) + '%" aria-hidden="true"></span></div>';
    if (opts.legend !== false) {
      html += '<ul class="legend">' + pos.map(function (s) {
        return '<li><span class="swatch" style="background:' + s.color + '"></span>' + esc(s.g.label) + '</li>';
      }).join('') + (neg < 0 ? '<li><span class="swatch hatch"></span>Deductions</li>' : '') + '</ul>';
    }
    return html + '</div>';
  }

  function api(path, body) {
    return fetch(path, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {})
      .then(function (r) { return r.json().then(function (j) { if (!r.ok) throw new Error(j.error || 'Request failed'); return j; }); });
  }

  window.CA = { anatomy: anatomy, esc: esc, api: api };
  document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
