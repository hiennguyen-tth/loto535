"""
crawler.py — Crawl kết quả Lotto 5/35 từ vietlott.vn (+ backup)

Chiến lược:
  1. Thử vietlott.vn (official) → parse HTML table
  2. Fallback sang ketquadientoan.com nếu lỗi / không có dữ liệu
  3. Trả về None nếu cả hai đều thất bại
"""
import re
import time
import sqlite3
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

try:
    from db import DB_PATH, get_conn
except ImportError:
    from backend.db import DB_PATH, get_conn

VIETLOTT_URL = "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/535.html"
BACKUP_URL   = "https://www.ketquadientoan.com/ket-qua-xo-so-dien-toan-lotto-535.html"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

TIMEOUT = 20  # seconds


def _parse_row(cols) -> dict | None:
    """Parse một dòng <tr> của bảng kết quả vietlott."""
    try:
        ky_text   = cols[0].get_text(strip=True)
        date_text = cols[1].get_text(strip=True)
        nums_text = cols[2].get_text(separator=" ", strip=True)

        ky_m = re.search(r"\d+", ky_text)
        if not ky_m:
            return None
        ky = int(ky_m.group())

        # "15/04/2026 - 13H" or "15/04/2026 13H"
        date_m = re.search(r"(\d{2}/\d{2}/\d{4})", date_text)
        if not date_m:
            return None
        ngay = datetime.strptime(date_m.group(1), "%d/%m/%Y").date()
        buoi = "S" if re.search(r"13[Hh]", date_text) else "T"

        # Extract all integers from nums cell
        all_nums = [int(x) for x in re.findall(r"\d+", nums_text)]
        # Filter to valid ranges: main 1-35, db 1-12
        main_candidates = [n for n in all_nums if 1 <= n <= 35]
        db_candidates   = [n for n in all_nums if 1 <= n <= 12]

        if len(main_candidates) < 5:
            return None

        s1, s2, s3, s4, s5 = sorted(main_candidates[:5])
        # DB is the last number in the cell, typically after "|"
        parts = re.split(r"[\|,]", nums_text)
        db_num = None
        if len(parts) >= 2:
            db_candidates2 = [int(x) for x in re.findall(r"\d+", parts[-1]) if 1 <= int(x) <= 12]
            if db_candidates2:
                db_num = db_candidates2[-1]
        if db_num is None and db_candidates:
            db_num = db_candidates[-1]
        if db_num is None:
            return None

        return dict(
            ky=ky, ngay=str(ngay), buoi=buoi,
            s1=s1, s2=s2, s3=s3, s4=s4, s5=s5, db=db_num,
            tong=s1 + s2 + s3 + s4 + s5,
        )
    except (ValueError, IndexError):
        return None


def fetch_latest_vietlott(n: int = 1) -> list[dict]:
    """
    Crawl từ vietlott.vn.
    Trả về list dict kết quả (mới nhất trước), tối đa n kỳ.
    """
    try:
        res = SESSION.get(VIETLOTT_URL, timeout=TIMEOUT)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        results = []
        # Vietlott thường dùng table.table hoặc table trong .result-table
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows[1:]:  # skip header
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue
                parsed = _parse_row(cols)
                if parsed:
                    results.append(parsed)
                if len(results) >= n:
                    return results
        return results
    except Exception as e:
        print(f"[crawler] vietlott error: {e}")
        return []


def fetch_backup(n: int = 1) -> list[dict]:
    """Crawl từ ketquadientoan.com làm backup."""
    try:
        res = SESSION.get(BACKUP_URL, timeout=TIMEOUT)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        results = []
        # Thử tìm block kết quả theo nhiều selector phổ biến
        blocks = (
            soup.select(".result-block")
            or soup.select(".ky-result")
            or soup.select(".result-item")
        )

        for block in blocks[:n]:
            header_el = (
                block.select_one(".ky-header")
                or block.select_one("h3")
                or block.select_one("h4")
            )
            if not header_el:
                continue
            header = header_el.get_text(strip=True)

            ky_m   = re.search(r"#?(\d{3,})", header)
            date_m = re.search(r"(\d{2}/\d{2}/\d{4})", header)
            if not ky_m or not date_m:
                continue

            ky   = int(ky_m.group(1))
            ngay = datetime.strptime(date_m.group(1), "%d/%m/%Y").date()
            buoi = "S" if re.search(r"13[Hh]", header) else "T"

            # Lấy các số từ ball elements
            ball_els = (
                block.select(".ball")
                or block.select(".so-ball")
                or block.select("span.num")
            )
            nums = [int(el.get_text(strip=True))
                    for el in ball_els
                    if el.get_text(strip=True).isdigit()]

            if len(nums) < 6:
                continue

            s1, s2, s3, s4, s5 = sorted(nums[:5])
            db_num = nums[5]
            if not (1 <= db_num <= 12):
                continue

            results.append(dict(
                ky=ky, ngay=str(ngay), buoi=buoi,
                s1=s1, s2=s2, s3=s3, s4=s4, s5=s5, db=db_num,
                tong=s1 + s2 + s3 + s4 + s5,
            ))

        return results
    except Exception as e:
        print(f"[crawler] backup error: {e}")
        return []


def save_if_new(result: dict, db_path: str = DB_PATH) -> bool:
    """Lưu vào DB nếu kỳ chưa tồn tại. Trả về True nếu insert thành công."""
    if not result:
        return False

    # Basic validation
    required_keys = {"ky", "ngay", "buoi", "s1", "s2", "s3", "s4", "s5", "db", "tong"}
    if not required_keys.issubset(result.keys()):
        print(f"[db] Dữ liệu thiếu field: {required_keys - set(result.keys())}")
        return False

    con = get_conn(db_path)
    try:
        cur = con.execute("SELECT 1 FROM results WHERE ky=?", (result["ky"],))
        if cur.fetchone():
            print(f"[db] Kỳ {result['ky']} đã tồn tại, bỏ qua.")
            return False

        con.execute(
            """
            INSERT INTO results (ky,ngay,buoi,s1,s2,s3,s4,s5,db,tong)
            VALUES (:ky,:ngay,:buoi,:s1,:s2,:s3,:s4,:s5,:db,:tong)
            """,
            result,
        )
        con.commit()
        print(f"[db] Đã lưu kỳ #{result['ky']} — {result['ngay']} ({result['buoi']})")
        return True
    except sqlite3.IntegrityError as e:
        print(f"[db] IntegrityError kỳ {result['ky']}: {e}")
        return False
    finally:
        con.close()


def run_crawl(db_path: str = DB_PATH) -> tuple[bool, dict | None]:
    """
    Crawl kỳ mới nhất và lưu vào DB.
    Trả về (is_new, result).
    """
    results = fetch_latest_vietlott(n=1)
    if not results:
        print("[crawler] vietlott thất bại, thử backup...")
        results = fetch_backup(n=1)

    if not results:
        print("[crawler] Không lấy được dữ liệu từ cả hai nguồn.")
        return False, None

    result  = results[0]
    is_new  = save_if_new(result, db_path)
    return is_new, result


def run_crawl_bulk(n: int = 10, db_path: str = DB_PATH) -> int:
    """
    Crawl nhiều kỳ gần nhất, hữu ích khi bootstrap dữ liệu.
    Trả về số kỳ mới được lưu.
    """
    saved = 0
    results = fetch_latest_vietlott(n=n)
    if not results:
        results = fetch_backup(n=n)

    for r in results:
        if save_if_new(r, db_path):
            saved += 1
        time.sleep(0.3)  # gentle rate-limit

    print(f"[crawler] Đã lưu {saved}/{len(results)} kỳ mới.")
    return saved


if __name__ == "__main__":
    is_new, result = run_crawl()
    print(f"is_new={is_new}, result={result}")
