"""
engine.py — Scoring + prediction logic cho Lotto 5/35

Composite score formula (chuẩn hoá 0–100):
    score = (freq_total / max_ft) * 40
          + (freq_30    / max_fw) * 30
          + (gap        / max_gap) * 30

Interpretation:
    - freq_total : lịch sử dài hạn — số "mạnh" về lâu dài
    - freq_30    : tần suất 30 kỳ gần nhất — số đang "hot"
    - gap        : càng lâu chưa ra → hệ số bù tăng (mean-reversion heuristic)
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


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_results(db_path: str = DB_PATH) -> list[tuple]:
    """
    Trả về list tuples (s1,s2,s3,s4,s5,db) sorted ascending by ky.
    Dùng tuple để dễ index và cache.
    """
    con = get_conn(db_path)
    cur = con.execute(
        "SELECT s1,s2,s3,s4,s5,db FROM results ORDER BY ky ASC"
    )
    rows = cur.fetchall()
    con.close()
    return [tuple(r) for r in rows]


# ---------------------------------------------------------------------------
# Core analytics
# ---------------------------------------------------------------------------

def compute_gap(num: int, draws: list[tuple], field_indices: list[int]) -> int:
    """
    Số kỳ kể từ lần cuối 'num' xuất hiện (tại các cột field_indices).
    draws phải được sort ASC theo ky.
    Trả về len(draws) nếu chưa bao giờ xuất hiện.
    """
    for i in range(len(draws) - 1, -1, -1):
        if num in [draws[i][j] for j in field_indices]:
            return len(draws) - 1 - i
    return len(draws)


def score_numbers(draws: list[tuple], window: int = WINDOW_DEFAULT) -> list[dict]:
    """
    Tính composite score cho từng số 1–35.
    Trả về list[dict] sorted descending by score.
    """
    if not draws:
        return [{"so": n, "freq_total": 0, "freq_30": 0, "gap": 0, "score": 0.0}
                for n in range(1, 36)]

    recent   = draws[-window:] if len(draws) >= window else draws
    main_idx = [0, 1, 2, 3, 4]

    results = []
    for num in range(1, 36):
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


def score_db_numbers(draws: list[tuple], window: int = WINDOW_DEFAULT) -> list[dict]:
    """
    Tính composite score cho số đặc biệt DB (1–12).
    Cùng công thức với score_numbers.
    """
    if not draws:
        return [{"db": n, "freq_total": 0, "freq_30": 0, "gap": 0, "score": 0.0}
                for n in range(1, 13)]

    recent = draws[-window:] if len(draws) >= window else draws

    results = []
    for db in range(1, 13):
        freq_total = sum(1 for r in draws  if r[5] == db)
        freq_win   = sum(1 for r in recent if r[5] == db)
        gap        = compute_gap(db, draws, [5])
        results.append({"db": db, "freq_total": freq_total,
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
# Set generation
# ---------------------------------------------------------------------------

def _valid_sum(nums: list[int], lo: int = SUM_MIN, hi: int = SUM_MAX) -> bool:
    return lo <= sum(nums) <= hi


def _is_valid_set(nums: list[int]) -> bool:
    """Loại bỏ bộ số thống kê bất thường."""
    s = sorted(nums)
    total = sum(s)
    if not (55 <= total <= 120):
        return False
    if s[-1] - s[0] < 8:          # quá cụm
        return False
    evens = sum(1 for n in s if n % 2 == 0)
    if evens == 0 or evens == 5:   # toàn chẵn / toàn lẻ
        return False
    consecutive = sum(1 for a, b in zip(s, s[1:]) if b - a == 1)
    if consecutive >= 4:           # 4 số liên tiếp cực hiếm
        return False
    return True


def _weighted_pick(pool: list[int], scores_map: dict[int, float],
                   k: int = 5, max_tries: int = 800) -> list[int]:
    """Chọn k số từ pool theo trọng số score, đảm bảo tổng hợp lệ."""
    weights = [max(scores_map.get(n, 0.1), 0.1) for n in pool]
    for _ in range(max_tries):
        picked = random.choices(pool, weights=weights, k=k * 4)
        # dedup, preserve weighted order
        seen = set()
        unique = []
        for p in picked:
            if p not in seen:
                seen.add(p)
                unique.append(p)
            if len(unique) == k:
                break
        if len(unique) == k and _is_valid_set(unique):
            return sorted(unique)
    # fallback: lấy ngẫu nhiên không theo trọng số nhưng hợp lệ
    for _ in range(200):
        s = sorted(random.sample(pool, k))
        if _is_valid_set(s):
            return s
    return sorted(random.sample(pool, k))


def _confidence(nums: list[int], scores_map: dict) -> int:
    """Mean score of the set's numbers, rounded to int (0-100)."""
    s = [scores_map.get(n, 0) for n in nums]
    return round(sum(s) / len(s)) if s else 0


def _tags(nums: list[int], hot_set: set, gap_set: set, top15_set: set) -> list[str]:
    """Return descriptive tags for a set of numbers."""
    tags = []
    hot_count = sum(1 for n in nums if n in hot_set)
    gap_count = sum(1 for n in nums if n in gap_set)
    evens     = sum(1 for n in nums if n % 2 == 0)
    if hot_count >= 2: tags.append("HOT")
    if gap_count >= 1: tags.append("GAP")
    if 2 <= evens <= 3: tags.append("BALANCED")
    if all(n in top15_set for n in nums): tags.append("STABLE")
    return tags[:3] if tags else ["STABLE"]


def generate_sets(
    num_scores: list[dict],
    db_scores: list[dict],
    n_sets: int = 5,
) -> list[dict]:
    """
    Sinh {n_sets} bộ số theo nhiều chiến lược khác nhau.

    Chiến lược:
        Bộ 1 — Top 5 composite score
        Bộ 2 — Top 3 composite + 2 số gap cao nhất
        Bộ 3 — Top 3 freq_total + 2 top freq_30 (đang hot)
        Bộ 4 — Weighted random từ top 15
        Bộ 5 — Weighted random từ top 15 (seed khác)
    """
    scores_map = {r["so"]: r["score"] for r in num_scores}

    top15     = [r["so"] for r in num_scores[:15]]
    top5      = [r["so"] for r in num_scores[:5]]
    top_gap   = sorted(num_scores, key=lambda x: x["gap"], reverse=True)
    hot_set   = {r["so"] for r in sorted(num_scores, key=lambda x: x["freq_30"], reverse=True)[:7]}
    gap_set   = {r["so"] for r in top_gap[:7]}
    top15_set = set(top15)
    top_ft  = sorted(num_scores, key=lambda x: x["freq_total"], reverse=True)
    top_hot = sorted(num_scores, key=lambda x: x["freq_30"], reverse=True)

    db_top = [r["db"] for r in db_scores[:3]]
    db0 = db_top[0] if db_top else 1
    db1 = db_top[1] if len(db_top) > 1 else db0
    db2 = db_top[2] if len(db_top) > 2 else db0

    # Bộ 1: top 5 composite
    bo1 = sorted(top5)
    if not _is_valid_set(bo1):
        bo1 = _weighted_pick(top15, scores_map)

    # Bộ 2: top 3 + 2 gap cao nhất (không trùng top3)
    top3 = top5[:3]
    gap_extra = [r["so"] for r in top_gap if r["so"] not in top3][:2]
    bo2_pool = top3 + gap_extra
    bo2 = sorted(bo2_pool[:5])
    if not _is_valid_set(bo2):
        bo2 = _weighted_pick(top15, scores_map)

    # Bộ 3: lịch sử dài hạn + đang hot
    seen3: list[int] = []
    for r in top_ft[:3]:
        if r["so"] not in seen3:
            seen3.append(r["so"])
    for r in top_hot:
        if r["so"] not in seen3:
            seen3.append(r["so"])
        if len(seen3) == 5:
            break
    bo3 = sorted(seen3[:5])
    if not _is_valid_set(bo3):
        bo3 = _weighted_pick(top15, scores_map)

    # Bộ 4 & 5: weighted random
    bo4 = _weighted_pick(top15, scores_map)
    bo5 = _weighted_pick(top15, scores_map)

    def _mk(name, nums, db):
        return {
            "ten": name, "nums": nums, "db": db,
            "confidence": _confidence(nums, scores_map),
            "tags": _tags(nums, hot_set, gap_set, top15_set),
        }

    return [
        _mk("Bộ 1 — Top composite",        bo1, db0),
        _mk("Bộ 2 — Composite + Gap",       bo2, db1),
        _mk("Bộ 3 — Lịch sử + Đang hot",   bo3, db2),
        _mk("Bộ 4 — Weighted random",       bo4, db0),
        _mk("Bộ 5 — Weighted random (alt)", bo5, db1),
    ]


# ---------------------------------------------------------------------------
# DB caching
# ---------------------------------------------------------------------------

def recalculate_scores(db_path: str = DB_PATH) -> tuple[list[dict], list[dict]]:
    """Tính lại toàn bộ scoring và persist vào scoring_cache / scoring_db."""
    draws      = load_results(db_path)
    num_scores = score_numbers(draws)
    db_scores  = score_db_numbers(draws)

    con = get_conn(db_path)
    try:
        con.execute("DELETE FROM scoring_cache")
        con.executemany(
            "INSERT INTO scoring_cache (so,freq_total,freq_30,gap,score) VALUES (?,?,?,?,?)",
            [(r["so"], r["freq_total"], r["freq_30"], r["gap"], r["score"])
             for r in num_scores],
        )

        con.execute("DELETE FROM scoring_db")
        con.executemany(
            "INSERT INTO scoring_db (db,freq_total,freq_30,gap,score) VALUES (?,?,?,?,?)",
            [(r["db"], r["freq_total"], r["freq_30"], r["gap"], r["score"])
             for r in db_scores],
        )
        con.commit()
    finally:
        con.close()

    print(f"[engine] Score calculated: {len(num_scores)} numbers, {len(db_scores)} DB nums "
          f"(based on {len(draws)} draws).")
    return num_scores, db_scores


# ---------------------------------------------------------------------------
# Backtest helpers
# ---------------------------------------------------------------------------

def backtest(draws: list[tuple], lookback: int = 50, predict_n: int = 100) -> dict:
    """
    Đánh giá mô hình trên {predict_n} kỳ cuối.
    Metrics:
        accuracy_pct — tỷ lệ top-5 có ≥2 số trúng
        hit3_pct     — tỷ lệ top-10 có ≥3 số trúng
        avg_hits     — trung bình số trùng trong top-10
    """
    total = min(predict_n, len(draws) - lookback)
    if total <= 0:
        return {"error": "Not enough draws for backtest",
                "total_tested": 0, "accuracy_pct": 0, "avg_hits": 0}

    hit2, hit3, total_hits, best_streak, cur_streak = 0, 0, 0, 0, 0
    for i in range(len(draws) - total, len(draws)):
        history = draws[max(0, i - lookback):i]
        actual  = set(draws[i][:5])
        sc      = score_numbers(history)
        top5    = {r["so"] for r in sc[:5]}
        top10   = {r["so"] for r in sc[:10]}
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
    scores, db_s = recalculate_scores()
    print("Top 10 numbers:", [r["so"] for r in scores[:10]])
    print("Top 5 DB:      ", [r["db"] for r in db_s[:5]])
