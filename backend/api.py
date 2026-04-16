"""
api.py — FastAPI backend for Lotto 5/35 Prediction Dashboard

Endpoints:
    GET /api/latest?n=20         — n kỳ gần nhất
    GET /api/predictions         — 5 bộ số dự đoán
    GET /api/scores              — bảng scoring 1-35
    GET /api/stats               — thống kê tổng hợp
    GET /api/frequency?window=0  — tần suất từng số
    GET /api/backtest            — kết quả backtest
    POST /api/crawl              — trigger crawl ngay (admin protected)
"""
import os
import time
import sqlite3
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

try:
    from db import DB_PATH, init_db, get_conn
    from engine import (
        load_results,
        score_numbers,
        score_db_numbers,
        generate_sets,
        recalculate_scores,
        backtest,
    )
except ImportError:
    from backend.db import DB_PATH, init_db, get_conn
    from backend.engine import (
        load_results,
        score_numbers,
        score_db_numbers,
        generate_sets,
        recalculate_scores,
        backtest,
    )

# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Init DB on startup."""
    init_db()
    yield


app = FastAPI(
    title="Lotto 5/35 Prediction API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow dashboard served from any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Serve frontend if it exists (production mode)
# ---------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def db_query(sql: str, params: tuple = ()) -> list[dict]:
    con = get_conn()
    cur = con.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


# Simple API key guard for write endpoints (set ADMIN_KEY env var)
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")

def require_admin(x_admin_key: str = Header(default="")):
    if ADMIN_KEY and x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/latest")
def get_latest(n: int = Query(20, ge=1, le=500)):
    """Lấy n kỳ gần nhất."""
    return db_query(
        "SELECT id,ky,ngay,buoi,s1,s2,s3,s4,s5,db,tong FROM results ORDER BY ky DESC LIMIT ?",
        (n,),
    )


@app.get("/api/predictions")
def get_predictions(window: int = Query(30, ge=10, le=200)):
    """Trả về 5 bộ số dự đoán cho kỳ tiếp theo."""
    draws   = load_results()
    num_sc  = score_numbers(draws, window=window)
    db_sc   = score_db_numbers(draws, window=window)
    sets    = generate_sets(num_sc, db_sc)

    hot  = sorted(num_sc, key=lambda x: x["freq_30"],    reverse=True)[:7]
    gap  = sorted(num_sc, key=lambda x: x["gap"],        reverse=True)[:7]

    return {
        "total_draws":  len(draws),
        "window":       window,
        "predictions":  sets,
        "top_numbers":  [r["so"]  for r in num_sc[:15]],
        "top_db":       [r["db"]  for r in db_sc[:5]],
        "hot_numbers":  hot,
        "gap_numbers":  gap,
    }


@app.get("/api/scores")
def get_scores():
    """Bảng scoring đầy đủ 1–35 từ cache."""
    rows = db_query("SELECT * FROM scoring_cache ORDER BY score DESC")
    if not rows:
        # cache chưa có — tính ngay
        num_sc, _ = recalculate_scores()
        return num_sc
    return rows


@app.get("/api/scores/db")
def get_scores_db():
    """Bảng scoring DB (1–12) từ cache."""
    rows = db_query("SELECT * FROM scoring_db ORDER BY score DESC")
    if not rows:
        _, db_sc = recalculate_scores()
        return db_sc
    return rows


@app.get("/api/stats")
def get_stats():
    """Thống kê tổng hợp."""
    total  = db_query("SELECT COUNT(*) as cnt FROM results")[0]["cnt"]
    latest = db_query(
        "SELECT * FROM results ORDER BY ky DESC LIMIT 1"
    )
    agg = db_query(
        "SELECT ROUND(AVG(tong),1) as avg, MIN(tong) as mn, MAX(tong) as mx FROM results"
    )[0]
    return {
        "total":     total,
        "latest":    latest[0] if latest else None,
        "sum_stats": agg,
    }


@app.get("/api/frequency")
def get_frequency(window: int = Query(0, ge=0)):
    """
    Tần suất từng số 1–35.
    window=0 → toàn bộ lịch sử
    window=N → N kỳ gần nhất
    """
    draws = load_results()
    if window > 0:
        draws = draws[-window:]

    freq: dict[int, int] = {}
    for r in draws:
        for n in r[:5]:
            freq[n] = freq.get(n, 0) + 1

    return [{"so": k, "count": freq.get(k, 0)} for k in range(1, 36)]


@app.get("/api/backtest")
def get_backtest(lookback: int = Query(50, ge=20, le=200),
                 predict_n: int = Query(100, ge=10, le=500)):
    """Chạy backtest và trả về accuracy metrics."""
    draws = load_results()
    return backtest(draws, lookback=lookback, predict_n=predict_n)


@app.post("/api/crawl")
def trigger_crawl(_: None = Depends(require_admin)):
    """Trigger crawl thủ công (yêu cầu X-Admin-Key header)."""
    from crawler import run_crawl
    is_new, result = run_crawl()
    if is_new:
        recalculate_scores()
    return {"is_new": is_new, "result": result}


@app.post("/api/recalculate")
def trigger_recalculate(_: None = Depends(require_admin)):
    """Tính lại toàn bộ score (yêu cầu X-Admin-Key header)."""
    num_sc, db_sc = recalculate_scores()
    return {
        "message": "Recalculated",
        "num_scores": num_sc[:5],
        "db_scores":  db_sc[:3],
    }


@app.get("/health")
def health():
    return {"status": "ok", "db": DB_PATH}
