/* ============================================================
   PUBLIC PORTFOLIO BUILD
   ------------------------------------------------------------
   The ASCENT scoring engine (component weights, promotion
   pipeline tables, region/age curves, normalization model)
   is proprietary and is NOT included in this public repo.
   It has been replaced below with a transparent demo stub so
   the interface remains fully interactive. Scores produced by
   this build are illustrative only and do NOT reflect the
   real ASCENT model.
   ============================================================ */

document.getElementById('yr').textContent = new Date().getFullYear();

const obs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
  });
}, { threshold: 0.08 });
document.querySelectorAll('.reveal').forEach(el => obs.observe(el));

function switchTab(tab) {
  document.querySelectorAll('.pathway-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  document.querySelectorAll('.pathway-panel').forEach(p => p.classList.toggle('active', p.id === 'panel-' + tab));
}

function clamp(x, lo, hi) { return Math.max(lo, Math.min(hi, x)); }

function validate(id, min, max) {
  const el = document.getElementById(id);
  const field = el.closest('.field');
  const v = parseFloat(el.value);
  if (isNaN(v) || v < min || v > max) {
    field.classList.add('has-error');
    return null;
  }
  field.classList.remove('has-error');
  return v;
}

/* ---- DEMO STUB ----------------------------------------------
   The real ASCENT formula is proprietary and lives in a private
   build. The function below is a simplified placeholder used only
   so the calculator UI works in this public demo.
   --------------------------------------------------------------- */
function demoScore(fr, wr, age) {
  // Illustrative only — NOT the real ASCENT weights.
  const base = 0.5 * (fr / 100) + 0.5 * (wr / 100);
  let ageNudge = (age >= 23 && age <= 27) ? 5 : 0;
  return clamp(base * 90 + ageNudge, 0, 100);
}

function calcONE() {
  document.querySelectorAll('#panel-one .field').forEach(f => f.classList.remove('has-error'));
  const fr = validate('one-fr', 0, 100);
  const wr = validate('one-wr', 0, 100);
  const age = validate('one-age', 16, 50);
  if (fr === null || wr === null || age === null) return;

  const score = demoScore(fr, wr, age);
  renderResult('one-result', score, [
    ['Demo Score', score.toFixed(1) + ' of 100', 'neutral'],
    ['Note', 'Real model omitted', 'neutral'],
  ], 'ONE Championship', score);
}

function calcDWCS() {
  document.querySelectorAll('#panel-dwcs .field').forEach(f => f.classList.remove('has-error'));
  const fr = validate('dwcs-fr', 0, 100);
  const wr = validate('dwcs-wr', 0, 100);
  const age = validate('dwcs-age', 16, 50);
  if (fr === null || wr === null || age === null) return;

  const score = demoScore(fr, wr, age);
  renderResult('dwcs-result', score, [
    ['Demo Score', score.toFixed(1) + ' of 100', 'neutral'],
    ['Note', 'Real model omitted', 'neutral'],
  ], 'DWCS', score);
}

function getTier(score, pathway) {
  if (score >= 85) return { label: 'Tier A — Elite signing readiness', color: '#27AE60' };
  if (score >= 70) return { label: 'Tier B — Strong prospect', color: '#D4AF37' };
  if (score >= 55) return { label: 'Tier C — Developing', color: '#E67E22' };
  return { label: 'Tier D — Significant gaps', color: '#C0392B' };
}

function renderResult(containerId, score, rows, pathway, rawScore) {
  const tier = getTier(score, pathway);
  const circ = 2 * Math.PI * 42;
  const offset = circ * (1 - score / 100);

  let html = '<div class="result-score-row">'
    + '<div class="score-ring-wrap"><svg viewBox="0 0 100 100">'
    + '<circle class="ring-bg" cx="50" cy="50" r="42"/>'
    + '<circle class="ring-fill" cx="50" cy="50" r="42" style="stroke-dasharray:' + circ.toFixed(1) + ';stroke-dashoffset:' + offset.toFixed(1) + ';stroke:' + tier.color + '"/>'
    + '</svg><div class="score-number" style="color:' + tier.color + '">' + Math.round(score) + '</div></div>'
    + '<div class="score-meta"><strong>' + pathway + ' ASCENT: ' + score.toFixed(1) + '/100</strong>'
    + '<div class="tier" style="color:' + tier.color + '">' + tier.label + '</div>'
    + '<div class="tier" style="color:var(--gray-dim);margin-top:4px">Demo build — real model private</div>'
    + '</div></div><div class="breakdown-list">';

  rows.forEach(r => {
    html += '<div class="breakdown-row"><span class="bl">' + r[0] + '</span><span class="bv ' + r[2] + '">' + r[1] + '</span></div>';
  });

  html += '</div>';
  document.getElementById(containerId).innerHTML = html;
}
