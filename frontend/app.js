/* app.js — Lotto 5/35 Prediction Dashboard */

// ── Config ────────────────────────────────────────────────────────────────
const API = (() => {
  // In production (served from FastAPI), use relative path
  if (window.location.port === "3000" || window.location.hostname === "localhost") {
    return "http://localhost:8000/api";
  }
  return "/api";
})();

let currentPredWindow = 30;

// ── Bootstrap ─────────────────────────────────────────────────────────────
async function init() {
  try {
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
      "Cập nhật: " + new Date().toLocaleString("vi-VN");

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
      <div class="val">${stats.total ?? "—"}</div>
      <div class="lbl">Tổng kỳ</div>
    </div>
    <div class="stat-card">
      <div class="val">${s.avg != null ? Math.round(s.avg) : "—"}</div>
      <div class="lbl">Tổng TB (5 số)</div>
    </div>
    <div class="stat-card">
      <div class="val">${s.mn ?? "—"} – ${s.mx ?? "—"}</div>
      <div class="lbl">Tổng Min – Max</div>
    </div>
    <div class="stat-card">
      <div class="val">${stats.latest?.ky ?? "—"}</div>
      <div class="lbl">Kỳ mới nhất</div>
    </div>
  `;
}

// ── Ball helpers ──────────────────────────────────────────────────────────
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
    `<span class="ky-label">Kỳ #${r.ky} — ${r.ngay} (${time})</span>`;
}

// ── Predictions ───────────────────────────────────────────────────────────
function renderPredictions(preds) {
  document.getElementById("predictions").innerHTML =
    (preds.predictions || []).map((p, i) => `
      <div class="pred-set">
        <span class="pred-label">${escapeHTML(p.ten)}</span>
        <div class="ball-row">
          ${(p.nums || []).map(n => ballHTML(n)).join("")}
          <span class="separator">|</span>
          ${ballHTML(p.db, "db")}
        </div>
      </div>
    `).join("");
}

async function setPredWindow(w, btn) {
  currentPredWindow = w === 0 ? 9999 : w;
  document.querySelectorAll(".toggle-row .btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  try {
    const preds = await apiFetch(`/predictions?window=${currentPredWindow}`);
    renderPredictions(preds);
    renderHotGap(preds.hot_numbers, preds.gap_numbers);
  } catch (e) {
    console.error(e);
  }
}

// ── Hot & Gap ─────────────────────────────────────────────────────────────
function renderHotGap(hot = [], gap = []) {
  document.getElementById("hot-nums").innerHTML =
    hot.map(r => `<span class="tag hot">🔥 ${r.so} <em>(${r.freq_30}x)</em></span>`).join("");
  document.getElementById("gap-nums").innerHTML =
    gap.map(r => `<span class="tag gap">⏳ ${r.so} <em>(${r.gap} kỳ)</em></span>`).join("");
}

// ── Frequency chart ───────────────────────────────────────────────────────
function renderFreqChart(freq) {
  const counts = freq.map(f => f.count);
  const maxVal = Math.max(...counts, 1);

  document.getElementById("freq-chart").innerHTML =
    freq.map(f => {
      const width = Math.round((f.count / maxVal) * 260);
      const highlight = f.count === maxVal ? "highlight" : "";
      return `
        <div class="freq-row">
          <span class="freq-num">${String(f.so).padStart(2, "0")}</span>
          <div class="freq-bar ${highlight}" style="width:${width}px"></div>
          <span class="freq-cnt">${f.count}</span>
        </div>
      `;
    }).join("");
}

async function loadFreq(window, btn) {
  const btns = btn.closest(".toggle-row").querySelectorAll(".btn");
  btns.forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  try {
    const freq = await apiFetch(`/frequency?window=${window}`);
    renderFreqChart(freq);
  } catch (e) {
    console.error(e);
  }
}

// ── History table ─────────────────────────────────────────────────────────
function renderHistory(rows) {
  document.getElementById("history-body").innerHTML =
    rows.map(r => {
      const time = r.buoi === "S" ? "13H" : "21H";
      const cls  = r.buoi === "S" ? "buoi-s" : "buoi-t";
      return `
        <tr>
          <td>#${r.ky}</td>
          <td>${escapeHTML(r.ngay)}</td>
          <td class="${cls}">${time}</td>
          <td>${r.s1}</td><td>${r.s2}</td><td>${r.s3}</td><td>${r.s4}</td><td>${r.s5}</td>
          <td><strong>${r.db}</strong></td>
          <td>${r.tong}</td>
        </tr>
      `;
    }).join("");
}

// ── Security: XSS prevention ──────────────────────────────────────────────
function escapeHTML(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ── Start ─────────────────────────────────────────────────────────────────
init();
