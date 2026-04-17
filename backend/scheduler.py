"""
scheduler.py — Cron job crawl 3 loại Lotto:
  - Lotto 5/35: quay 13h00 & 21h00 hằng ngày → crawl lúc 13:30, 14:00, 21:30, 22:00
  - Mega 6/45: quay 18h00 T4, T6, CN → crawl lúc 18:30, 19:00
  - Power 6/55: quay 18h00 T3, T5, T7 → crawl lúc 18:30, 19:00

Chạy:
    python backend/scheduler.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import schedule
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [scheduler] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def job_535():
    log.info("[535] Bắt đầu crawl Lotto 5/35...")
    try:
        from crawler import run_crawl
        from engine import recalculate_scores

        is_new, result = run_crawl()
        if is_new:
            log.info(f"[535] Có kết quả mới (kỳ #{result['ky']}), tính lại score...")
            recalculate_scores()
        else:
            log.info("[535] Không có dữ liệu mới.")
    except Exception as e:
        log.error(f"[535] Job thất bại: {e}", exc_info=True)


def job_645():
    log.info("[645] Bắt đầu crawl Mega 6/45...")
    try:
        from crawler import run_crawl_645
        from engine import recalculate_scores

        is_new, result = run_crawl_645()
        if is_new:
            log.info(f"[645] Có kết quả mới (kỳ #{result['ky']}), tính lại score...")
            recalculate_scores(game="645")
        else:
            log.info("[645] Không có dữ liệu mới.")
    except Exception as e:
        log.error(f"[645] Job thất bại: {e}", exc_info=True)


def job_655():
    log.info("[655] Bắt đầu crawl Power 6/55...")
    try:
        from crawler import run_crawl_655
        from engine import recalculate_scores

        is_new, result = run_crawl_655()
        if is_new:
            log.info(f"[655] Có kết quả mới (kỳ #{result['ky']}), tính lại score...")
            recalculate_scores(game="655")
        else:
            log.info("[655] Không có dữ liệu mới.")
    except Exception as e:
        log.error(f"[655] Job thất bại: {e}", exc_info=True)


# Lotto 5/35: hằng ngày lúc 13:00 & 21:00 → crawl 13:30, 14:00, 21:30, 22:00
schedule.every().day.at("13:30").do(job_535)
schedule.every().day.at("14:00").do(job_535)
schedule.every().day.at("21:30").do(job_535)
schedule.every().day.at("22:00").do(job_535)

# Mega 6/45: T4=Wednesday, T6=Friday, CN=Sunday lúc 18:00 → crawl 18:30, 19:00
schedule.every().wednesday.at("18:30").do(job_645)
schedule.every().wednesday.at("19:00").do(job_645)
schedule.every().friday.at("18:30").do(job_645)
schedule.every().friday.at("19:00").do(job_645)
schedule.every().sunday.at("18:30").do(job_645)
schedule.every().sunday.at("19:00").do(job_645)

# Power 6/55: T3=Tuesday, T5=Thursday, T7=Saturday lúc 18:00 → crawl 18:30, 19:00
schedule.every().tuesday.at("18:30").do(job_655)
schedule.every().tuesday.at("19:00").do(job_655)
schedule.every().thursday.at("18:30").do(job_655)
schedule.every().thursday.at("19:00").do(job_655)
schedule.every().saturday.at("18:30").do(job_655)
schedule.every().saturday.at("19:00").do(job_655)

if __name__ == "__main__":
    log.info("Scheduler đang chạy cho 535/645/655. Ctrl+C để dừng.")
    while True:
        schedule.run_pending()
        time.sleep(30)
