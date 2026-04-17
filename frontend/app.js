/* LottoAI v4 — app.js — Multi-game: Lotto 5/35, Mega 6/45, Power 6/55 */
'use strict';

const API = '';

// ─── SEO PER GAME ─────────────────────────────────────
const SEO_TITLE = {
  '535': 'LottoAI — AI Dự Đoán Lotto 5/35 · Phân Tích Vietlott',
  '645': 'LottoAI — AI Dự Đoán Mega 6/45 · Phân Tích Vietlott',
  '655': 'LottoAI — AI Dự Đoán Power 6/55 · Phân Tích Vietlott',
};
const SEO_DESC = {
  '535': 'AI phân tích Lotto 5/35: tần suất, số nóng, số quá hạn. 5 bộ số dự đoán mỗi kỳ. Cập nhật tự động từ vietlott.vn.',
  '645': 'AI phân tích Mega 6/45: tần suất, số nóng, số quá hạn. 5 bộ số dự đoán mỗi kỳ. Cập nhật T4, T6, CN từ vietlott.vn.',
  '655': 'AI phân tích Power 6/55: tần suất, số nóng, số quá hạn. Cả Power ball 01-55. Cập nhật T3, T5, T7 từ vietlott.vn.',
};

// ─── GAME CONFIG ─────────────────────────────────────
const GAMES = {
  '535': {
    id: '535', label: 'Lotto 5/35',
    mainN: 5, mainMax: 35, hasDb: true, hasPower: false,
    dbLabel: 'DB', dbBallCls: 'db',
    schedule: '2 lần/ngày · 13H & 21H',
    freqLabel: 'Phân tích thống kê số 1–35',
  },
  '645': {
    id: '645', label: 'Mega 6/45',
    mainN: 6, mainMax: 45, hasDb: false, hasPower: false,
    dbLabel: null, dbBallCls: null,
    schedule: '3 lần/tuần · T4 · T6 · CN',
    freqLabel: 'Phân tích thống kê số 1–45',
  },
  '655': {
    id: '655', label: 'Power 6/55',
    mainN: 6, mainMax: 55, hasDb: false, hasPower: true,
    dbLabel: 'Power', dbBallCls: 'power',
    schedule: '3 lần/tuần · T3 · T5 · T7',
    freqLabel: 'Phân tích thống kê số 1–55',
  },
};

const REGEN_MSGS = [
  'Analyzing patterns...',
  'Detecting anomalies...',
  'Computing frequency clusters...',
  'Generating optimized sets...',
  'Finalizing...',
];

let state = {
  game: '535',
  predictions: null,
  latest: [],
  stats: null,
  window: 30,
  histPage: 1,
  saved: [],
  regenTimer: null,
  explainOpen: new Set(),
  _feat: null,
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

// ─── GAME HELPERS ────────────────────────────────────
function gameParam() { return '?game=' + state.game; }
function gameCfg() { return GAMES[state.game]; }

function switchGame(g) {
  if (!GAMES[g] || g === state.game) return;
  state.game = g;
  state.predictions = null;
  state.latest = [];
  state.histPage = 1;

  document.querySelectorAll('.game-tab').forEach(function (b) {
    b.classList.toggle('active', b.dataset.game === g);
    b.setAttribute('aria-selected', b.dataset.game === g ? 'true' : 'false');
  });

  var heroTitle = document.getElementById('hero-game-title');
  if (heroTitle) heroTitle.textContent = GAMES[g].label;
  var heroSched = document.getElementById('hero-schedule');
  if (heroSched) heroSched.textContent = GAMES[g].schedule;
  var predSub = document.getElementById('pred-section-sub');
  if (predSub) predSub.textContent = 'Scoring: Tần suất (40%) · Gap (30%) · Recent (30%) · ' + GAMES[g].label;
  var freqSub = document.getElementById('freq-section-sub');
  if (freqSub) freqSub.textContent = GAMES[g].freqLabel;

  updateHistoryHeader();

  // Update SEO meta tags dynamically
  document.title = SEO_TITLE[g];
  var metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) metaDesc.setAttribute('content', SEO_DESC[g]);
  var ogTitle = document.querySelector('meta[property="og:title"]');
  if (ogTitle) ogTitle.setAttribute('content', SEO_TITLE[g]);
  var ogDesc = document.querySelector('meta[property="og:description"]');
  if (ogDesc) ogDesc.setAttribute('content', SEO_DESC[g]);

  loadAll();
}

function updateHistoryHeader() {
  var thead = document.getElementById('hist-thead');
  if (!thead) return;
  var cfg = gameCfg();
  var cols = '<th>Kỳ</th><th>Ngày</th>';
  if (cfg.id === '535') cols += '<th>Buổi</th>';
  for (var i = 1; i <= cfg.mainN; i++) cols += '<th>Số ' + i + '</th>';
  if (cfg.hasDb || cfg.hasPower) cols += '<th>' + cfg.dbLabel + '</th>';
  cols += '<th>Tổng</th>';
  thead.innerHTML = '<tr>' + cols + '</tr>';
}

// ─── INIT ─────────────────────────────────────────────
function init() {
  initTheme();
  initNavbar();
  initSaved();
  updateSessionInfo();
  initGameTabs();
  loadAll();
}

function initGameTabs() {
  document.querySelectorAll('.game-tab').forEach(function (btn) {
    btn.addEventListener('click', function () { switchGame(this.dataset.game); });
  });
  var heroTitle = document.getElementById('hero-game-title');
  if (heroTitle) heroTitle.textContent = GAMES['535'].label;
  var predSub = document.getElementById('pred-section-sub');
  if (predSub) predSub.textContent = 'Scoring: Tần suất (40%) · Gap (30%) · Recent (30%) · Lotto 5/35';
}

async function loadAll() {
  showPredSkeleton();
  hideError();
  try {
    var g = gameParam();
    const [preds, stats, latest] = await Promise.all([
      fetchJSON(API + '/api/predictions' + g + '&window=' + state.window),
      fetchJSON(API + '/api/stats' + g),
      fetchJSON(API + '/api/latest' + g + '&n=20'),
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
  state.regenTimer = setInterval(function () {
    if (lblEl) lblEl.textContent = REGEN_MSGS[phase % REGEN_MSGS.length];
    phase++;
  }, 700);
  try {
    const preds = await fetchJSON(API + '/api/predictions' + gameParam() + '&window=' + state.window);
    state.predictions = preds;
    renderHeroFeatured(preds);
    renderPredictions(preds);
    renderHotGap(preds);
    showToast('New prediction set generated!', 'success');
  } catch (err) {
    showToast('Could not generate. Try again.', 'error');
  } finally {
    clearInterval(state.regenTimer);
    btn.disabled = false;
    if (lblEl) lblEl.innerHTML = '&#x1F3B2; Generate New';
  }
}

async function loadFrequency(win) {
  try {
    const freq = await fetchJSON(API + '/api/frequency' + gameParam() + '&window=' + win);
    renderInsights(freq, win);
    renderFreqChart(freq);
  } catch (e) { console.warn('[freq]', e); }
}

async function loadBacktest() {
  try {
    const bt = await fetchJSON(API + '/api/backtest' + gameParam());
    renderBacktest(bt);
  } catch (e) {
    const el = document.getElementById('backtest-metrics');
    if (el) el.innerHTML = '<p style="color:var(--text-3);font-size:.8rem;padding:12px">Cần thêm dữ liệu để chạy backtest (≥150 kỳ).</p>';
  }
}

async function loadMoreHistory() {
  state.histPage += 1;
  try {
    var rows = await fetchJSON(API + '/api/latest' + gameParam() + '&n=' + (state.histPage * 20));
    state.latest = rows;
    renderHistory(rows, false);
  } catch (e) { showToast('Không tải thêm được.', 'error'); }
}

// ─── MANUAL CRAWL ─────────────────────────────────────
async function doCrawl() {
  var btn = document.getElementById('btn-crawl');
  if (!btn || btn.disabled) return;
  btn.disabled = true;
  var origHtml = btn.innerHTML;
  btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Đang crawl...';
  try {
    var res = await fetch(API + '/api/crawl' + gameParam(), {
      method: 'POST',
      signal: AbortSignal.timeout(30000),
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    var data = await res.json();
    if (data.is_new && data.result) {
      showToast('✅ Đã cập nhật kỳ #' + data.result.ky + ' (' + GAMES[state.game].label + ')', 'success', 4000);
      await loadAll();
    } else {
      showToast('ℹ️ Đã có dữ liệu mới nhất rồi.', 'info');
    }
  } catch (e) {
    console.error('[crawl]', e);
    showToast('❌ Crawl thất bại. Thử lại sau.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = origHtml;
  }
}

// ─── RENDER HELPERS ───────────────────────────────────
function ball(num, cls, size) {
  cls = cls || 'main'; size = size ? ' ball--' + size : '';
  return '<span class="ball ball--' + cls + size + '">' + pad(num) + '</span>';
}
function pad(n) { return String(n).padStart(2, '0'); }
function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

function showPredSkeleton() {
  var el = document.getElementById('pred-list');
  if (!el) return;
  var cfg = gameCfg();
  var h = '';
  for (var i = 0; i < 5; i++) {
    h += '<div class="pred-card" style="opacity:.4"><div class="pred-card__body"><div class="pred-card__balls">';
    for (var j = 0; j < cfg.mainN; j++) h += '<div class="s-ball s-ball--main"></div>';
    if (cfg.hasDb || cfg.hasPower) h += '<div class="pred-card__sep">|</div><div class="s-ball s-ball--db"></div>';
    h += '</div></div></div>';
  }
  el.innerHTML = h;
}
function showError() {
  var e = document.getElementById('pred-error');
  if (e) e.classList.remove('hidden');
  var l = document.getElementById('pred-list');
  if (l) l.innerHTML = '';
}
function hideError() {
  var e = document.getElementById('pred-error');
  if (e) e.classList.add('hidden');
}

// ─── RENDER STATS BAR ─────────────────────────────────
function renderStats(stats, preds) {
  var el = document.getElementById('stats-bar');
  if (!el) return;
  var s = stats.sum_stats || {};
  var lat = stats.latest || {};
  el.innerHTML = [
    { val: stats.total || 0, label: 'Tổng kỳ quay' },
    { val: lat.ky ? '#' + pad(lat.ky) : '—', label: 'Kỳ gần nhất' },
    { val: lat.ngay || '—', label: 'Ngày quay' },
    { val: s.avg ? 'Σ' + Math.round(s.avg) : '—', label: 'Tổng TB' },
  ].map(function (d) {
    return '<div class="stat-pill"><div class="stat-pill__val">' + esc(String(d.val)) +
      '</div><div class="stat-pill__label">' + esc(d.label) + '</div></div>';
  }).join('');
  var hd = document.getElementById('hero-draws');
  if (hd) hd.textContent = stats.total || '--';
}

// ─── RENDER HERO LAST DRAW ────────────────────────────
function renderHeroLastDraw(r) {
  if (!r) return;
  var el = document.getElementById('hero-balls');
  if (!el) return;
  var cfg = gameCfg();
  var balls = [];
  for (var i = 1; i <= cfg.mainN; i++) balls.push(r['s' + i]);
  var html = balls.map(function (n) { return ball(n, 'main'); }).join('');
  if (cfg.hasPower && r.power) html += ball(r.power, 'power');
  else if (cfg.hasDb && r.db) html += ball(r.db, 'db');
  el.innerHTML = html;
}

// ─── RENDER HERO FEATURED CARD ────────────────────────
function renderHeroFeatured(preds) {
  var p0 = preds.predictions && preds.predictions[0];
  if (!p0) return;
  var cfg = gameCfg();
  var bEl = document.getElementById('feat-balls');
  if (bEl) {
    var html = (p0.nums || []).map(function (n) { return ball(n, 'main', 'lg'); }).join('');
    if (cfg.hasPower && p0.db) html += '<div class="feat-card__sep">|</div>' + ball(p0.db, 'power', 'lg');
    else if (cfg.hasDb && p0.db) html += '<div class="feat-card__sep">|</div>' + ball(p0.db, 'db', 'lg');
    bEl.innerHTML = html;
  }
  var fill = document.getElementById('feat-conf-fill');
  if (fill) fill.style.width = (p0.confidence || 0) + '%';
  var lbl = document.getElementById('feat-conf-label');
  if (lbl) lbl.textContent = 'Confidence: ' + (p0.confidence || 0) + '%';
  var tagsEl = document.getElementById('feat-tags');
  if (tagsEl) tagsEl.innerHTML = renderTags(p0.tags || []);
  state._feat = p0;
}

// ─── RENDER PREDICTIONS ───────────────────────────────
function buildExplain(p, preds) {
  if (!preds) return '';
  var cfg = gameCfg();
  var hotSet = new Set((preds.hot_numbers || []).map(function (r) { return r.so; }));
  var gapArr = preds.gap_numbers || [];
  var gapSet = new Set(gapArr.map(function (r) { return r.so; }));
  var nums = p.nums || [];
  var hotNums = nums.filter(function (n) { return hotSet.has(n); });
  var gapNums = nums.filter(function (n) { return gapSet.has(n); });
  var evens = nums.filter(function (n) { return n % 2 === 0; });
  var lo = nums.filter(function (n) { return n <= Math.floor(cfg.mainMax / 3); }).length;
  var mid = nums.filter(function (n) { return n > Math.floor(cfg.mainMax / 3) && n <= Math.floor(cfg.mainMax * 2 / 3); }).length;
  var hi = nums.filter(function (n) { return n > Math.floor(cfg.mainMax * 2 / 3); }).length;
  var avgGap = gapArr.length > 0 ? Math.round(gapArr.reduce(function (a, r) { return a + r.gap; }, 0) / gapArr.length) : 0;
  return '<p>🔥 <strong>' + hotNums.length + ' hot numbers</strong>' +
    (hotNums.length > 0 ? ' (' + hotNums.map(pad).join(', ') + ')' : '') +
    ': xuất hiện nhiều trong ' + (preds.window || 30) + ' kỳ gần nhất</p>' +
    (gapNums.length > 0 ? '<p>⏳ <strong>' + gapNums.length + ' overdue</strong>' +
      ' (' + gapNums.map(pad).join(', ') + '): avg gap ~' + avgGap + ' kỳ</p>' : '') +
    '<p>⚖️ Tỷ lệ chẵn/lẻ: <strong>' + evens.length + '/' + (nums.length - evens.length) + '</strong></p>' +
    '<p>📊 Phân bố: thấp <strong>' + lo + '</strong> · giữa <strong>' + mid + '</strong> · cao <strong>' + hi + '</strong></p>';
}

function renderPredictions(preds) {
  var el = document.getElementById('pred-list');
  if (!el) return;
  var cfg = gameCfg();
  var ps = preds.predictions || [];
  var savedSet = new Set(state.saved.map(function (s) { return s._key; }));
  el.innerHTML = ps.map(function (p, i) {
    var key = (p.nums || []).join(',') + '|' + (p.db || 0) + '|' + state.game;
    var isSaved = savedSet.has(key);
    var sum = (p.nums || []).reduce(function (a, b) { return a + b; }, 0);
    var dbHtml = '';
    if (cfg.hasPower && p.db) dbHtml = '<span class="pred-card__sep">|</span>' + ball(p.db, 'power');
    else if (cfg.hasDb && p.db) dbHtml = '<span class="pred-card__sep">|</span>' + ball(p.db, 'db');
    return (
      '<div class="pred-card" id="pred-card-' + i + '">' +
      '<div class="pred-card__body">' +
      '<div class="pred-card__head">' +
      '<div class="pred-card__meta">' +
      '<span class="pred-card__num">#' + (i + 1) + '</span>' +
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
      (p.nums || []).map(function (n) { return ball(n); }).join('') + dbHtml +
      '</div>' +
      '<div class="pred-card__conf">' +
      '<div class="pred-card__conf-row">' +
      '<div class="conf-bar" style="flex:1"><div class="conf-bar__fill" style="width:' + (p.confidence || 0) + '%"></div></div>' +
      '<span class="pred-card__conf-pct">' + (p.confidence || 0) + '%</span>' +
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
  return (tags || []).map(function (t) {
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
  if (hotEl) hotEl.innerHTML = hot.map(function (r) {
    return ball(r.so, 'hot', 'sm') + '<span style="font-size:.65rem;color:var(--text-3);margin-right:4px">' + (r.freq_30 || 0) + 'x</span>';
  }).join('');
  if (gapEl) gapEl.innerHTML = gap.map(function (r) {
    return ball(r.so, 'gap', 'sm') + '<span style="font-size:.65rem;color:var(--text-3);margin-right:4px">' + (r.gap || 0) + 'kỳ</span>';
  }).join('');
  if (hotTrend && hot.length > 0) {
    var avg30 = hot.reduce(function (a, r) { return a + r.freq_30; }, 0) / hot.length;
    hotTrend.textContent = '↑ TB ' + avg30.toFixed(1) + 'x mỗi 30 kỳ';
  }
  if (gapTrend && gap.length > 0) {
    var avgGap = gap.reduce(function (a, r) { return a + r.gap; }, 0) / gap.length;
    gapTrend.textContent = 'Avg gap: ~' + Math.round(avgGap) + ' kỳ';
  }
}

// ─── INSIGHTS + FREQ CHART ────────────────────────────
function renderInsights(freqData, win) {
  var grid = document.getElementById('insight-grid');
  if (!grid) return;
  var cfg = gameCfg();
  var sorted = freqData.slice().sort(function (a, b) { return b.count - a.count; });
  var byNum = freqData.slice().sort(function (a, b) { return a.so - b.so; });
  var total = byNum.reduce(function (a, r) { return a + r.count; }, 0);
  var evens = byNum.filter(function (r) { return r.so % 2 === 0; }).reduce(function (a, r) { return a + r.count; }, 0);
  var evenPct = total > 0 ? Math.round(evens / total * 100) : 0;
  var step = Math.ceil(cfg.mainMax / 5);
  var ranges = [];
  for (var s = 1; s <= cfg.mainMax; s += step) ranges.push([s, Math.min(s + step - 1, cfg.mainMax)]);
  var rangeTotals = ranges.map(function (r) {
    return byNum.filter(function (d) { return d.so >= r[0] && d.so <= r[1]; }).reduce(function (a, d) { return a + d.count; }, 0);
  });
  var maxRangeIdx = rangeTotals.indexOf(Math.max.apply(null, rangeTotals));
  var maxRange = ranges[maxRangeIdx];
  var minN = sorted[sorted.length - 1] ? sorted[sorted.length - 1].count : 0;
  grid.innerHTML = [
    { label: 'Most Active Range', val: maxRange[0] + '–' + maxRange[1], sub: rangeTotals[maxRangeIdx] + ' lần xuất hiện' },
    { label: 'Odd / Even Split', val: (100 - evenPct) + '% / ' + evenPct + '%', sub: 'Lẻ / Chẵn' },
    { label: 'Số ít xuất hiện nhất', val: pad(sorted[sorted.length - 1].so), sub: minN + ' lần (' + (win ? win + ' kỳ' : 'all') + ')' },
  ].map(function (d) {
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
  var sorted = freqData.slice().sort(function (a, b) { return b.count - a.count; });
  var maxCount = sorted[0] ? sorted[0].count : 1;
  var top5Set = new Set(sorted.slice(0, 5).map(function (r) { return r.so; }));
  var top15Set = new Set(sorted.slice(0, 15).map(function (r) { return r.so; }));
  var bot5Set = new Set(sorted.slice(-5).map(function (r) { return r.so; }));
  var byNum = freqData.slice().sort(function (a, b) { return a.so - b.so; });
  el.innerHTML = byNum.map(function (r) {
    var pct = maxCount > 0 ? (r.count / maxCount * 100).toFixed(1) : 0;
    var rowCls = '', badge = '';
    if (top5Set.has(r.so)) { rowCls = ' freq-row--top5'; badge = '<span class="freq-badge freq-badge--hot">HOT</span>'; }
    else if (top15Set.has(r.so)) { rowCls = ' freq-row--top15'; }
    else if (bot5Set.has(r.so)) { rowCls = ' freq-row--bot5'; badge = '<span class="freq-badge freq-badge--cold">LOW</span>'; }
    return '<div class="freq-row' + rowCls + '">' +
      '<span class="freq-row__num">' + pad(r.so) + '</span>' +
      '<div class="freq-row__track"><div class="freq-row__fill" style="width:' + pct + '%"></div></div>' +
      '<span class="freq-row__count">' + r.count + '</span>' + badge +
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
    { val: bt.accuracy_pct != null ? bt.accuracy_pct : '—', pct: '%', label: 'Hit ≥2 số / top-N' },
    { val: bt.avg_hits != null ? bt.avg_hits : '—', pct: '', label: 'Avg số trúng (top-2N)' },
    { val: bt.hit3_pct != null ? bt.hit3_pct : '—', pct: '%', label: 'Hit ≥3 số / top-2N' },
    { val: bt.total_tested != null ? bt.total_tested : '—', pct: '', label: 'Kỳ kiểm tra' },
  ];
  el.innerHTML = metrics.map(function (m) {
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
  var cfg = gameCfg();
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="12" class="empty-cell">Không có dữ liệu</td></tr>';
    return;
  }
  var html = rows.map(function (r) {
    var cells = '<td class="ky-cell">#' + pad(r.ky) + '</td><td class="ngay-cell">' + (r.ngay || '') + '</td>';
    if (cfg.id === '535') {
      cells += '<td><span class="' + (r.buoi === 'S' ? 'buoi-s' : 'buoi-t') + '">' + (r.buoi === 'S' ? '13H' : '21H') + '</span></td>';
    }
    for (var i = 1; i <= cfg.mainN; i++) cells += '<td>' + ball(r['s' + i], 'main', 'sm') + '</td>';
    if (cfg.hasPower && r.power) cells += '<td>' + ball(r.power, 'power', 'sm') + '</td>';
    else if (cfg.hasDb && r.db) cells += '<td>' + ball(r.db, 'db', 'sm') + '</td>';
    cells += '<td class="tong-cell">' + (r.tong || '') + '</td>';
    return '<tr>' + cells + '</tr>';
  }).join('');
  updateHistoryHeader();
  if (append) tbody.insertAdjacentHTML('beforeend', html);
  else tbody.innerHTML = html;
}

// ─── SAVE PICKS ───────────────────────────────────────
function initSaved() {
  try { state.saved = JSON.parse(localStorage.getItem('lotto_saved') || '[]'); } catch (e) { state.saved = []; }
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
  var key = (p.nums || []).join(',') + '|' + (p.db || 0) + '|' + state.game;
  var existIdx = state.saved.findIndex(function (s) { return s._key === key; });
  if (existIdx >= 0) {
    state.saved.splice(existIdx, 1);
    showToast('Đã xóa khỏi danh sách lưu.', 'info');
  } else {
    var entry = Object.assign({}, p, {
      _key: key,
      _game: state.game,
      _gameLabel: GAMES[state.game].label,
      _saved: new Date().toLocaleDateString('vi-VN'),
    });
    state.saved.unshift(entry);
    showToast('Đã lưu bộ số! (' + GAMES[state.game].label + ')', 'success');
  }
  persistSaved();
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
  var listEl = document.getElementById('saved-list');
  if (!listEl) return;
  if (state.saved.length === 0) {
    if (emptyEl) emptyEl.classList.remove('hidden');
    listEl.innerHTML = '';
    return;
  }
  if (emptyEl) emptyEl.classList.add('hidden');
  listEl.innerHTML = state.saved.map(function (p, i) {
    var sum = (p.nums || []).reduce(function (a, b) { return a + b; }, 0);
    var gcfg = GAMES[p._game || '535'];
    var dbHtml = '';
    if (gcfg.hasPower && p.db) dbHtml = '<span class="pred-card__sep">|</span>' + ball(p.db, 'power');
    else if (gcfg.hasDb && p.db) dbHtml = '<span class="pred-card__sep">|</span>' + ball(p.db, 'db');
    return '<div class="pred-card">' +
      '<div class="pred-card__body">' +
      '<div class="pred-card__head">' +
      '<div class="pred-card__meta"><span class="pred-card__name">' + esc(p._gameLabel || 'Lotto') + ' · ' + (p._saved || '') + '</span></div>' +
      '<button class="act-btn" onclick="deleteSaved(' + i + ')">✕ Xóa</button>' +
      '</div>' +
      '<div class="pred-card__balls">' + (p.nums || []).map(function (n) { return ball(n); }).join('') + dbHtml + '</div>' +
      '<div class="pred-card__tags"><span style="font-size:.7rem;color:var(--text-3)">Σ' + sum + '</span>' + renderTags(p.tags || []) + '</div>' +
      '</div>' +
      '</div>';
  }).join('');
}
function deleteSaved(i) { state.saved.splice(i, 1); persistSaved(); }

// ─── SHARE ────────────────────────────────────────────
async function shareSet(idx) {
  if (!state.predictions) return;
  var p = state.predictions.predictions[idx];
  if (!p) return;
  var cfg = gameCfg();
  var dbPart = '';
  if ((cfg.hasDb || cfg.hasPower) && p.db) dbPart = '  |  ' + cfg.dbLabel + ': ' + pad(p.db);
  var text = '[' + cfg.label + '] #' + (idx + 1) + ' AI PICK\n' +
    (p.nums || []).map(pad).join(' · ') + dbPart +
    '\nConfidence: ' + (p.confidence || 0) + '%\nhttps://lotto535.fly.dev';
  try {
    if (navigator.share) { await navigator.share({ text: text }); }
    else { await navigator.clipboard.writeText(text); showToast('Đã copy bộ số!', 'success'); }
  } catch (e) { /* user cancelled */ }
}

// ─── THEME ────────────────────────────────────────────
function initTheme() {
  var saved = localStorage.getItem('theme') || 'dark';
  applyTheme(saved);
  var btn = document.getElementById('theme-btn');
  if (btn) btn.addEventListener('click', function () {
    var cur = document.documentElement.getAttribute('data-theme');
    applyTheme(cur === 'dark' ? 'light' : 'dark');
  });
}
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('theme', t);
  var sun = document.getElementById('icon-sun');
  var moon = document.getElementById('icon-moon');
  if (sun) sun.classList.toggle('hidden', t === 'dark');
  if (moon) moon.classList.toggle('hidden', t === 'light');
}

// ─── NAVBAR ───────────────────────────────────────────
function initNavbar() {
  window.addEventListener('scroll', function () {
    var nb = document.getElementById('navbar');
    if (nb) nb.classList.toggle('scrolled', window.scrollY > 10);
    var top = document.getElementById('btn-top');
    if (top) top.classList.toggle('hidden', window.scrollY < 400);
  });
  var hb = document.getElementById('hamburger');
  if (hb) hb.addEventListener('click', function () {
    var nav = document.getElementById('nav-links');
    if (!nav) return;
    var open = nav.classList.toggle('open');
    this.classList.toggle('open', open);
    this.setAttribute('aria-expanded', String(open));
  });
  document.querySelectorAll('.nav-links a').forEach(function (a) {
    a.addEventListener('click', function () {
      var nav = document.getElementById('nav-links');
      var hb = document.getElementById('hamburger');
      if (nav) nav.classList.remove('open');
      if (hb) { hb.classList.remove('open'); hb.setAttribute('aria-expanded', 'false'); }
    });
  });
  // Tab: prediction window
  document.querySelectorAll('[data-window]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('[data-window]').forEach(function (b) { b.classList.remove('active'); });
      this.classList.add('active');
      state.window = parseInt(this.dataset.window) || 0;
      doRegenerate();
    });
  });
  // Tab: frequency
  document.querySelectorAll('[data-freq]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('[data-freq]').forEach(function (b) { b.classList.remove('active'); });
      this.classList.add('active');
      loadFrequency(parseInt(this.dataset.freq) || 0);
    });
  });
}

// ─── SESSION INFO ─────────────────────────────────────
function updateSessionInfo() {
  var dateEl = document.getElementById('hero-date');
  var sessEl = document.getElementById('hero-session');
  var now = new Date();
  if (dateEl) dateEl.textContent = now.toLocaleDateString('vi-VN', { weekday: 'short', day: '2-digit', month: '2-digit' });
  var h = now.getHours();
  var sess = h < 13 ? 'Trước kỳ 13H' : h < 21 ? 'Sau kỳ 13H · Chờ 21H' : 'Sau kỳ 21H';
  if (sessEl) sessEl.textContent = sess;
}

// ─── TOAST ────────────────────────────────────────────
function showToast(msg, type, dur) {
  type = type || 'info'; dur = dur || 3000;
  var c = document.getElementById('toast-container');
  if (!c) return;
  var t = document.createElement('div');
  t.className = 'toast toast--' + type;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(function () {
    t.style.opacity = '0'; t.style.transform = 'scale(0.9)'; t.style.transition = '0.2s';
    setTimeout(function () { t.remove(); }, 200);
  }, dur);
}

// ─── BOOT ─────────────────────────────────────────────
init();
