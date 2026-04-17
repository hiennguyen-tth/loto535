"""startup.py — Init DB and auto-seed/crawl if empty, then launch API."""
import sys
import subprocess

sys.path.insert(0, "/app")

try:
    from backend.db import init_db, get_conn
    from backend.engine import recalculate_scores

    # Always init schema (idempotent)
    init_db()

    def _ensure_scores(game: str, score_table: str):
        """Recalculate scoring cache if it's empty but we have draw data."""
        with get_conn() as conn:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {score_table}").fetchone()[0]
        if cnt == 0:
            print(f"[startup] {game} scoring cache empty — recalculating...", flush=True)
            try:
                recalculate_scores(game=game)
            except Exception as e:
                print(f"[startup] {game} score rebuild error: {e}", flush=True)

    # ── Lotto 5/35 ────────────────────────────────────────────────────────────
    with get_conn() as conn:
        count535 = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]

    if count535 == 0:
        print("[startup] 535 DB is empty — trying live crawl...", flush=True)
        try:
            from backend.crawler import run_crawl_bulk
            saved = run_crawl_bulk(n=10)
            if saved == 0:
                print("[startup] 535 crawl got no data — seeding sample...", flush=True)
                subprocess.run(["python", "/app/seed_sample.py"], check=False)
        except Exception as e:
            print(f"[startup] 535 crawl error: {e} — seeding sample...", flush=True)
            subprocess.run(["python", "/app/seed_sample.py"], check=False)
        try:
            recalculate_scores()
        except Exception as e:
            print(f"[startup] 535 score error: {e}", flush=True)
    else:
        print(f"[startup] 535 DB has {count535} draws — ready.", flush=True)
        _ensure_scores("535", "scoring_cache")
        # Catch-up: grab latest draw in case machine was suspended during scheduled crawl
        try:
            from backend.crawler import run_crawl
            is_new, result = run_crawl()
            if is_new:
                print(f"[startup] 535 catch-up: kỳ #{result['ky']} mới — recalculating...", flush=True)
                recalculate_scores()
            else:
                print("[startup] 535 already up-to-date.", flush=True)
        except Exception as e:
            print(f"[startup] 535 catch-up error: {e}", flush=True)

    # ── Mega 6/45 ─────────────────────────────────────────────────────────────
    with get_conn() as conn:
        count645 = conn.execute("SELECT COUNT(*) FROM results_645").fetchone()[0]

    if count645 == 0:
        print("[startup] 645 DB is empty — crawling Mega 6/45...", flush=True)
        try:
            from backend.crawler import run_crawl_bulk_645
            saved645 = run_crawl_bulk_645(n=8)
            if saved645 > 0:
                recalculate_scores(game="645")
                print(f"[startup] 645 seeded {saved645} draws.", flush=True)
            else:
                print("[startup] 645 crawl returned no data.", flush=True)
        except Exception as e:
            print(f"[startup] 645 crawl error: {e}", flush=True)
    else:
        print(f"[startup] 645 DB has {count645} draws — ready.", flush=True)
        _ensure_scores("645", "scoring_645")
        # Catch-up: grab latest draw in case machine was suspended during scheduled crawl
        try:
            from backend.crawler import run_crawl_645
            is_new, result = run_crawl_645()
            if is_new:
                print(f"[startup] 645 catch-up: kỳ #{result['ky']} mới — recalculating...", flush=True)
                recalculate_scores(game="645")
            else:
                print("[startup] 645 already up-to-date.", flush=True)
        except Exception as e:
            print(f"[startup] 645 catch-up error: {e}", flush=True)

    # ── Power 6/55 ────────────────────────────────────────────────────────────
    with get_conn() as conn:
        count655 = conn.execute("SELECT COUNT(*) FROM results_655").fetchone()[0]

    if count655 == 0:
        print("[startup] 655 DB is empty — crawling Power 6/55...", flush=True)
        try:
            from backend.crawler import run_crawl_bulk_655
            saved655 = run_crawl_bulk_655(n=8)
            if saved655 > 0:
                recalculate_scores(game="655")
                print(f"[startup] 655 seeded {saved655} draws.", flush=True)
            else:
                print("[startup] 655 crawl returned no data.", flush=True)
        except Exception as e:
            print(f"[startup] 655 crawl error: {e}", flush=True)
    else:
        print(f"[startup] 655 DB has {count655} draws — ready.", flush=True)
        _ensure_scores("655", "scoring_655")
        # Catch-up: grab latest draw in case machine was suspended during scheduled crawl
        try:
            from backend.crawler import run_crawl_655
            is_new, result = run_crawl_655()
            if is_new:
                print(f"[startup] 655 catch-up: kỳ #{result['ky']} mới — recalculating...", flush=True)
                recalculate_scores(game="655")
            else:
                print("[startup] 655 already up-to-date.", flush=True)
        except Exception as e:
            print(f"[startup] 655 catch-up error: {e}", flush=True)

except Exception as e:
    print(f"[startup] WARNING: startup error ({e}) — continuing anyway", flush=True)
