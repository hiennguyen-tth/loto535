"""
engine.py — Scoring + prediction logic cho LottoAI (5/35, Mega 6/45, Power 6/55)

Composite score formula (chuẩn hoá 0–100):
    score = (freq_total / max_ft) * 40
          + (freq_30    / max_fw) * 30
          + (gap        / max_gap) * 30
"""
import sqlite3
import random
from functools import lru_cache

try:
    from db import DB_PATH, get_conn
except ImportError:
    from backend.db import DB_PATH, get_conn

WINDOW_DEFAULT = 30
SUM_MIN = 68
SUM_MAX = 112

# Game configurations
GAME_CONFIGS = {
    "535": {
        "main_n": 5, "main_max": 35, "has_power": False,
        "has_db": True, "db_max": 12,
        "table": "results", "score_table": "scoring_cache",
        "score_db_table": "scoring_db",
        "sum_min": 55, "sum_max": 125, "spread_min": 8,
        "select_cols": "s1,s2,s3,s4,s5,db",
    },
    "645": {
        "main_n": 6, "main_max": 45, "has_power": False,
        "has_db": False, "db_max": None,
        "table": "results_645", "score_table": "scoring_645",
        "score_db_table": None,
        "sum_min": 75, "sum_max": 210, "spread_min": 10,
        "select_cols": "s1,s2,s3,s4,s5,s6",
    },
    "655": {
        "main_n": 6, "main_max": 55, "has_power": True,
        "has_db": False, "db_max": 55,
        "table": "results_655", "score_table": "scoring_655",
        "score_db_table": "scoring_655_power",
        "sum_min": 85, "sum_max": 240, "spread_min": 12,
        "select_cols": "s1,s2,s3,s4,s5,s6,power",
    },
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_results(db_path: str = DB_PATH, game: str = "535") -> list[tuple]:
    """
    Trả về list tuples sorted ascending by ky.
    535: (s1,s2,s3,s4,s5,db)
    645: (s1,s2,s3,s4,s5,s6)
    655: (s1,s2,s3,s4,s5,s6,power)
    """
    cfg = GAME_CONFIGS[game]
    con = get_conn(db_path)
    cur = con.execute(
        f"SELECT {cfg['select_cols']} FROM {cfg['table']} ORDER BY ky ASC"
    )
    rows = cur.fetchall()
    con.close()
    return [tuple(r) for r in rows]


# ---------------------------------------------------------------------------
# Core analytics
# ---------------------------------------------------------------------------

def compute_gap(num: int, draws: list[tuple], field_indices: list[int]) -> int:
    """
    Số kỳ kể từ lần cuối 'num' xuất hiện tại các field_indices.
    draws phải sort ASC theo ky.
    """
    for i in range(len(draws) - 1, -1, -1):
        if num in [draws[i][j] for j in field_indices]:
            return len(draws) - 1 - i
    return len(draws)


def score_numbers(draws: list[tuple], window: int = WINDOW_DEFAULT,
                  game: str = "535") -> list[dict]:
    """
    Tính composite score cho từng số chính theo game type.
    Trả về list[dict] sorted descending by score.
    """
    cfg = GAME_CONFIGS[game]
    main_n   = cfg["main_n"]
    main_max = cfg["main_max"]
    main_idx = list(range(main_n))

    if not draws:
        return [{"so": n, "freq_total": 0, "freq_30": 0, "gap": 0, "score": 0.0}
                for n in range(1, main_max + 1)]

    recent = draws[-window:] if window > 0 and len(draws) >= window else draws

    results = []
    for num in range(1, main_max + 1):
        freq_total = sum(1 for r in draws  if num in (r[j] for j in main_idx))
        freq_win   = sum(1 for r in recent if num in (r[j] for j in main_idx))
        gap        = compute_gap(num, draws, main_idx)
        results.append({"so": num, "freq_total": freq_total,
                        "freq_30": freq_win, "gap": gap})

    max_ft  = max(r["freq_total"] for r in results) or 1
    max_fw  = max(r["freq_30"]    for r in results) or 1
    max_gap = max(r["gap"]        for r in results) or 1

    for r in results:
        r["score"] = round(
            (r["freq_total"] / max_ft)  * 40 +
            (r["freq_30"]    / max_fw)  * 30 +
            (r["gap"]        / max_gap) * 30,
            4,
        )

    return sorted(results, key=lambda x: x["score"], reverse=True)


def score_db_numbers(draws: list[tuple], window: int = WINDOW_DEFAULT,
                     game: str = "535") -> list[dict]:
    """
    Tính composite score cho số đặc biệt (DB / Power).
    535: DB col index 5, range 1-12
    655: Power col index 6, range 1-55
    """
    cfg = GAME_CONFIGS[game]
    if not cfg["has_db"] and not cfg["has_power"]:
        return []

    if game == "535":
        db_idx = 5
        db_max = 12
        key    = "db"
    else:  # 655
        db_idx = 6
        db_max = 55
        key    = "db"

    if not draws:
        return [{key: n, "freq_total": 0, "freq_30": 0, "gap": 0, "score": 0.0}
                for n in range(1, db_max + 1)]

    recent = draws[-window:] if window > 0 and len(draws) >= window else draws

    results = []
    for db in range(1, db_max + 1):
        freq_total = sum(1 for r in draws  if r[db_idx] == db)
        freq_win   = sum(1 for r in recent if r[db_idx] == db)
        gap        = compute_gap(db, draws, [db_idx])
        results.append({key: db, "freq_total": freq_total,
                        "freq_30": freq_win, "gap": gap})

    max_ft  = max(r["freq_total"] for r in results) or 1
    max_fw  = max(r["freq_30"]    for r in results) or 1
    max_gap = max(r["gap"]        for r in results) or 1

    for r in results:
        r["score"] = round(
            (r["freq_total"] / max_ft)  * 40 +
            (r["freq_30"]    / max_fw)  * 30 +
            (r["gap"]        / max_gap) * 30,
            4,
        )

    return sorted(results, key=lambda x: x["score"], reverse=True)


# ---------------------------------------------------------------------------
# Set validation
# ---------------------------------------------------------------------------

def _is_valid_set(nums: list[int], game: str = "535") -> bool:
    """Loại bỏ bộ số thống kê bất thường dựa theo game."""
    cfg = GAME_CONFIGS[game]
    s = sorted(nums)
    total = sum(s)
    n = len(s)

    if not (cfg["sum_min"] <= total <= cfg["sum_max"]):
        return False
    if s[-1] - s[0] < cfg["spread_min"]:
        return False
    evens = sum(1 for x in s if x % 2 == 0)
    if evens == 0 or evens == n:
        return False
    consecutive = sum(1 for a, b in zip(s, s[1:]) if b - a == 1)
    if consecutive >= 4:
        return False
    return True


def _weighted_pick(pool: list[int], scores_map: dict[int, float],
                   k: int, game: str = "535", max_tries: int = 800) -> list[int]:
    weights = [max(scores_map.get(n, 0.1), 0.1) for n in pool]
    for _ in range(max_tries):
        picked = random.choices(pool, weights=weights, k=k * 4)
        seen = set()
        unique = []
        for p in picked:
            if p not in seen:
                seen.add(p)
                unique.append(p)
            if len(unique) == k:
                break
        if len(unique) == k and _is_valid_set(unique, game):
            return sorted(unique)
    for _ in range(200):
        s = sorted(random.sample(pool, k))
        if _is_valid_set(s, game):
            return s
    return sorted(random.sample(pool, k))


def _confidence(nums: list[int], scores_map: dict) -> int:
    s = [scores_map.get(n, 0) for n in nums]
    return round(sum(s) / len(s)) if s else 0


def _tags(nums: list[int], hot_set: set, gap_set: set, top_set: set) -> list[str]:
    tags = []
    hot_count = sum(1 for n in nums if n in hot_set)
    gap_count = sum(1 for n in nums if n in gap_set)
    evens     = sum(1 for n in nums if n % 2 == 0)
    n = len(nums)
    if hot_count >= 2: tags.append("HOT")
    if gap_count >= 1: tags.append("GAP")
    if 2 <= evens <= n - 2: tags.append("BALANCED")
    if all(x in top_set for x in nums): tags.append("STABLE")
    return tags[:3] if tags else ["STABLE"]


# ---------------------------------------------------------------------------
# Set generation (game-aware)
# ---------------------------------------------------------------------------

def generate_sets(
    num_scores: list[dict],
    db_scores: list[dict],
    n_sets: int = 5,
    game: str = "535",
) -> list[dict]:
    """
    Sinh {n_sets} bộ số theo nhiều chiến lược. Hoạt động với 535, 645, 655.
    """
    cfg   = GAME_CONFIGS[game]
    k     = cfg["main_n"]
    topN  = min(15, len(num_scores))
    top5N = min(k, len(num_scores))

    scores_map = {r["so"]: r["score"] for r in num_scores}
    top_pool = [r["so"] for r in num_scores[:topN]]
    top_k    = [r["so"] for r in num_scores[:top5N]]
    top_gap  = sorted(num_scores, key=lambda x: x["gap"], reverse=True)
    hot_set  = {r["so"] for r in sorted(num_scores, key=lambda x: x["freq_30"], reverse=True)[:7]}
    gap_set  = {r["so"] for r in top_gap[:7]}
    top_set  = set(top_pool)
    top_ft   = sorted(num_scores, key=lambda x: x["freq_total"], reverse=True)
    top_hot  = sorted(num_scores, key=lambda x: x["freq_30"], reverse=True)

    # DB / Power selection
    if game == "535":
        db_top = [r["db"] for r in db_scores[:3]]
        db0 = db_top[0] if db_top else 1
        db1 = db_top[1] if len(db_top) > 1 else db0
        db2 = db_top[2] if len(db_top) > 2 else db0
        has_db = True
    elif game == "655":
        db_top = [r["db"] for r in db_scores[:3]]
        db0 = db_top[0] if db_top else 1
        db1 = db_top[1] if len(db_top) > 1 else db0
        db2 = db_top[2] if len(db_top) > 2 else db0
        has_db = True
    else:
        db0 = db1 = db2 = None
        has_db = False

    # Bộ 1: top k composite
    bo1 = sorted(top_k)
    if not _is_valid_set(bo1, game):
        bo1 = _weighted_pick(top_pool, scores_map, k, game)

    # Bộ 2: top (k-2) + 2 gap
    top_base = top_k[:k - 2]
    gap_extra = [r["so"] for r in top_gap if r["so"] not in top_base][:2]
    bo2 = sorted((top_base + gap_extra)[:k])
    if not _is_valid_set(bo2, game):
        bo2 = _weighted_pick(top_pool, scores_map, k, game)

    # Bộ 3: lịch sử dài hạn + đang hot
    seen3: list[int] = []
    for r in top_ft[:k - 2]:
        if r["so"] not in seen3:
            seen3.append(r["so"])
    for r in top_hot:
        if r["so"] not in seen3:
            seen3.append(r["so"])
        if len(seen3) == k:
            break
    bo3 = sorted(seen3[:k])
    if not _is_valid_set(bo3, game):
        bo3 = _weighted_pick(top_pool, scores_map, k, game)

    # Bộ 4 & 5: weighted random
    bo4 = _weighted_pick(top_pool, scores_map, k, game)
    bo5 = _weighted_pick(top_pool, scores_map, k, game)

    def _mk(name, nums, db):
        return {
            "ten": name, "nums": nums, "db": db,
            "confidence": _confidence(nums, scores_map),
            "tags": _tags(nums, hot_set, gap_set, top_set),
        }

    return [
        _mk("Bộ 1 — Top composite",        bo1, db0),
        _mk("Bộ 2 — Composite + Gap",       bo2, db1),
        _mk("Bộ 3 — Lịch sử + Đang hot",   bo3, db2),
        _mk("Bộ 4 — Weighted random",       bo4, db0),
        _mk("Bộ 5 — Weighted random (alt)", bo5, db1),
    ]


# ---------------------------------------------------------------------------
# DB caching (game-aware)
# ---------------------------------------------------------------------------

def recalculate_scores(db_path: str = DB_PATH, game: str = "535") -> tuple[list[dict], list[dict]]:
    """Tính lại toàn bộ scoring và persist vào bảng cache của từng game."""
    cfg        = GAME_CONFIGS[game]
    draws      = load_results(db_path, game=game)
    num_scores = score_numbers(draws, game=game)
    db_scores  = score_db_numbers(draws, game=game)

    con = get_conn(db_path)
    try:
        # Main numbers cache
        con.execute(f"DELETE FROM {cfg['score_table']}")
        if game == "535":
            con.executemany(
                "INSERT INTO scoring_cache (so,freq_total,freq_30,gap,score) VALUES (?,?,?,?,?)",
                [(r["so"], r["freq_total"], r["freq_30"], r["gap"], r["score"])
                 for r in num_scores],
            )
        elif game == "645":
            con.executemany(
                "INSERT INTO scoring_645 (so,freq_total,freq_30,gap,score) VALUES (?,?,?,?,?)",
                [(r["so"], r["freq_total"], r["freq_30"], r["gap"], r["score"])
                 for r in num_scores],
            )
        elif game == "655":
            con.executemany(
                "INSERT INTO scoring_655 (so,freq_total,freq_30,gap,score) VALUES (?,?,?,?,?)",
                [(r["so"], r["freq_total"], r["freq_30"], r["gap"], r["score"])
                 for r in num_scores],
            )

        # DB/Power numbers cache
        if game == "535" and db_scores:
            con.execute("DELETE FROM scoring_db")
            con.executemany(
                "INSERT INTO scoring_db (db,freq_total,freq_30,gap,score) VALUES (?,?,?,?,?)",
                [(r["db"], r["freq_total"], r["freq_30"], r["gap"], r["score"])
                 for r in db_scores],
            )
        elif game == "655" and db_scores:
            con.execute("DELETE FROM scoring_655_power")
            con.executemany(
                "INSERT INTO scoring_655_power (so,freq_total,freq_30,gap,score) VALUES (?,?,?,?,?)",
                [(r["db"], r["freq_total"], r["freq_30"], r["gap"], r["score"])
                 for r in db_scores],
            )

        con.commit()
    finally:
        con.close()

    print(f"[engine:{game}] Score calculated: {len(num_scores)} numbers, "
          f"{len(db_scores)} DB/Power nums (based on {len(draws)} draws).")
    return num_scores, db_scores


# ---------------------------------------------------------------------------
# Backtest helpers (game-aware)
# ---------------------------------------------------------------------------

def backtest(draws: list[tuple], lookback: int = 50, predict_n: int = 100,
             game: str = "535") -> dict:
    """
    Đánh giá mô hình trên {predict_n} kỳ cuối.
    """
    cfg = GAME_CONFIGS[game]
    k   = cfg["main_n"]
    total = min(predict_n, len(draws) - lookback)
    if total <= 0:
        return {"error": "Not enough draws for backtest",
                "total_tested": 0, "accuracy_pct": 0, "avg_hits": 0}

    hit2, hit3, total_hits, best_streak, cur_streak = 0, 0, 0, 0, 0
    for i in range(len(draws) - total, len(draws)):
        history = draws[max(0, i - lookback):i]
        actual  = set(draws[i][:k])
        sc      = score_numbers(history, game=game)
        top5    = {r["so"] for r in sc[:k]}
        top10   = {r["so"] for r in sc[:k * 2]}
        hits    = len(actual & top10)
        total_hits += hits
        if len(actual & top5) >= 2:
            hit2 += 1
            cur_streak += 1
            best_streak = max(best_streak, cur_streak)
        else:
            cur_streak = 0
        if hits >= 3:
            hit3 += 1

    return {
        "total_tested":  total,
        "accuracy_pct":  round(hit2 / total * 100, 1),
        "hit3_pct":      round(hit3 / total * 100, 1),
        "avg_hits":      round(total_hits / total, 2),
        "best_streak":   best_streak,
        "hit2_in_top5":  f"{hit2 / total * 100:.1f}%",
        "hit3_in_top10": f"{hit3 / total * 100:.1f}%",
    }


if __name__ == "__main__":
    for g in ("535", "645", "655"):
        scores, db_s = recalculate_scores(game=g)
        print(f"[{g}] Top 10:", [r["so"] for r in scores[:10]])
        if db_s:
            print(f"[{g}] Top 5 DB/Power:", [r["db"] for r in db_s[:5]])


