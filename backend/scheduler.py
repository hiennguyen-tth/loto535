"""
scheduler.py — Cron job crawl Lotto 5/35 lúc 13:30 & 22:00 mỗi ngày.

Chạy:
    python backend/scheduler.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import schedule
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [scheduler] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def job():
    log.info("Bắt đầu crawl...")
    try:
        from crawler import run_crawl
        from engine import recalculate_scores

        is_new, result = run_crawl()
        if is_new:
            log.info(f"Có kết quả mới (kỳ #{result['ky']}), tính lại score...")
            recalculate_scores()
        else:
            log.info("Không có dữ liệu mới.")
    except Exception as e:
        log.error(f"Job thất bại: {e}", exc_info=True)


# Lotto 5/35 quay lúc 13h00 và 21h00
# Crawl lúc 13:30 và 22:00 để đảm bảo kết quả đã được đăng
schedule.every().day.at("13:30").do(job)
schedule.every().day.at("22:00").do(job)

if __name__ == "__main__":
    log.info("Scheduler đang chạy (13:30 & 22:00 hằng ngày). Ctrl+C để dừng.")
    while True:
        schedule.run_pending()
        time.sleep(30)
