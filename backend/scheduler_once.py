"""
scheduler_once.py — Chạy 1 lần rồi thoát (dùng với cron / GitHub Actions).

Dùng:
    python backend/scheduler_once.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

try:
    from db import init_db
    from crawler import run_crawl
    from engine import recalculate_scores

    init_db()
    is_new, result = run_crawl()
    if is_new:
        log.info(f"Kết quả mới: kỳ #{result['ky']} — {result['ngay']}")
        recalculate_scores()
    else:
        log.info("Không có kết quả mới.")
    sys.exit(0)
except Exception as e:
    log.error(f"Lỗi: {e}", exc_info=True)
    sys.exit(1)
