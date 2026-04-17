"""
api.py — FastAPI backend for LottoAI (Lotto 5/35, Mega 6/45, Power 6/55)

All data endpoints accept ?game=535|645|655  (default 535)
"""
import os
import time
import sqlite3
from contextlib import asynccontextmanager
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

try:
    from db import DB_PATH, init_db, get_conn
    from engine import (
        GAME_CONFIGS,
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
        GAME_CONFIGS,
        load_results,
        score_numbers,
        score_db_numbers,
        generate_sets,
        recalculate_scores,
        backtest,
    )

VALID_GAMES = {"535", "645", "655"}

# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Init DB on startup."""
    init_db()
    yield


app = FastAPI(
    title="LottoAI Prediction API",
    description="AI prediction engine for Lotto 5/35, Mega 6/45, Power 6/55",
    version="2.0.0",
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
# Frontend helpers — explicit routes for SEO/PWA files before SPA catch-all
# ---------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

def _fe(name: str):
    return FileResponse(os.path.join(FRONTEND_DIR, name))

@app.get("/robots.txt", include_in_schema=False)
async def robots(): return _fe("robots.txt")

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap(): return _fe("sitemap.xml")

@app.get("/ads.txt", include_in_schema=False)
async def ads_txt(): return _fe("ads.txt")

@app.get("/google21779641c6e2dbb4.html", include_in_schema=False)
async def google_verify(): return _fe("google21779641c6e2dbb4.html")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def db_query(sql: str, params: tuple = ()) -> list[dict]:
    con = get_conn()
    cur = con.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def _validate_game(game: str) -> str:
    if game not in VALID_GAMES:
        raise HTTPException(status_code=400, detail=f"game must be one of: {sorted(VALID_GAMES)}")
    return game


# Simple API key guard for write endpoints (set ADMIN_KEY env var)
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")

def require_admin(x_admin_key: str = Header(default="")):
    if ADMIN_KEY and x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/latest")
def get_latest(game: str = Query("535"), n: int = Query(20, ge=1, le=500)):
    """Lấy n kỳ gần nhất."""
    _validate_game(game)
    cfg = GAME_CONFIGS[game]
    tbl = cfg["table"]
    cols = cfg["select_cols"]
    if game == "535":
        return db_query(
            f"SELECT id,ky,ngay,buoi,{cols},tong FROM {tbl} ORDER BY ky DESC LIMIT ?",
            (n,),
        )
    else:
        return db_query(
            f"SELECT id,ky,ngay,{cols},tong FROM {tbl} ORDER BY ky DESC LIMIT ?",
            (n,),
        )


@app.get("/api/predictions")
def get_predictions(game: str = Query("535"),
                    window: int = Query(30, ge=0, le=500)):
    """Trả về 5 bộ số dự đoán cho kỳ tiếp theo."""
    _validate_game(game)
    draws   = load_results(game=game)
    num_sc  = score_numbers(draws, window=window, game=game)
    db_sc   = score_db_numbers(draws, window=window, game=game)
    sets    = generate_sets(num_sc, db_sc, game=game)

    hot = sorted(num_sc, key=lambda x: x["freq_30"], reverse=True)[:7]
    gap = sorted(num_sc, key=lambda x: x["gap"],     reverse=True)[:7]

    return {
        "game":         game,
        "total_draws":  len(draws),
        "window":       window,
        "predictions":  sets,
        "top_numbers":  [r["so"] for r in num_sc[:15]],
        "top_db":       [r["db"] for r in db_sc[:5]] if db_sc else [],
        "hot_numbers":  hot,
        "gap_numbers":  gap,
    }


@app.get("/api/scores")
def get_scores(game: str = Query("535")):
    """Bảng scoring đầy đủ (số chính) từ cache."""
    _validate_game(game)
    cfg = GAME_CONFIGS[game]
    rows = db_query(f"SELECT * FROM {cfg['score_table']} ORDER BY score DESC")
    if not rows:
        num_sc, _ = recalculate_scores(game=game)
        return num_sc
    return rows


@app.get("/api/scores/db")
def get_scores_db(game: str = Query("535")):
    """Bảng scoring DB / Power từ cache."""
    _validate_game(game)
    cfg = GAME_CONFIGS[game]
    if not cfg["score_db_table"]:
        return []
    rows = db_query(f"SELECT * FROM {cfg['score_db_table']} ORDER BY score DESC")
    if not rows:
        _, db_sc = recalculate_scores(game=game)
        return db_sc
    return rows


@app.get("/api/stats")
def get_stats(game: str = Query("535")):
    """Thống kê tổng hợp."""
    _validate_game(game)
    cfg = GAME_CONFIGS[game]
    tbl = cfg["table"]
    total  = db_query(f"SELECT COUNT(*) as cnt FROM {tbl}")[0]["cnt"]
    latest = db_query(f"SELECT * FROM {tbl} ORDER BY ky DESC LIMIT 1")
    # Sum stats — only for main numbers
    main_n = cfg["main_n"]
    sum_expr = "+".join(f"s{i+1}" for i in range(main_n))
    agg = db_query(
        f"SELECT ROUND(AVG(tong),1) as avg, MIN(tong) as mn, MAX(tong) as mx FROM {tbl}"
    )[0]
    return {
        "game":    game,
        "total":   total,
        "latest":  latest[0] if latest else None,
        "sum_stats": agg,
    }


@app.get("/api/frequency")
def get_frequency(game: str = Query("535"), window: int = Query(0, ge=0)):
    """
    Tần suất từng số chính.
    window=0 → toàn bộ lịch sử; window=N → N kỳ gần nhất.
    """
    _validate_game(game)
    cfg    = GAME_CONFIGS[game]
    draws  = load_results(game=game)
    if window > 0:
        draws = draws[-window:]

    main_n   = cfg["main_n"]
    main_max = cfg["main_max"]
    freq: dict[int, int] = {}
    for r in draws:
        for n in r[:main_n]:
            freq[n] = freq.get(n, 0) + 1

    return [{"so": k, "count": freq.get(k, 0)} for k in range(1, main_max + 1)]


@app.get("/api/backtest")
def get_backtest(game: str = Query("535"),
                 lookback: int = Query(50, ge=20, le=200),
                 predict_n: int = Query(100, ge=10, le=500)):
    """Chạy backtest và trả về accuracy metrics."""
    _validate_game(game)
    draws = load_results(game=game)
    return backtest(draws, lookback=lookback, predict_n=predict_n, game=game)


@app.post("/api/crawl")
def trigger_crawl(game: str = Query("535")):
    """Trigger crawl thủ công — không cần auth. Crawl kỳ mới nhất và tính lại score nếu có data mới."""
    _validate_game(game)
    try:
        from crawler import run_crawl, run_crawl_645, run_crawl_655
    except ImportError:
        from backend.crawler import run_crawl, run_crawl_645, run_crawl_655

    if game == "535":
        is_new, result = run_crawl()
    elif game == "645":
        is_new, result = run_crawl_645()
    else:
        is_new, result = run_crawl_655()

    if is_new:
        recalculate_scores(game=game)
    return {"game": game, "is_new": is_new, "result": result}


@app.post("/api/crawl-bulk")
def trigger_crawl_bulk(game: str = Query("535"),
                       n: int = Query(10, ge=1, le=50),
                       _: None = Depends(require_admin)):
    """Crawl nhiều kỳ (yêu cầu X-Admin-Key header)."""
    _validate_game(game)
    try:
        from crawler import run_crawl_bulk, run_crawl_bulk_645, run_crawl_bulk_655
    except ImportError:
        from backend.crawler import run_crawl_bulk, run_crawl_bulk_645, run_crawl_bulk_655

    if game == "535":
        saved = run_crawl_bulk(n=n)
    elif game == "645":
        saved = run_crawl_bulk_645(n=n)
    else:
        saved = run_crawl_bulk_655(n=n)

    if saved > 0:
        recalculate_scores(game=game)
    return {"game": game, "saved": saved, "requested": n}


@app.post("/api/recalculate")
def trigger_recalculate(game: str = Query("535"), _: None = Depends(require_admin)):
    """Tính lại toàn bộ score (yêu cầu X-Admin-Key header)."""
    _validate_game(game)
    num_sc, db_sc = recalculate_scores(game=game)
    return {
        "message":    "Recalculated",
        "game":       game,
        "num_scores": num_sc[:5],
        "db_scores":  db_sc[:3],
    }


@app.get("/health")
def health():
    return {"status": "ok", "db": DB_PATH}


# ---------------------------------------------------------------------------
# SPA catch-all — MUST be last; serves index.html for any unmatched route
# ---------------------------------------------------------------------------
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
