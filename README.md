# LottoAI — AI Dự Đoán Xổ Số Vietlott

> **Live:** [https://lotto535.fly.dev](https://lotto535.fly.dev)

> ⚠️ Xổ số là trò chơi may rủi. Mỗi kỳ quay hoàn toàn độc lập. Tool này chỉ phân tích thống kê để vui chơi, không phải công cụ đầu tư.

Hỗ trợ 3 sản phẩm Vietlott:
- **Lotto 5/35** — Chọn 5 số (1–35) + DB (1–12), 2 lần/ngày (13H & 21H)
- **Mega 6/45** — Chọn 6 số (1–45), 3 lần/tuần (T4 · T6 · CN)
- **Power 6/55** — Chọn 6 số (1–55) + Power (1–55), 3 lần/tuần (T3 · T5 · T7)

---

## ✨ Tính năng

| Feature | Chi tiết |
|---|---|
| 🎮 Multi-game | Hỗ trợ Lotto 5/35, Mega 6/45, Power 6/55 — chuyển tab tức thì |
| 🕷️ Auto crawl | Crawl vietlott.vn tự động theo lịch mỗi game |
| 📊 Scoring engine | Composite score: freq_total (40%) + freq_30 (30%) + gap (30%) |
| 🔮 5 bộ dự đoán | Per-set **Confidence %** + **HOT/GAP/BALANCED/STABLE** tags |
| 🧠 AI Explain | Giải thích lý do chọn từng bộ số (hot/overdue counts, distribution) |
| ↺ Generate New | Animation "Analyzing → Generating" với fresh API call |
| ☆ Save Picks | Lưu bộ số kèm game label vào localStorage |
| 📈 Frequency chart | Animated bars, HOT/LOW badges, insight cards theo window |
| 🔥 Hot & Gap tracker | Trend indicator: avg hot rate + avg gap rounds |
| 🧪 Backtest | 4 metrics: accuracy %, avg hits, hit3 %, total tested |
| 🌐 REST API | FastAPI · Swagger docs `/docs` · tất cả endpoint nhận `?game=` |
| 🎨 Dark/Light UI | Dark-first, Space Mono cho số, Be Vietnam Pro cho text |
| 📱 PWA | manifest.json, theme-color, apple-touch-icon |
| 🔍 SEO | Meta tags, OG, JSON-LD, sitemap.xml, robots.txt, AdSense |
| 🚀 Fly.io | Docker + persistent SQLite volume |

---

## 📁 Cấu trúc

```
loto5-35/
├── backend/
│   ├── db.py               # SQLite schema: results/scoring 535 + 645 + 655
│   ├── crawler.py          # Crawl vietlott.vn cho cả 3 game
│   ├── engine.py           # Game-agnostic scoring + prediction (GAME_CONFIGS)
│   ├── api.py              # FastAPI — mọi endpoint nhận ?game=535|645|655
│   ├── scheduler.py        # APScheduler: crawl + recalc theo lịch từng game
│   └── scheduler_once.py   # Chạy 1 lần (cron / GH Actions)
├── frontend/
│   ├── index.html          # SPA — game selector tabs + dynamic hero/history
│   ├── app.js              # Multi-game JS (GAMES config, switchGame, ...)
│   └── style.css           # Styles: .ball--power, .game-selector-bar
├── data/
│   └── lotto535.db         # SQLite (tables: results, results_645, results_655, ...)
├── init_db.py
├── import_excel.py
├── seed_sample.py
├── requirements.txt
├── Dockerfile
├── fly.toml
└── README.md
```

---

## 🚀 Chạy local

### Yêu cầu
- Python 3.11+

### 1. Cài dependencies

```bash
pip install -r requirements.txt
```

### 2. Khởi tạo DB (tạo tất cả bảng cho 3 game)

```bash
python init_db.py
```

### 3. Import / Crawl dữ liệu

**Seed mẫu để test nhanh (Lotto 5/35):**
```bash
python seed_sample.py
```

**Crawl từ vietlott.vn:**
```bash
python -c "from backend.crawler import run_crawl, run_crawl_645, run_crawl_655; run_crawl(); run_crawl_645(); run_crawl_655()"
```

**Crawl bulk (nhiều kỳ lịch sử):**
```bash
python -c "from backend.crawler import run_crawl_bulk, run_crawl_bulk_645, run_crawl_bulk_655; run_crawl_bulk(50); run_crawl_bulk_645(30); run_crawl_bulk_655(30)"
```

### 4. Tính score lần đầu

```bash
python -c "
import sys; sys.path.insert(0,'backend')
from engine import recalculate_scores
recalculate_scores('535')
recalculate_scores('645')
recalculate_scores('655')
"
```

### 5. Chạy API

```bash
uvicorn backend.api:app --reload --port 8000
```

Swagger docs: http://localhost:8000/docs

### 6. Mở frontend

```bash
cd frontend && python -m http.server 3000
```

Mở: http://localhost:3000

---

## 🌐 Deploy lên Fly.io

```bash
# Deploy lại sau khi thay đổi code
fly deploy

# Xem logs
fly logs

# Crawl bulk qua API sau deploy
curl -X POST "https://lotto535.fly.dev/api/crawl-bulk?game=645&n=30" -H "X-Admin-Key: YOUR_KEY"
curl -X POST "https://lotto535.fly.dev/api/crawl-bulk?game=655&n=30" -H "X-Admin-Key: YOUR_KEY"
curl -X POST "https://lotto535.fly.dev/api/recalculate?game=645" -H "X-Admin-Key: YOUR_KEY"
curl -X POST "https://lotto535.fly.dev/api/recalculate?game=655" -H "X-Admin-Key: YOUR_KEY"
```

---

## ⚙️ Biến môi trường

| Biến | Mặc định | Mô tả |
|---|---|---|
| `DB_PATH` | `data/lotto535.db` | Đường dẫn SQLite |
| `ADMIN_KEY` | _(trống)_ | API key cho write endpoints |

---

## 📡 API Endpoints

Tất cả GET endpoint nhận `?game=535` (default) | `645` | `655`.

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/latest?game=535&n=20` | n kỳ gần nhất |
| GET | `/api/predictions?game=535&window=30` | 5 bộ số dự đoán |
| GET | `/api/scores?game=535` | Bảng scoring số chính |
| GET | `/api/scores/db?game=535` | Bảng scoring DB/Power |
| GET | `/api/stats?game=535` | Thống kê tổng hợp |
| GET | `/api/frequency?game=535&window=30` | Tần suất từng số |
| GET | `/api/backtest?game=535` | Backtest accuracy |
| POST | `/api/crawl?game=535` | Trigger crawl (X-Admin-Key) |
| POST | `/api/crawl-bulk?game=535&n=10` | Crawl nhiều kỳ (X-Admin-Key) |
| POST | `/api/recalculate?game=535` | Tính lại score (X-Admin-Key) |

---

## 🗄️ Database Schema

| Bảng | Game | Mô tả |
|---|---|---|
| `results` | 5/35 | ky, ngay, buoi, s1–s5, db, tong |
| `scoring_cache` | 5/35 | Scoring số chính 1–35 |
| `scoring_db` | 5/35 | Scoring DB 1–12 |
| `results_645` | 6/45 | ky, ngay, s1–s6, tong |
| `scoring_645` | 6/45 | Scoring số 1–45 |
| `results_655` | 6/55 | ky, ngay, s1–s6, power, tong |
| `scoring_655` | 6/55 | Scoring số chính 1–55 |
| `scoring_655_power` | 6/55 | Scoring Power 1–55 |
