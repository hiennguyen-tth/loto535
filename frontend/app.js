/* LottoAI v3 — app.js */
'use strict';

const API = '';   // same-origin
const REGEN_MSGS = [
  'Analyzing patterns...',
  'Detecting anomalies...',
  'Computing frequency clusters...',
  'Generating optimized sets...',
  'Finalizing...',
];

let state = {
  predictions: null,
  latest: [],
  stats: null,
  window: 30,
  histPage: 1,
  saved: [],
  regenTimer: null,
  explainOpen: new Set(),
};

// ─── FETCH ────────────────────────────────────────────
async function fetchJSON(url, retries) {
  retries = retries === undefined ? 3 : retries;
  let lastErr;
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(12000) });
      if (!res.ok) throw new Error('HTTP ' + res.status + ' ' + url);
      return await res.json();
    } catch (e) {
      lastErr = e;
      if (i < retries - 1) await sleep(800 * (i + 1));
    }
  }
  throw lastErr;
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ─── INIT ─────────────────────────────────────────────
function init() {
  initTheme();
  initNavbar();
  initSaved();
  updateSessionInfo();
  loadAll();
}

async function loadAll() {
  showPredSkeleton();
  hideError();

  try {
    const [preds, stats, latest] = await Promise.all([
      fetchJSON(API + '/api/predictions?window=' + state.window),
      fetchJSON(API + '/api/stats'),
      fetchJSON(API + '/api/latest?n=20'),
    ]);

    state.predictions = preds;
    state.stats = stats;
    state.latest = latest;

    renderStats(stats, preds);
    renderHeroLastDraw(latest[0]);
    renderHeroFeatured(preds);
    renderPredictions(preds);
    renderHotGap(preds);

    loadFrequency(0);
    loadBacktest();
    renderHistory(latest, false);
    renderSaved();
  } catch (err) {
    console.error('[loadAll]', err);
    showError();
    showToast('Không thể tải dữ liệu. Kiểm tra kết nối.', 'error');
  }
}

// ─── REGENERATE ───────────────────────────────────────
async function doRegenerate() {
  const btn = document.getElementById('btn-regen');
  const lblEl = document.getElementById('regen-label');
  if (!btn || btn.disabled) return;

  btn.disabled = true;
  showPredSkeleton();

  let phase = 0;
  if (state.regenTimer) clearInterval(state.regenTimer);
  state.regenTimer = setInterval(function() {
    if (lblEl) lblEl.textContent = REGEN_MSGS[phase % REGEN_MSGS.length];
    phase++;
  }, 700);

  try {
    const preds = await fetchJSON(API + '/api/predictions?window=' + state.window);
    state.predictions = preds;
    renderHeroFeatured(preds);
    renderPredictions(preds);
    renderHotGap(preds);
    showToast('Generated new prediction set!', 'success');
  } catch (err) {
    showToast('Could not generate. Try again.', 'error');
  } finally {
    clearInterval(state.regenTimer);
    btn.disabled = false;
    if (lblEl) lblEl.textContent = 'Generate New';
  }
}

async function loadFrequency(win) {
  try {
    const freq = await fetchJSON(API + '/api/frequency?window=' + win);
    renderInsights(freq, win);
    renderFreqChart(freq);
  } catch (e) { console.warn('[freq]', e); }
}

async function loadBacktest() {
  try {
    const bt = await fetchJSON(API + '/api/backtest');
    renderBacktest(bt);
  } catch (e) {
    const el = document.getElementById('backtest-metrics');
    if (el) el.innerHTML = '<p style="color:var(--text-3);font-size:.8rem;padding:12px">Cần thêm dữ liệu để chạy backtest (≥150 kỳ).</p>';
  }
}

async function loadMoreHistory() {
  state.histPage += 1;
  try {
    const rows = await fetchJSON(API + '/api/latest?n=' + (state.histPage * 20));
    state.latest = rows;
    renderHistory(rows, false);
  } catch (e) { showToast('Không tải thêm được.', 'error'); }
}

// ─── RENDER HELPERS ───────────────────────────────────
function ball(num, cls, size) {
  cls = cls || 'main'; size = size ? ' ball--' + size : '';
  return '<span class="ball ball--' + cls + size + '">' + pad(num) + '</span>';
}
function pad(n) { return String(n).padStart(2, '0'); }
function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

function showPredSkeleton() {
  const el = document.getElementById('pred-list');
  if (!el) return;
  let h = '';
  for (let i = 0; i < 5; i++) {
    h += '<div class="pred-card" style="opacity:.4"><div class="pred-card__body"><div class="pred-card__balls">';
    for (let j = 0; j < 5; j++) h += '<div class="s-ball s-ball--main"></div>';
    h += '<div class="pred-card__sep">|</div><div class="s-ball s-ball--db"></div></div></div></div>';
  }
  el.innerHTML = h;
}
function showError() {
  const e = document.getElementById('pred-error');
  if (e) e.classList.remove('hidden');
  const l = document.getElementById('pred-list');
  if (l) l.innerHTML = '';
}
function hideError() {
  const e = document.getElementById('pred-error');
  if (e) e.classList.add('hidden');
}

// ─── RENDER STATS BAR ─────────────────────────────────
function renderStats(stats, preds) {
  const el = document.getElementById('stats-bar');
  if (!el) return;
  const s = stats.sum_stats || {};
  const lat = stats.latest || {};
  el.innerHTML = [
    { val: stats.total || 0, label: 'Tổng kỳ quay' },
    { val: lat.ky ? '#' + pad(lat.ky) : '—', label: 'Kỳ gần nhất' },
    { val: lat.ngay || '—', label: 'Ngày quay' },
    { val: s.avg ? 'Σ' + Math.round(s.avg) : '—', label: 'Tổng TB 5 số' },
  ].map(function(d) {
    return '<div class="stat-pill"><div class="stat-pill__val">' + esc(String(d.val)) +
           '</div><div class="stat-pill__label">' + esc(d.label) + '</div></div>';
  }).join('');

  // update hero draws count
  var hd = document.getElementById('hero-draws');
  if (hd) hd.textContent = stats.total || '--';
}

// ─── RENDER HERO LAST DRAW ────────────────────────────
function renderHeroLastDraw(r) {
  if (!r) return;
  const el = document.getElementById('hero-balls');
  if (!el) return;
  el.innerHTML = [r.s1, r.s2, r.s3, r.s4, r.s5].map(function(n) {
    return ball(n, 'main');
  }).join('') + ball(r.db, 'db');
}

// ─── RENDER HERO FEATURED CARD ────────────────────────
function renderHeroFeatured(preds) {
  const p0 = preds.predictions && preds.predictions[0];
  if (!p0) return;

  const bEl = document.getElementById('feat-balls');
  if (bEl) {
    bEl.innerHTML = (p0.nums || []).map(function(n) { return ball(n, 'main', 'lg'); }).join('') +
      '<div class="feat-card__sep">|</div>' + ball(p0.db, 'db', 'lg');
  }

  const fill = document.getElementById('feat-conf-fill');
  if (fill) fill.style.width = (p0.confidence || 0) + '%';

  const lbl = document.getElementById('feat-conf-label');
  if (lbl) lbl.textContent = 'Confidence: ' + (p0.confidence || 0) + '%';

  const tagsEl = document.getElementById('feat-tags');
  if (tagsEl) tagsEl.innerHTML = renderTags(p0.tags || []);

  // store for explain
  state._feat = p0;
}

// ─── RENDER PREDICTIONS ───────────────────────────────
function buildExplain(p, preds) {
  if (!preds) return '';
  const hotSet = new Set((preds.hot_numbers || []).map(function(r) { return r.so; }));
  const gapArr = (preds.gap_numbers || []);
  const gapSet = new Set(gapArr.map(function(r) { return r.so; }));
  const nums = p.nums || [];

  const hotNums = nums.filter(function(n) { return hotSet.has(n); });
  const gapNums = nums.filter(function(n) { return gapSet.has(n); });
  const evens   = nums.filter(function(n) { return n % 2 === 0; });
  const low     = nums.filter(function(n) { return n <= 12; }).length;
  const mid     = nums.filter(function(n) { return n > 12 && n <= 24; }).length;
  const hi      = nums.filter(function(n) { return n > 24; }).length;

  const avgGap = gapArr.length > 0 ? Math.round(gapArr.reduce(function(a,r){ return a+r.gap; },0)/gapArr.length) : 0;

  return '<p>🔥 <strong>' + hotNums.length + ' hot numbers</strong>' +
    (hotNums.length > 0 ? ' (' + hotNums.map(pad).join(', ') + ')' : '') +
    ': xuất hiện nhiều trong ' + (preds.window || 30) + ' kỳ gần nhất</p>' +
    (gapNums.length > 0 ? '<p>⏳ <strong>' + gapNums.length + ' overdue</strong>' +
    ' (' + gapNums.map(pad).join(', ') + '): avg gap ~' + avgGap + ' kỳ </p>' : '') +
    '<p>⚖️ Tỷ lệ chẵn/lẻ: <strong>' + evens.length + '/' + (5 - evens.length) + '</strong></p>' +
    '<p>📊 Phân bố: thấp (1-12) <strong>' + low + '</strong> · giữa (13-24) <strong>' + mid + '</strong> · cao (25-35) <strong>' + hi + '</strong></p>';
}

function renderPredictions(preds) {
  const el = document.getElementById('pred-list');
  if (!el) return;
  const ps = preds.predictions || [];
  const savedSet = new Set(state.saved.map(function(s) { return s._key; }));

  el.innerHTML = ps.map(function(p, i) {
    const key = (p.nums || []).join(',') + '|' + p.db;
    const isSaved = savedSet.has(key);
    const sum = (p.nums || []).reduce(function(a,b){return a+b;}, 0);
    return (
      '<div class="pred-card" id="pred-card-' + i + '">' +
        '<div class="pred-card__body">' +
          '<div class="pred-card__head">' +
            '<div class="pred-card__meta">' +
              '<span class="pred-card__num">#' + (i+1) + '</span>' +
              '<span class="pred-card__name">' + esc(p.ten) + '</span>' +
            '</div>' +
            '<div class="pred-card__acts">' +
              '<button class="act-btn" onclick="toggleExplain(' + i + ')">Giải thích AI</button>' +
              '<button class="act-btn' + (isSaved ? ' act-btn--saved' : '') + '" id="save-btn-' + i + '" onclick="toggleSave(' + i + ')">' +
                (isSaved ? '★ Đã lưu' : '☆ Save') +
              '</button>' +
              '<button class="act-btn" onclick="shareSet(' + i + ')">Share</button>' +
            '</div>' +
          '</div>' +
          '<div class="pred-card__balls">' +
            (p.nums || []).map(function(n){ return ball(n); }).join('') +
            '<span class="pred-card__sep">|</span>' + ball(p.db, 'db') +
          '</div>' +
          '<div class="pred-card__conf">' +
            '<div class="pred-card__conf-row">' +
              '<div class="conf-bar" style="flex:1"><div class="conf-bar__fill" style="width:' + (p.confidence||0) + '%"></div></div>' +
              '<span class="pred-card__conf-pct">' + (p.confidence||0) + '%</span>' +
              '<span style="font-size:.7rem;color:var(--text-3)">Σ' + sum + '</span>' +
            '</div>' +
          '</div>' +
          '<div class="pred-card__tags">' + renderTags(p.tags || []) + '</div>' +
        '</div>' +
        '<div class="explain-panel hidden" id="explain-' + i + '">' + buildExplain(p, preds) + '</div>' +
      '</div>'
    );
  }).join('');
}

function renderTags(tags) {
  return (tags || []).map(function(t) {
    var c = t === 'HOT' ? 'hot' : t === 'GAP' ? 'gap' : t === 'BALANCED' ? 'balanced' : 'stable';
    var icon = t === 'HOT' ? '🔥' : t === 'GAP' ? '⏳' : t === 'BALANCED' ? '⚖️' : '📊';
    return '<span class="tag tag--' + c + '">' + icon + ' ' + t + '</span>';
  }).join('');
}

// ─── EXPLAIN TOGGLE ───────────────────────────────────
function toggleExplain(idx) {
  var panelId = 'explain-' + idx;
  var el = document.getElementById(panelId);
  if (!el) return;
  var isHidden = el.classList.toggle('hidden');

  if (idx === 'feat') {
    // Hero featured explain
    if (!isHidden && state.predictions) {
      el.innerHTML = buildExplain(state._feat || state.predictions.predictions[0], state.predictions);
    }
    var btn = el.previousElementSibling;
    if (btn) btn.textContent = isHidden ? 'Giải thích AI ▾' : 'Ẩn ▴';
  }
}

// ─── HOT / GAP ────────────────────────────────────────
function renderHotGap(preds) {
  var hotEl = document.getElementById('hot-balls');
  var gapEl = document.getElementById('gap-balls');
  var hotTrend = document.getElementById('hot-trend');
  var gapTrend = document.getElementById('gap-trend');

  var hot = preds.hot_numbers || [];
  var gap = preds.gap_numbers || [];

  if (hotEl) hotEl.innerHTML = hot.map(function(r) {
    return ball(r.so, 'hot', 'sm') + '<span style="font-size:.65rem;color:var(--text-3);margin-right:4px">' + (r.freq_30||0) + 'x</span>';
  }).join('');

  if (gapEl) gapEl.innerHTML = gap.map(function(r) {
    return ball(r.so, 'gap', 'sm') + '<span style="font-size:.65rem;color:var(--text-3);margin-right:4px">' + (r.gap||0) + 'kỳ</span>';
  }).join('');

  if (hotTrend && hot.length > 0) {
    var avg30 = hot.reduce(function(a,r){ return a+r.freq_30; }, 0) / hot.length;
    hotTrend.textContent = '↑ TB ' + avg30.toFixed(1) + 'x mỗi 30 kỳ';
  }
  if (gapTrend && gap.length > 0) {
    var avgGap = gap.reduce(function(a,r){ return a+r.gap; }, 0) / gap.length;
    gapTrend.textContent = 'Avg gap: ~' + Math.round(avgGap) + ' kỳ';
  }
}

// ─── INSIGHTS + FREQ CHART ────────────────────────────
function renderInsights(freqData, win) {
  var grid = document.getElementById('insight-grid');
  if (!grid) return;

  var sorted = freqData.slice().sort(function(a,b){return b.count-a.count;});
  var maxN = sorted[0] ? sorted[0].count : 1;
  var minN = sorted[sorted.length-1] ? sorted[sorted.length-1].count : 0;

  var byNum = freqData.slice().sort(function(a,b){return a.so-b.so;});
  var total = byNum.reduce(function(a,r){return a+r.count;}, 0);
  var evens = byNum.filter(function(r){return r.so%2===0;}).reduce(function(a,r){return a+r.count;}, 0);
  var evenPct = total > 0 ? Math.round(evens/total*100) : 0;

  // Most active range (1-7, 8-14, 15-21, 22-28, 29-35)
  var ranges = [[1,7],[8,14],[15,21],[22,28],[29,35]];
  var rangeTotals = ranges.map(function(r) {
    return byNum.filter(function(d){return d.so>=r[0]&&d.so<=r[1];}).reduce(function(a,d){return a+d.count;},0);
  });
  var maxRangeIdx = rangeTotals.indexOf(Math.max.apply(null, rangeTotals));
  var maxRange = ranges[maxRangeIdx];

  grid.innerHTML = [
    { label: 'Most Active Range', val: maxRange[0] + '–' + maxRange[1], sub: rangeTotals[maxRangeIdx] + ' lần xuất hiện' },
    { label: 'Odd / Even Split', val: (100-evenPct) + '% / ' + evenPct + '%', sub: 'Lẻ / Chẵn' },
    { label: 'Số ít xuất hiện nhất', val: pad(sorted[sorted.length-1].so), sub: minN + ' lần (của ' + (win||'all') + ' kỳ)' },
  ].map(function(d) {
    return '<div class="insight-card">' +
      '<div class="insight-card__label">' + d.label + '</div>' +
      '<div class="insight-card__val">' + d.val + '</div>' +
      '<div class="insight-card__sub">' + d.sub + '</div>' +
    '</div>';
  }).join('');
}

function renderFreqChart(freqData) {
  var el = document.getElementById('freq-chart');
  if (!el) return;

  var sorted = freqData.slice().sort(function(a,b){return b.count-a.count;});
  var maxCount = sorted[0] ? sorted[0].count : 1;
  var top5Set = new Set(sorted.slice(0,5).map(function(r){return r.so;}));
  var top15Set = new Set(sorted.slice(0,15).map(function(r){return r.so;}));
  var bot5Set = new Set(sorted.slice(-5).map(function(r){return r.so;}));

  var byNum = freqData.slice().sort(function(a,b){return a.so-b.so;});

  el.innerHTML = byNum.map(function(r) {
    var pct = maxCount > 0 ? (r.count/maxCount*100).toFixed(1) : 0;
    var rowCls = '';
    var badge = '';
    if (top5Set.has(r.so)) { rowCls = ' freq-row--top5'; badge = '<span class="freq-badge freq-badge--hot">HOT</span>'; }
    else if (top15Set.has(r.so)) { rowCls = ' freq-row--top15'; }
    else if (bot5Set.has(r.so)) { rowCls = ' freq-row--bot5'; badge = '<span class="freq-badge freq-badge--cold">LOW</span>'; }

    return '<div class="freq-row' + rowCls + '">' +
      '<span class="freq-row__num">' + pad(r.so) + '</span>' +
      '<div class="freq-row__track"><div class="freq-row__fill" style="width:' + pct + '%"></div></div>' +
      '<span class="freq-row__count">' + r.count + '</span>' +
      badge +
    '</div>';
  }).join('');
}

// ─── BACKTEST ─────────────────────────────────────────
function renderBacktest(bt) {
  var el = document.getElementById('backtest-metrics');
  if (!el) return;
  if (bt.error) {
    el.innerHTML = '<p style="color:var(--text-3);font-size:.8rem;padding:12px">' + esc(bt.error) + '</p>';
    return;
  }
  var metrics = [
    { val: bt.accuracy_pct != null ? bt.accuracy_pct : '—', pct: '%', label: 'Hit ≥2 số / top-5' },
    { val: bt.avg_hits != null ? bt.avg_hits : '—', pct: '', label: 'Avg số trúng (top-10)' },
    { val: bt.hit3_pct != null ? bt.hit3_pct : '—', pct: '%', label: 'Hit ≥3 số / top-10' },
    { val: bt.total_tested != null ? bt.total_tested : '—', pct: '', label: 'Kỳ kiểm tra' },
  ];
  el.innerHTML = metrics.map(function(m) {
    return '<div class="bt-metric">' +
      '<div class="bt-metric__val">' + esc(String(m.val)) + '<span class="bt-metric__pct">' + m.pct + '</span></div>' +
      '<div class="bt-metric__label">' + m.label + '</div>' +
    '</div>';
  }).join('');
}

// ─── HISTORY ──────────────────────────────────────────
function renderHistory(rows, append) {
  var tbody = document.getElementById('hist-body');
  if (!tbody) return;
  if (!rows.length) { tbody.innerHTML = '<tr><td colspan="10" class="empty-cell">Không có dữ liệu</td></tr>'; return; }
  var html = rows.map(function(r) {
    return '<tr>' +
      '<td class="ky-cell">#' + pad(r.ky) + '</td>' +
      '<td class="ngay-cell">' + (r.ngay||'') + '</td>' +
      '<td><span class="' + (r.buoi==='S'?'buoi-s':'buoi-t') + '">' + (r.buoi==='S'?'13H':'21H') + '</span></td>' +
      [r.s1,r.s2,r.s3,r.s4,r.s5].map(function(n){ return '<td>' + ball(n,'main','sm') + '</td>'; }).join('') +
      '<td>' + ball(r.db,'db','sm') + '</td>' +
      '<td class="tong-cell">' + (r.tong||'') + '</td>' +
    '</tr>';
  }).join('');
  if (append) tbody.insertAdjacentHTML('beforeend', html);
  else tbody.innerHTML = html;
}

// ─── SAVE PICKS ───────────────────────────────────────
function initSaved() {
  try { state.saved = JSON.parse(localStorage.getItem('lotto_saved') || '[]'); } catch(e) { state.saved = []; }
  updateSavedNav();
}

function persistSaved() {
  localStorage.setItem('lotto_saved', JSON.stringify(state.saved));
  updateSavedNav();
  renderSaved();
}

function updateSavedNav() {
  var cnt = state.saved.length;
  var el = document.getElementById('saved-count');
  if (el) el.textContent = cnt;
  var link = document.getElementById('saved-nav-link');
  if (link) link.classList.toggle('hidden', cnt === 0);
}

function toggleSave(idx) {
  if (!state.predictions) return;
  var p = state.predictions.predictions[idx];
  if (!p) return;
  var key = (p.nums||[]).join(',') + '|' + p.db;
  var existIdx = state.saved.findIndex(function(s){ return s._key === key; });
  if (existIdx >= 0) {
    state.saved.splice(existIdx, 1);
    showToast('Đã xóa khỏi danh sách lưu.', 'info');
  } else {
    var entry = Object.assign({}, p, { _key: key, _saved: new Date().toLocaleDateString('vi-VN') });
    state.saved.unshift(entry);
    showToast('Đã lưu bộ số!', 'success');
  }
  persistSaved();
  // Update the save button
  var btn = document.getElementById('save-btn-' + idx);
  if (btn) {
    var isSaved = existIdx < 0;
    btn.textContent = isSaved ? '★ Đã lưu' : '☆ Save';
    btn.classList.toggle('act-btn--saved', isSaved);
  }
}

function clearSaved() {
  state.saved = [];
  persistSaved();
  showToast('Đã xóa tất cả bộ số đã lưu.', 'info');
}

function renderSaved() {
  var emptyEl = document.getElementById('saved-empty');
  var listEl  = document.getElementById('saved-list');
  if (!listEl) return;

  if (state.saved.length === 0) {
    if (emptyEl) emptyEl.classList.remove('hidden');
    listEl.innerHTML = '';
    return;
  }
  if (emptyEl) emptyEl.classList.add('hidden');

  listEl.innerHTML = state.saved.map(function(p, i) {
    var sum = (p.nums||[]).reduce(function(a,b){return a+b;}, 0);
    return '<div class="pred-card">' +
      '<div class="pred-card__body">' +
        '<div class="pred-card__head">' +
          '<div class="pred-card__meta"><span class="pred-card__name">Lưu ' + (p._saved||'') + '</span></div>' +
          '<button class="act-btn" onclick="deleteSaved(' + i + ')">✕ Xóa</button>' +
        '</div>' +
        '<div class="pred-card__balls">' +
          (p.nums||[]).map(function(n){ return ball(n); }).join('') +
          '<span class="pred-card__sep">|</span>' + ball(p.db,'db') +
        '</div>' +
        '<div class="pred-card__tags">' +
          '<span style="font-size:.7rem;color:var(--text-3)">Σ' + sum + '</span>' +
          renderTags(p.tags||[]) +
        '</div>' +
      '</div>' +
    '</div>';
  }).join('');
}

function deleteSaved(i) {
  state.saved.splice(i, 1);
  persistSaved();
}

// ─── SHARE ────────────────────────────────────────────
async function shareSet(idx) {
  if (!state.predictions) return;
  var p = state.predictions.predictions[idx];
  if (!p) return;
  var text = '#' + (idx+1) + ' AI PICK\n' + (p.nums||[]).map(pad).join(' · ') + '  |  DB: ' + pad(p.db) +
    '\nConfidence: ' + (p.confidence||0) + '%' +
    '\nhttps://lotto535.fly.dev';
  try {
    if (navigator.share) { await navigator.share({ text: text }); }
    else { await navigator.clipboard.writeText(text); showToast('Đã copy bộ số!', 'success'); }
  } catch(e) { /* user cancelled */ }
}

// ─── THEME ────────────────────────────────────────────
function initTheme() {
  var saved = localStorage.getItem('theme') || 'dark';
  applyTheme(saved);
  var btn = document.getElementById('theme-btn');
  if (btn) btn.addEventListener('click', function() {
    var cur = document.documentElement.getAttribute('data-theme');
    applyTheme(cur === 'dark' ? 'light' : 'dark');
  });
}
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('theme', t);
  var sun  = document.getElementById('icon-sun');
  var moon = document.getElementById('icon-moon');
  if (sun)  sun.classList.toggle('hidden', t === 'dark');
  if (moon) moon.classList.toggle('hidden', t === 'light');
}

// ─── NAVBAR ───────────────────────────────────────────
function initNavbar() {
  window.addEventListener('scroll', function() {
    var nb = document.getElementById('navbar');
    if (nb) nb.classList.toggle('scrolled', window.scrollY > 10);
    var top = document.getElementById('btn-top');
    if (top) top.classList.toggle('hidden', window.scrollY < 400);
  });

  var hb = document.getElementById('hamburger');
  if (hb) hb.addEventListener('click', function() {
    var nav = document.getElementById('nav-links');
    if (!nav) return;
    var open = nav.classList.toggle('open');
    this.classList.toggle('open', open);
    this.setAttribute('aria-expanded', String(open));
  });

  document.querySelectorAll('.nav-links a').forEach(function(a) {
    a.addEventListener('click', function() {
      var nav = document.getElementById('nav-links');
      var hb  = document.getElementById('hamburger');
      if (nav) nav.classList.remove('open');
      if (hb)  { hb.classList.remove('open'); hb.setAttribute('aria-expanded','false'); }
    });
  });

  // Tab: prediction window
  document.querySelectorAll('[data-window]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      document.querySelectorAll('[data-window]').forEach(function(b){b.classList.remove('active');});
      this.classList.add('active');
      state.window = parseInt(this.dataset.window) || 0;
      doRegenerate();
    });
  });

  // Tab: frequency
  document.querySelectorAll('[data-freq]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      document.querySelectorAll('[data-freq]').forEach(function(b){b.classList.remove('active');});
      this.classList.add('active');
      loadFrequency(parseInt(this.dataset.freq)||0);
    });
  });
}

// ─── SESSION INFO ─────────────────────────────────────
function updateSessionInfo() {
  var dateEl = document.getElementById('hero-date');
  var sessEl = document.getElementById('hero-session');
  var now = new Date();
  if (dateEl) dateEl.textContent = now.toLocaleDateString('vi-VN', {weekday:'short', day:'2-digit', month:'2-digit'});
  var h = now.getHours();
  var sess = h < 13 ? 'Trước kỳ 13H' : h < 21 ? 'Sau kỳ 13H · Chờ 21H' : 'Sau kỳ 21H';
  if (sessEl) sessEl.textContent = sess;
}

// ─── TOAST ────────────────────────────────────────────
function showToast(msg, type, dur) {
  type = type||'info'; dur = dur||3000;
  var c = document.getElementById('toast-container');
  if (!c) return;
  var t = document.createElement('div');
  t.className = 'toast toast--' + type;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(function() {
    t.style.opacity = '0'; t.style.transform = 'scale(0.9)'; t.style.transition = '0.2s';
    setTimeout(function(){ t.remove(); }, 200);
  }, dur);
}

// ─── BOOT ─────────────────────────────────────────────
init();