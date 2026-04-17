"""
scheduler.py — Cron job crawl Lotto 5/35 trong 2 cửa sổ mỗi ngày:
  - 13:30 và 14:00 (kỳ sáng, data trả về trễ)
  - 21:30 và 22:00 (kỳ tối, data trả về trễ)

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
# Crawl trong cửa sổ 13:30-14:00 và 21:30-22:00 để đảm bảo kết quả đã được đăng
# (data vietlott.vn đôi khi trả về trễ 30-60 phút)
schedule.every().day.at("13:30").do(job)
schedule.every().day.at("14:00").do(job)
schedule.every().day.at("21:30").do(job)
schedule.every().day.at("22:00").do(job)

if __name__ == "__main__":
    log.info("Scheduler đang chạy (13:30, 14:00, 21:30, 22:00 hằng ngày). Ctrl+C để dừng.")
    while True:
        schedule.run_pending()
        time.sleep(30)
