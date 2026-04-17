"""startup.py — Init DB and auto-seed/crawl if empty, then launch API."""
import sys
import subprocess

sys.path.insert(0, "/app")

try:
    from backend.db import init_db, get_conn

    # Always init schema (idempotent)
    init_db()

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
            from backend.engine import recalculate_scores
            recalculate_scores()
        except Exception as e:
            print(f"[startup] 535 score error: {e}", flush=True)
    else:
        print(f"[startup] 535 DB has {count535} draws — ready.", flush=True)

    # ── Mega 6/45 ─────────────────────────────────────────────────────────────
    with get_conn() as conn:
        count645 = conn.execute("SELECT COUNT(*) FROM results_645").fetchone()[0]

    if count645 == 0:
        print("[startup] 645 DB is empty — crawling Mega 6/45...", flush=True)
        try:
            from backend.crawler import run_crawl_bulk_645
            from backend.engine import recalculate_scores
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

    # ── Power 6/55 ────────────────────────────────────────────────────────────
    with get_conn() as conn:
        count655 = conn.execute("SELECT COUNT(*) FROM results_655").fetchone()[0]

    if count655 == 0:
        print("[startup] 655 DB is empty — crawling Power 6/55...", flush=True)
        try:
            from backend.crawler import run_crawl_bulk_655
            from backend.engine import recalculate_scores
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

except Exception as e:
    print(f"[startup] WARNING: startup error ({e}) — continuing anyway", flush=True)
