# LottoAI — AI Lotto 5/35 Prediction Engine

> **Live:** [https://lotto535.fly.dev](https://lotto535.fly.dev)

> ⚠️ Xổ số là trò chơi may rủi. Mỗi kỳ quay hoàn toàn độc lập. Tool này chỉ phân tích thống kê để vui chơi, không phải công cụ đầu tư.

---

## ✨ Tính năng

| Feature | Chi tiết |
|---|---|
| 🕷️ Auto crawl | Crawl vietlott.vn lúc 13:30 & 22:00 hằng ngày |
| 📊 Scoring engine | Composite score: freq_total (40%) + freq_30 (30%) + gap (30%) |
| 🔮 5 bộ dự đoán | Per-set **Confidence %** + **HOT/GAP/BALANCED/STABLE** tags |
| 🧠 AI Explain | Giải thích lý do chọn từng bộ số (hot/overdue counts, distribution) |
| ↺ Regenerate | Animation "Analyzing → Generating" với API call |
| ☆ Save Picks | Lưu bộ số vào localStorage, xem lại bất cứ lúc nào |
| 📈 Frequency chart | Animated bars, HOT/LOW badges, 3 insight cards trên mỗi window |
| 🔥 Hot & Gap tracker | Trend indicator: avg hot rate + avg gap rounds |
| 🧪 Backtest | 4 metrics: accuracy %, avg hits, hit3 %, total tested |
| 🌐 REST API | FastAPI · Swagger docs `/docs` |
| 🎨 Dark/Light UI | Dark-first design, Space Mono cho số, Be Vietnam Pro cho text |
| 📱 PWA | manifest.json, theme-color, apple-touch-icon |
| 🔍 SEO | Meta tags, OG, JSON-LD, sitemap.xml, robots.txt, AdSense |
| 🚀 Fly.io deploy | Docker + persistent SQLite volume |

---

## 📁 Cấu trúc

```
loto5-35/
├── backend/
│   ├── __init__.py
│   ├── db.py               # SQLite helper + schema init
│   ├── crawler.py          # Crawl vietlott.vn + backup
│   ├── engine.py           # Scoring + prediction logic
│   ├── api.py              # FastAPI endpoints
│   ├── scheduler.py        # Chạy liên tục (13:30 & 22:00)
│   └── scheduler_once.py   # Chạy 1 lần (dùng với cron / GH Actions)
├── frontend/
│   ├── index.html          # Dashboard UI
│   ├── app.js              # Dashboard logic
│   └── style.css           # Styles
├── data/
│   └── lotto535.db         # SQLite database (auto-created)
├── .github/
│   └── workflows/
│       └── crawl.yml       # GitHub Actions auto-crawl
├── init_db.py              # Khởi tạo DB
├── import_excel.py         # Import dữ liệu từ Excel
├── seed_sample.py          # Seed 20 kỳ mẫu để test
├── debug_crawler.py        # Debug HTML structure vietlott.vn
├── requirements.txt
├── Dockerfile
├── fly.toml
└── README.md
```

---

## 🚀 Chạy local

### Yêu cầu
- Python 3.11+
- pip

### Bước 1: Cài dependencies

```bash
pip install -r requirements.txt
```

### Bước 2: Khởi tạo DB

```bash
python init_db.py
```

### Bước 3: Import dữ liệu

**Option A — Import từ Excel (nếu có file sẵn):**
```bash
python import_excel.py path/to/full_tool_535.xlsx
```

**Option B — Seed dữ liệu mẫu (để test nhanh):**
```bash
python seed_sample.py
```

**Option C — Crawl từ vietlott.vn:**
```bash
cd backend
python crawler.py
```

### Bước 4: Tính score lần đầu

```bash
python -c "import sys; sys.path.insert(0,'backend'); from engine import recalculate_scores; recalculate_scores()"
```

### Bước 5: Chạy API

```bash
uvicorn backend.api:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Bước 6: Mở frontend

```bash
cd frontend && python -m http.server 3000
```

Mở: http://localhost:3000

### Bước 7: Bật scheduler (optional)

```bash
python backend/scheduler.py
```

---

## 🌐 Deploy lên Fly.io

### Yêu cầu
- [flyctl](https://fly.io/docs/hands-on/install-flyctl/) đã cài
- Đã đăng nhập: `fly auth login`

### Deploy lần đầu

```bash
# 1. Tạo app (chỉ chạy lần đầu)
fly launch --name lotto535 --region sin --no-deploy

# 2. Tạo volume lưu SQLite
fly volumes create lotto535_data --size 1 --region sin

# 3. Set admin key (bảo vệ /api/crawl và /api/recalculate)
fly secrets set ADMIN_KEY="your-secret-key-here"

# 4. Deploy
fly deploy

# 5. Mở app
fly open
```

### Deploy lại (sau khi thay đổi code)

```bash
fly deploy
```

### Import data lên production

```bash
# Chạy seed trực tiếp trên máy Fly
fly ssh console -C "python /app/seed_sample.py"

# Hoặc import Excel (upload file trước)
fly sftp get /tmp/file.xlsx
fly ssh console -C "python /app/import_excel.py /tmp/file.xlsx"
```

### Xem logs

```bash
fly logs
```

---

## ⚙️ Biến môi trường

| Biến | Mặc định | Mô tả |
|---|---|---|
| `DB_PATH` | `data/lotto535.db` | Đường dẫn SQLite |
| `ADMIN_KEY` | _(trống - không bảo vệ)_ | API key cho endpoints write |

---

## 📡 API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/latest?n=20` | n kỳ gần nhất |
| GET | `/api/predictions?window=30` | 5 bộ số dự đoán |
| GET | `/api/scores` | Bảng scoring 1–35 |
| GET | `/api/scores/db` | Bảng scoring DB 1–12 |
| GET | `/api/stats` | Thống kê tổng hợp |
| GET | `/api/frequency?window=0` | Tần suất từng số |
| GET | `/api/backtest` | Backtest accuracy |
| POST | `/api/crawl` | Trigger crawl (cần X-Admin-Key) |
| POST | `/api/recalculate` | Tính lại score (cần X-Admin-Key) |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| External fonts | **None** — system font stack (`system-ui, -apple-system, "Segoe UI"`) |
| JS framework | **None** — vanilla JS (~7 KB) |
| CSS framework | **None** — custom CSS design tokens (~5 KB) |
| API calls | Parallel via `Promise.all` — 4 endpoints in one round-trip |
| AdSense | `async` attribute — non-blocking page render |
| Static files | Served via FastAPI `FileResponse` — no extra server layer |
| Time to first byte | ~50 ms (Fly.io SIN region) |
| DB | SQLite on persistent Fly volume — zero external DB latency |

### Optimizations applied
- **Sticky navbar** with `backdrop-filter: blur` — CSS only, no JS
- `<link rel="preload" href="style.css" as="style">` — early asset discovery
- `<script src="app.js" defer>` — parse HTML before executing JS
- All render functions update DOM in one `innerHTML` assignment per element
- Frequency bars: CSS `width` via inline style, no Canvas/SVG
- History table: 4-col (no redundant columns)
- No animation libraries — only CSS `@keyframes shimmer` for skeleton loading

---

## 🧮 Scoring Formula

$$\text{score} = \frac{\text{freq\_total}}{\text{max\_ft}} \times 40 + \frac{\text{freq\_30}}{\text{max\_fw}} \times 30 + \frac{\text{gap}}{\text{max\_gap}} \times 30$$

- **freq_total** (40%): Tần suất toàn bộ lịch sử — số "mạnh" dài hạn
- **freq_30** (30%): Tần suất 30 kỳ gần nhất — số đang "hot"
- **gap** (30%): Số kỳ chưa xuất hiện — heuristic mean-reversion

---

## 🔧 Troubleshooting

**Crawler không lấy được dữ liệu?**
```bash
python debug_crawler.py
# Kiểm tra debug.html để tìm đúng CSS selector
```

**DB lỗi?**
```bash
python init_db.py  # Re-init DB
```

**Score chưa được tính?**
```bash
python -c "import sys; sys.path.insert(0,'backend'); from engine import recalculate_scores; recalculate_scores()"
```
