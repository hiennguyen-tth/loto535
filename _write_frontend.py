from pathlib import Path

BASE = Path("/Users/hien.nguyen13/Desktop/loto5-35/frontend")

# ─── index.html ──────────────────────────────────────────────
(BASE / "index.html").write_text('''<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <!-- ── SEO ─────────────────────────────────────────────── -->
  <title>Lotto 5/35 AI Dự Đoán — Soi Cầu Xổ Số 5/35 Hôm Nay</title>
  <meta name="description" content="Dự đoán Lotto 5/35 bằng AI thống kê — Top 5 bộ số xác suất cao, cập nhật sau mỗi kỳ quay. Tần suất, số quá hạn, backtest walk-forward." />
  <meta name="keywords" content="dự đoán lotto 5/35, soi cầu lotto 5/35, lotto 5/35 hôm nay, kết quả lotto 5/35, thống kê lotto 5/35, lotto 5 35 AI, soi cầu xổ số 5/35, dự đoán xổ số 5 số, xổ số 5/35 hôm nay" />
  <meta name="robots" content="index, follow" />
  <meta name="author" content="Lotto 5/35 AI Team" />
  <link rel="canonical" href="https://lotto535.fly.dev/" />

  <!-- ── Open Graph ────────────────────────────────────────── -->
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Lotto 5/35 AI" />
  <meta property="og:title" content="Lotto 5/35 AI Dự Đoán — Soi Cầu Hôm Nay" />
  <meta property="og:description" content="Dự đoán Lotto 5/35 bằng AI thống kê. Top 5 bộ số cập nhật realtime. Tần suất, số quá hạn, backtest." />
  <meta property="og:url" content="https://lotto535.fly.dev/" />
  <meta property="og:locale" content="vi_VN" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="Lotto 5/35 AI Dự Đoán" />
  <meta name="twitter:description" content="Soi cầu Lotto 5/35 bằng AI — Top 5 bộ số cập nhật sau mỗi kỳ." />

  <!-- ── JSON-LD ────────────────────────────────────────────── -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "name": "Lotto 5/35 AI Predictor",
    "url": "https://lotto535.fly.dev/",
    "description": "Hệ thống dự đoán Lotto 5/35 sử dụng phân tích thống kê: tần suất, số quá hạn, điểm tổng hợp và backtest walk-forward.",
    "applicationCategory": "EntertainmentApplication",
    "operatingSystem": "Any",
    "inLanguage": "vi",
    "offers": { "@type": "Offer", "price": "0", "priceCurrency": "VND" }
  }
  </script>

  <!-- ── AdSense ────────────────────────────────────────────── -->
  <meta name="google-adsense-account" content="ca-pub-2330743593269954" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2330743593269954" crossorigin="anonymous"></script>

  <link rel="stylesheet" href="style.css" />
</head>
<body>

  <!-- ── Header ─────────────────────────────────────────────── -->
  <header>
    <div class="header-left">
      <span class="logo">🎯</span>
      <div>
        <div class="header-title">Lotto 5/35 AI</div>
        <div class="header-sub">Soi Cầu Dự Đoán</div>
      </div>
    </div>
    <div class="header-right">
      <span id="last-update" class="update-pill">Đang tải...</span>
      <button class="refresh-btn" onclick="init()" title="Làm mới dữ liệu" aria-label="Làm mới">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
      </button>
    </div>
  </header>

  <!-- ── Error banner ───────────────────────────────────────── -->
  <div id="error-banner" class="error-banner hidden">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
    Không kết nối được đến API — <strong>lotto535.fly.dev</strong>. Kiểm tra server đang chạy.
  </div>

  <main>

    <!-- ── Stats ──────────────────────────────────────────── -->
    <div class="stats-grid" id="stats-row">
      <div class="stat-card skeleton"><div class="sk-inner"></div></div>
      <div class="stat-card skeleton"><div class="sk-inner"></div></div>
      <div class="stat-card skeleton"><div class="sk-inner"></div></div>
      <div class="stat-card skeleton"><div class="sk-inner"></div></div>
    </div>

    <!-- ── Latest kỳ ──────────────────────────────────────── -->
    <section class="card">
      <div class="card-hd">
        <h2><span class="sec-icon">📌</span> Kỳ quay mới nhất</h2>
      </div>
      <div class="card-body">
        <div id="latest-result" class="ball-row"></div>
      </div>
    </section>

    <!-- ── Predictions ────────────────────────────────────── -->
    <section class="card">
      <div class="card-hd">
        <h2><span class="sec-icon">🔮</span> Dự đoán kỳ tiếp theo</h2>
        <div class="seg-ctrl">
          <button class="seg-btn active" onclick="setPredWindow(30,this)">30 kỳ</button>
          <button class="seg-btn" onclick="setPredWindow(50,this)">50 kỳ</button>
          <button class="seg-btn" onclick="setPredWindow(9999,this)">Tất cả</button>
        </div>
      </div>
      <div class="card-body" id="predictions"></div>
    </section>

    <!-- ── AdSense slot ───────────────────────────────────── -->
    <div class="ad-wrap">
      <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-2330743593269954" data-ad-slot="auto" data-ad-format="auto" data-full-width-responsive="true"></ins>
      <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
    </div>

    <!-- ── Hot & Gap ──────────────────────────────────────── -->
    <div class="two-col">
      <section class="card">
        <div class="card-hd">
          <h2><span class="sec-icon">🔥</span> Đang hot <span class="badge hot-badge">30 kỳ</span></h2>
        </div>
        <div class="card-body">
          <div id="hot-nums" class="tag-row"></div>
        </div>
      </section>
      <section class="card">
        <div class="card-hd">
          <h2><span class="sec-icon">⏳</span> Nợ lâu nhất</h2>
        </div>
        <div class="card-body">
          <div id="gap-nums" class="tag-row"></div>
        </div>
      </section>
    </div>

    <!-- ── Frequency ──────────────────────────────────────── -->
    <section class="card">
      <div class="card-hd">
        <h2><span class="sec-icon">📊</span> Tần suất xuất hiện</h2>
        <div class="seg-ctrl">
          <button class="seg-btn active" onclick="loadFreq(0,this)">Tất cả</button>
          <button class="seg-btn" onclick="loadFreq(30,this)">30 kỳ</button>
          <button class="seg-btn" onclick="loadFreq(50,this)">50 kỳ</button>
        </div>
      </div>
      <div class="card-body">
        <div id="freq-chart" class="freq-grid"></div>
      </div>
    </section>

    <!-- ── History ────────────────────────────────────────── -->
    <section class="card">
      <div class="card-hd">
        <h2><span class="sec-icon">📋</span> Lịch sử 20 kỳ gần nhất</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Kỳ</th><th>Ngày</th><th>Buổi</th>
              <th>S1</th><th>S2</th><th>S3</th><th>S4</th><th>S5</th>
              <th>DB</th><th>Tổng</th>
            </tr>
          </thead>
          <tbody id="history-body"></tbody>
        </table>
      </div>
    </section>

  </main>

  <footer>
    ⚠️ Xổ số là trò chơi may rủi. Công cụ này chỉ mang tính phân tích thống kê, không đảm bảo kết quả.
  </footer>

  <script src="app.js"></script>
</body>
</html>
''', encoding='utf-8')
print("index.html ✓")

# ─── style.css ────────────────────────────────────────────────
(BASE / "style.css").write_text('''\
/* ══════════════════════════════════════════════════════════════
   Lotto 5/35 AI — Dark Dashboard (bingo-inspired dark theme)
══════════════════════════════════════════════════════════════ */

/* ── Tokens ──────────────────────────────────────────────────── */
:root {
  --bg:         #0f172a;
  --surface:    #1e293b;
  --surface-2:  #162032;
  --border:     rgba(255,255,255,0.07);
  --border-lg:  rgba(255,255,255,0.12);

  --indigo:     #6366f1;
  --indigo-dim: rgba(99,102,241,0.18);
  --indigo-dk:  #312e81;
  --violet:     #7c3aed;

  --hot:        #FF6B3D;
  --hot-dim:    rgba(255,107,61,0.18);
  --gap:        #FFC857;
  --gap-dim:    rgba(255,200,87,0.15);

  --text:       #e2e8f0;
  --text-2:     #94a3b8;
  --text-muted: #475569;

  --ball-main-bg:  #6366f1;
  --ball-db-bg:    #7c3aed;
  --ball-sz:       36px;

  --r-sm:  6px;
  --r-md:  12px;
  --r-lg:  16px;
  --r-xl:  20px;
  --r-full:9999px;

  --shadow: 0 4px 24px rgba(0,0,0,0.4);
  --max-w:  1040px;
  --font:   system-ui,-apple-system,"Segoe UI",sans-serif;
}

/* ── Reset ────────────────────────────────────────────────────── */
*,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }
html { scroll-behavior:smooth; }
body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:#334155; border-radius:3px; }

/* ── Header ───────────────────────────────────────────────────── */
header {
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
  padding: 0 1.5rem;
  height: 62px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid rgba(99,102,241,0.3);
  box-shadow: 0 2px 20px rgba(0,0,0,0.5);
}
.header-left { display:flex; align-items:center; gap:12px; }
.logo { font-size:1.6rem; line-height:1; filter:drop-shadow(0 2px 4px rgba(0,0,0,.4)); }
.header-title { font-size:1rem; font-weight:800; color:#a5b4fc; letter-spacing:-.02em; }
.header-sub   { font-size:.68rem; color:#6366f1; margin-top:1px; font-weight:500; }
.header-right { display:flex; align-items:center; gap:8px; }

.update-pill {
  font-size:.7rem;
  background: rgba(99,102,241,0.2);
  color:#a5b4fc;
  padding:4px 12px;
  border-radius:var(--r-full);
  border:1px solid rgba(99,102,241,0.35);
  white-space:nowrap;
}
.refresh-btn {
  width:32px; height:32px; border:none;
  border-radius:var(--r-full);
  background:rgba(255,255,255,0.1); color:#e2e8f0;
  cursor:pointer; display:flex; align-items:center; justify-content:center;
  transition:background .15s;
}
.refresh-btn:hover { background:rgba(255,255,255,0.2); }

/* ── Error banner ─────────────────────────────────────────────── */
.error-banner {
  display:flex; align-items:center; gap:8px;
  background:#450a0a; color:#fca5a5;
  border-left:4px solid #dc2626;
  padding:.75rem 1.5rem; font-size:.82rem;
}
.hidden { display:none !important; }

/* ── Main ─────────────────────────────────────────────────────── */
main {
  max-width: var(--max-w);
  margin: 0 auto;
  padding: 1.25rem 1rem 2.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* ── Stats grid ───────────────────────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4,1fr);
  gap: .75rem;
}
.stat-card {
  background: var(--surface);
  border-radius: var(--r-lg);
  padding: 1.1rem 1.1rem .9rem;
  border: 1px solid var(--border-lg);
  position: relative;
  overflow: hidden;
}
.stat-card::before {
  content:'';
  position:absolute; top:0; left:0; right:0; height:3px;
  background: linear-gradient(90deg, var(--indigo), var(--violet));
}
.stat-card .icon  { font-size:1.2rem; margin-bottom:.4rem; display:block; }
.stat-card .val   { font-size:1.8rem; font-weight:800; color:#f1f5f9; letter-spacing:-.04em; line-height:1; margin-bottom:.3rem; }
.stat-card .lbl   { font-size:.68rem; color:var(--text-muted); font-weight:600; text-transform:uppercase; letter-spacing:.06em; }

/* skeleton */
.skeleton::before { display:none; }
.sk-inner {
  height:74px; border-radius:var(--r-sm);
  background:linear-gradient(90deg,#1e293b 25%,#273449 50%,#1e293b 75%);
  background-size:200% 100%;
  animation:shimmer 1.5s infinite;
}
@keyframes shimmer {
  0%   {background-position:200% 0}
  100% {background-position:-200% 0}
}

/* ── Card ─────────────────────────────────────────────────────── */
.card {
  background: var(--surface);
  border-radius: var(--r-xl);
  border: 1px solid var(--border-lg);
  overflow: hidden;
  box-shadow: var(--shadow);
}
.card-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .9rem 1.25rem .75rem;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
  gap: .5rem;
}
.card-hd h2 {
  font-size:.88rem; font-weight:700; color:#cbd5e1;
  display:flex; align-items:center; gap:6px;
}
.sec-icon { font-size:1rem; }
.card-body { padding:.85rem 1.25rem 1.1rem; }

/* ── Two-col ───────────────────────────────────────────────────── */
.two-col { display:grid; grid-template-columns:1fr 1fr; gap:1rem; }

/* ── Badge ─────────────────────────────────────────────────────── */
.badge       { font-size:.6rem; font-weight:700; padding:2px 8px; border-radius:var(--r-full); text-transform:uppercase; letter-spacing:.06em; }
.hot-badge   { background:rgba(255,107,61,0.2); color:#FF6B3D; border:1px solid rgba(255,107,61,0.4); }

/* ── Seg control ──────────────────────────────────────────────── */
.seg-ctrl {
  display:flex; gap:3px;
  background: rgba(255,255,255,0.05);
  padding:3px; border-radius:var(--r-sm);
  border:1px solid var(--border-lg);
}
.seg-btn {
  padding:4px 13px; border:none;
  border-radius:calc(var(--r-sm) - 2px);
  background:transparent; color:var(--text-2);
  font-size:.72rem; font-weight:600;
  cursor:pointer; transition:.15s;
  font-family:var(--font); white-space:nowrap;
}
.seg-btn.active {
  background:var(--indigo); color:#fff;
  box-shadow:0 1px 6px rgba(99,102,241,.5);
}
.seg-btn:not(.active):hover { background:rgba(255,255,255,0.08); color:var(--text); }

/* ── Balls ─────────────────────────────────────────────────────── */
.ball-row   { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.ball {
  width:var(--ball-sz); height:var(--ball-sz);
  border-radius:var(--r-full);
  display:inline-flex; align-items:center; justify-content:center;
  font-weight:800; font-size:.85rem; letter-spacing:-.02em;
  flex-shrink:0;
}
.ball.main { background:var(--ball-main-bg); color:#fff; box-shadow:0 2px 8px rgba(99,102,241,.45); }
.ball.db   { background:var(--ball-db-bg);   color:#fff; box-shadow:0 2px 8px rgba(124,58,237,.45); }
.separator { color:var(--text-muted); font-size:1.2rem; margin:0 2px; }
.ky-label  { font-size:.75rem; color:var(--text-2); margin-left:6px; white-space:nowrap; }

/* ── Predictions ──────────────────────────────────────────────── */
.pred-list { display:flex; flex-direction:column; gap:0; }
.pred-set {
  display:flex; align-items:center; gap:12px; flex-wrap:wrap;
  padding:.7rem 0;
  border-bottom:1px solid var(--border);
}
.pred-set:last-child { border-bottom:none; }
.pred-index {
  width:22px; height:22px;
  border-radius:var(--r-full);
  background:var(--indigo-dim);
  color:var(--indigo);
  display:inline-flex; align-items:center; justify-content:center;
  font-size:.7rem; font-weight:800; flex-shrink:0;
}
.pred-label {
  font-size:.72rem; color:var(--text-2);
  min-width:80px; flex-shrink:0;
}
.pred-balls { display:flex; align-items:center; gap:6px; flex-wrap:wrap; flex:1; }
.pred-sum   { font-size:.72rem; color:var(--text-muted); white-space:nowrap; }
.pred-sum strong { color:var(--gap); font-weight:700; }

/* ── Hot / Gap tags ─────────────────────────────────────────────── */
.tag-row { display:flex; flex-wrap:wrap; gap:7px; padding-top:4px; }
.tag {
  display:inline-flex; align-items:center; gap:5px;
  padding:5px 12px;
  border-radius:var(--r-full);
  font-size:.78rem; font-weight:700; cursor:default;
}
.tag.hot { background:var(--hot-dim); color:var(--hot);  border:1px solid rgba(255,107,61,0.4); }
.tag.gap { background:var(--gap-dim); color:var(--gap);  border:1px solid rgba(255,200,87,0.4); }
.tag-count { font-size:.65rem; font-weight:600; opacity:.8; }

/* ── Frequency grid ─────────────────────────────────────────────── */
.freq-grid {
  display:grid;
  grid-template-columns:repeat(7,1fr);
  gap:7px;
}
.freq-cell {
  display:flex; flex-direction:column; align-items:center;
  background:rgba(255,255,255,0.03);
  border-radius:var(--r-md);
  padding:8px 4px 6px;
  border:1px solid var(--border);
  cursor:default; transition:background .15s;
}
.freq-cell:hover { background:rgba(99,102,241,0.1); }
.freq-cell.rank-1 { background:rgba(255,107,61,0.15); border-color:rgba(255,107,61,0.4); }
.freq-cell.rank-2 { background:rgba(255,200,87,0.12); border-color:rgba(255,200,87,0.35); }
.freq-cell.rank-3 { background:rgba(99,102,241,0.15); border-color:rgba(99,102,241,0.4);  }
.freq-num  { font-size:.72rem; font-weight:800; color:#a5b4fc; margin-bottom:5px; }
.freq-bar-wrap { width:16px; height:36px; display:flex; align-items:flex-end; }
.freq-bar  { width:100%; border-radius:3px 3px 0 0; background:var(--indigo); min-height:3px; }
.freq-cell.rank-1 .freq-bar { background:var(--hot); }
.freq-cell.rank-2 .freq-bar { background:var(--gap); }
.freq-count { font-size:.65rem; color:var(--text-2); margin-top:4px; font-weight:600; }

/* ── History table ───────────────────────────────────────────────── */
.table-wrap { overflow-x:auto; }
table  { width:100%; border-collapse:collapse; font-size:.8rem; }
th,td  { padding:.55rem .75rem; text-align:center; white-space:nowrap; }
th     { font-size:.65rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:var(--text-muted); border-bottom:1px solid var(--border-lg); background:var(--surface-2); }
td     { border-bottom:1px solid var(--border); }
tr:last-child td { border-bottom:none; }
tr:hover td { background:rgba(99,102,241,0.05); }

.pill {
  display:inline-flex; align-items:center; justify-content:center;
  width:28px; height:28px; border-radius:var(--r-full);
  font-weight:700; font-size:.78rem;
}
.pill.main-sm { background:rgba(99,102,241,0.2);  color:#a5b4fc; }
.pill.db-sm   { background:rgba(124,58,237,0.25); color:#c4b5fd; }
.buoi-s { color:var(--hot); font-weight:700; font-size:.72rem; }
.buoi-t { color:var(--indigo); font-weight:700; font-size:.72rem; }
.tong-cell { font-weight:700; color:var(--gap); }

/* ── Ad wrap ─────────────────────────────────────────────────────── */
.ad-wrap { min-height:90px; background:var(--surface); border-radius:var(--r-lg); border:1px solid var(--border); overflow:hidden; }

/* ── Footer ─────────────────────────────────────────────────────── */
footer {
  margin-top:1rem;
  text-align:center; font-size:.75rem;
  color:var(--text-muted);
  padding:1.5rem 1rem;
  border-top:1px solid var(--border);
}

/* ── Responsive ──────────────────────────────────────────────────── */
@media (max-width:700px) {
  .stats-grid  { grid-template-columns:1fr 1fr; }
  .two-col     { grid-template-columns:1fr; }
  .freq-grid   { grid-template-columns:repeat(5,1fr); }
  .pred-label  { display:none; }
  h2 { font-size:.82rem; }
}
@media (max-width:420px) {
  .stats-grid { grid-template-columns:1fr 1fr; }
  .freq-grid  { grid-template-columns:repeat(4,1fr); }
  .card-body  { padding:.7rem .85rem; }
  .card-hd    { padding:.7rem .85rem .6rem; }
  th,td       { padding:.45rem .5rem; }
}
''', encoding='utf-8')
print("style.css ✓")

# ─── app.js ────────────────────────────────────────────────────
(BASE / "app.js").write_text('''\
/* app.js — Lotto 5/35 AI Dashboard */

// ── Config ────────────────────────────────────────────────────────────────
const API = "https://lotto535.fly.dev/api";
let currentPredWindow = 30;

// ── Bootstrap ─────────────────────────────────────────────────────────────
async function init() {
  try {
    document.getElementById("error-banner").classList.add("hidden");

    const [stats, preds, latest, freq] = await Promise.all([
      apiFetch("/stats"),
      apiFetch(`/predictions?window=${currentPredWindow}`),
      apiFetch("/latest?n=20"),
      apiFetch("/frequency?window=0"),
    ]);

    renderStats(stats);
    if (latest.length) renderLatest(latest[0]);
    renderPredictions(preds);
    renderHotGap(preds.hot_numbers, preds.gap_numbers);
    renderFreqChart(freq);
    renderHistory(latest);

    document.getElementById("last-update").textContent =
      "Cập nhật: " + new Date().toLocaleString("vi-VN", {
        hour: "2-digit", minute: "2-digit",
        day: "2-digit", month: "2-digit",
      });

  } catch (err) {
    console.error("Init error:", err);
    document.getElementById("error-banner").classList.remove("hidden");
  }
}

// ── API helper ────────────────────────────────────────────────────────────
async function apiFetch(path) {
  const res = await fetch(API + path);
  if (!res.ok) throw new Error(`API ${path} → HTTP ${res.status}`);
  return res.json();
}

// ── Stats ─────────────────────────────────────────────────────────────────
function renderStats(stats) {
  const s = stats.sum_stats || {};
  document.getElementById("stats-row").innerHTML = `
    <div class="stat-card">
      <span class="icon">📦</span>
      <div class="val">${stats.total ?? "—"}</div>
      <div class="lbl">Tổng kỳ</div>
    </div>
    <div class="stat-card">
      <span class="icon">➕</span>
      <div class="val">${s.avg != null ? Math.round(s.avg) : "—"}</div>
      <div class="lbl">Tổng TB</div>
    </div>
    <div class="stat-card">
      <span class="icon">📏</span>
      <div class="val">${s.mn ?? "—"}–${s.mx ?? "—"}</div>
      <div class="lbl">Min–Max</div>
    </div>
    <div class="stat-card">
      <span class="icon">🏆</span>
      <div class="val">#${stats.latest?.ky ?? "—"}</div>
      <div class="lbl">Kỳ mới nhất</div>
    </div>
  `;
}

// ── Ball helper ───────────────────────────────────────────────────────────
function ballHTML(num, cls = "main") {
  return `<span class="ball ${cls}">${String(num).padStart(2, "0")}</span>`;
}

// ── Latest result ─────────────────────────────────────────────────────────
function renderLatest(r) {
  if (!r) return;
  const time = r.buoi === "S" ? "13H" : "21H";
  document.getElementById("latest-result").innerHTML =
    [r.s1, r.s2, r.s3, r.s4, r.s5].map(n => ballHTML(n)).join("") +
    `<span class="separator">|</span>` +
    ballHTML(r.db, "db") +
    `<span class="ky-label">Kỳ #${r.ky} — ${escapeHTML(r.ngay)} (${time})</span>`;
}

// ── Predictions ───────────────────────────────────────────────────────────
function renderPredictions(preds) {
  const items = (preds.predictions || []).map((p, i) => {
    const total = (p.nums || []).reduce((a, b) => a + b, 0);
    const label = escapeHTML((p.ten || "").replace(/^Bộ \\d+ — /, ""));
    return `
      <div class="pred-set">
        <span class="pred-index">${i + 1}</span>
        <span class="pred-label">${label}</span>
        <div class="pred-balls">
          ${(p.nums || []).map(n => ballHTML(n)).join("")}
          <span class="separator">|</span>
          ${ballHTML(p.db, "db")}
        </div>
        <span class="pred-sum">Tổng: <strong>${total}</strong></span>
      </div>`;
  }).join("");
  document.getElementById("predictions").innerHTML =
    items ? `<div class="pred-list">${items}</div>` : `<p style="color:var(--text-muted);padding:.5rem 0">Chưa có dữ liệu dự đoán.</p>`;
}

async function setPredWindow(w, btn) {
  currentPredWindow = w;
  btn.closest(".seg-ctrl").querySelectorAll(".seg-btn")
    .forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  try {
    const preds = await apiFetch(`/predictions?window=${w}`);
    renderPredictions(preds);
    renderHotGap(preds.hot_numbers, preds.gap_numbers);
  } catch (e) { console.error(e); }
}

// ── Hot & Gap ─────────────────────────────────────────────────────────────
function renderHotGap(hot = [], gap = []) {
  document.getElementById("hot-nums").innerHTML =
    hot.map(r =>
      `<span class="tag hot">🔥 <strong>${r.so}</strong> <span class="tag-count">${r.freq_30}×</span></span>`
    ).join("") || `<span style="color:var(--text-muted);font-size:.8rem">Không có dữ liệu</span>`;

  document.getElementById("gap-nums").innerHTML =
    gap.map(r =>
      `<span class="tag gap">⏳ <strong>${r.so}</strong> <span class="tag-count">${r.gap} kỳ</span></span>`
    ).join("") || `<span style="color:var(--text-muted);font-size:.8rem">Không có dữ liệu</span>`;
}

// ── Frequency chart ───────────────────────────────────────────────────────
function renderFreqChart(freq) {
  const sorted = [...freq].sort((a, b) => b.count - a.count);
  const maxVal = sorted[0]?.count || 1;
  const rankMap = {};
  sorted.slice(0, 3).forEach((f, i) => { rankMap[f.so] = i + 1; });

  document.getElementById("freq-chart").innerHTML =
    freq.map(f => {
      const rank = rankMap[f.so] ? `rank-${rankMap[f.so]}` : "";
      const barH = Math.max(Math.round((f.count / maxVal) * 36), 3);
      return `
        <div class="freq-cell ${rank}" title="Số ${f.so}: ${f.count} lần">
          <span class="freq-num">${String(f.so).padStart(2, "0")}</span>
          <div class="freq-bar-wrap">
            <div class="freq-bar" style="height:${barH}px"></div>
          </div>
          <span class="freq-count">${f.count}</span>
        </div>`;
    }).join("");
}

async function loadFreq(window, btn) {
  btn.closest(".seg-ctrl").querySelectorAll(".seg-btn")
    .forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  try {
    const freq = await apiFetch(`/frequency?window=${window}`);
    renderFreqChart(freq);
  } catch (e) { console.error(e); }
}

// ── History table ─────────────────────────────────────────────────────────
function renderHistory(rows) {
  if (!rows.length) {
    document.getElementById("history-body").innerHTML =
      `<tr><td colspan="10" style="color:var(--text-muted);padding:1rem">Chưa có dữ liệu</td></tr>`;
    return;
  }
  document.getElementById("history-body").innerHTML =
    rows.map(r => {
      const time = r.buoi === "S" ? "13H" : "21H";
      const cls  = r.buoi === "S" ? "buoi-s" : "buoi-t";
      return `
        <tr>
          <td><strong>#${r.ky}</strong></td>
          <td>${escapeHTML(r.ngay)}</td>
          <td class="${cls}">${time}</td>
          <td><span class="pill main-sm">${r.s1}</span></td>
          <td><span class="pill main-sm">${r.s2}</span></td>
          <td><span class="pill main-sm">${r.s3}</span></td>
          <td><span class="pill main-sm">${r.s4}</span></td>
          <td><span class="pill main-sm">${r.s5}</span></td>
          <td><span class="pill db-sm">${r.db}</span></td>
          <td class="tong-cell">${r.tong}</td>
        </tr>`;
    }).join("");
}

// ── XSS guard ─────────────────────────────────────────────────────────────
function escapeHTML(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/\'/g, "&#039;");
}

// ── Start ─────────────────────────────────────────────────────────────────
init();
''', encoding='utf-8')
print("app.js ✓")

# ─── robots.txt ────────────────────────────────────────────────
(BASE / "robots.txt").write_text(
    "User-agent: *\nAllow: /\n\nSitemap: https://lotto535.fly.dev/sitemap.xml\n",
    encoding='utf-8'
)
print("robots.txt ✓")

# ─── sitemap.xml ───────────────────────────────────────────────
(BASE / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    '  <url>\n'
    '    <loc>https://lotto535.fly.dev/\</loc\>\n'
    '    <changefreq>always</changefreq>\n'
    '    <priority>1.0</priority>\n'
    '    <lastmod>2026-04-16</lastmod>\n'
    '  </url>\n'
    '</urlset>\n',
    encoding='utf-8'
)
print("sitemap.xml ✓")

# ─── ads.txt ───────────────────────────────────────────────────
(BASE / "ads.txt").write_text(
    "# Google AdSense\ngoogle.com, pub-2330743593269954, DIRECT, f08c47fec0942fa0\n",
    encoding='utf-8'
)
print("ads.txt ✓")

print("\nAll files written OK")
