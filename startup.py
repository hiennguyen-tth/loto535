"""startup.py — Init DB and auto-seed/crawl if empty, then launch API."""
import sys
import subprocess

sys.path.insert(0, "/app")

try:
    from backend.db import init_db, get_conn

    # Always init schema (idempotent)
    init_db()

    # Check if DB has data
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]

    if count == 0:
        print("[startup] DB is empty — trying live crawl...", flush=True)
        # Try live crawl first
        try:
            from backend.crawler import run_crawl_bulk
            saved = run_crawl_bulk(n=10)
            if saved == 0:
                # Fall back to seed sample
                print("[startup] Crawl got no data — seeding sample...", flush=True)
                subprocess.run(["python", "/app/seed_sample.py"], check=False)
        except Exception as e:
            print(f"[startup] Crawl error: {e} — seeding sample...", flush=True)
            subprocess.run(["python", "/app/seed_sample.py"], check=False)

        # Recalculate scores
        try:
            from backend.engine import recalculate_scores
            recalculate_scores()
        except Exception as e:
            print(f"[startup] Score recalculate error: {e}", flush=True)
    else:
        print(f"[startup] DB has {count} draws — ready.", flush=True)

except Exception as e:
    print(f"[startup] WARNING: startup error ({e}) — continuing anyway", flush=True)
