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

VIETLOTT_URL         = "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/535"
VIETLOTT_HISTORY_URL = "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/winning-number-535"
VIETLOTT_DETAIL_URL  = "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/535?id={ky}&nocatche=1"
BACKUP_URL      = "https://www.ketquadientoan.com/ket-qua-xo-so-dien-toan-lotto-535.html"
BACKUP_DATE_URL = "https://www.ketquadientoan.com/ket-qua-xo-so-dien-toan-lotto-535/{date}.html"

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


def _buoi_from_ky(ky: int) -> str:
    """Xác định buổi từ số kỳ: chẵn = Tối (21H), lẻ = Sáng (13H)."""
    return "T" if ky % 2 == 0 else "S"


def _parse_history_row(row) -> dict | None:
    """
    Parse một hàng <tr> trong bảng lịch sử vietlott (winning-number-535).
    Cột bố cục: Ngày | Kỳ | Bộ số (5 balls + separator + 1 DB ball)
    """
    try:
        tds = row.find_all("td")
        if len(tds) < 3:
            return None

        date_text = tds[0].get_text(strip=True)
        ky_text   = tds[1].get_text(strip=True)
        balls_td  = tds[2]

        date_m = re.search(r"(\d{2}/\d{2}/\d{4})", date_text)
        if not date_m:
            return None
        ngay = datetime.strptime(date_m.group(1), "%d/%m/%Y").date()

        ky_m = re.search(r"\d+", ky_text)
        if not ky_m:
            return None
        ky = int(ky_m.group())
        buoi = _buoi_from_ky(ky)

        # All spans with class bong_tron — the last one is DB (has no-margin-right)
        all_balls = balls_td.find_all("span", class_="bong_tron")
        db_balls  = balls_td.find_all("span", class_=lambda c: c and "no-margin-right" in c)

        nums = []
        for b in all_balls:
            classes = b.get("class", [])
            if "no-margin-right" not in classes and "bong_tron-sperator" not in classes:
                txt = b.get_text(strip=True)
                if txt.isdigit() and 1 <= int(txt) <= 35:
                    nums.append(int(txt))

        db_num = None
        for b in db_balls:
            txt = b.get_text(strip=True)
            if txt.isdigit() and 1 <= int(txt) <= 12:
                db_num = int(txt)
                break

        if len(nums) < 5 or db_num is None:
            return None

        s1, s2, s3, s4, s5 = sorted(nums[:5])
        return dict(
            ky=ky, ngay=str(ngay), buoi=buoi,
            s1=s1, s2=s2, s3=s3, s4=s4, s5=s5, db=db_num,
            tong=s1 + s2 + s3 + s4 + s5,
        )
    except (ValueError, IndexError):
        return None


def fetch_latest_vietlott(n: int = 1) -> list[dict]:
    """
    Crawl kỳ mới nhất từ trang chi tiết vietlott.vn/535.
    Trả về list chứa tối đa 1 kết quả (kỳ mới nhất).
    Với n > 1, chuyển sang fetch_history_vietlott.
    """
    if n > 1:
        return fetch_history_vietlott(n)
    try:
        res = SESSION.get(VIETLOTT_URL, timeout=TIMEOUT)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # Lấy kỳ và ngày từ .chitietketqua_title
        title_el = soup.find(class_="chitietketqua_title")
        if not title_el:
            return []
        title_text = title_el.get_text(" ", strip=True)

        ky_m   = re.search(r"#(\d+)", title_text)
        date_m = re.search(r"(\d{2}/\d{2}/\d{4})", title_text)
        if not ky_m or not date_m:
            return []

        ky   = int(ky_m.group(1))
        ngay = datetime.strptime(date_m.group(1), "%d/%m/%Y").date()
        buoi = _buoi_from_ky(ky)

        # 5 số chính: .bong_tron.small không có class 'active'
        # Số đặc biệt DB: .bong_tron.small.active (hoặc no-margin-right + active)
        all_balls = soup.find_all("span", class_="bong_tron")
        main_nums = []
        db_num    = None

        for b in all_balls:
            classes = b.get("class", [])
            txt = b.get_text(strip=True)
            if not txt.isdigit():
                continue
            val = int(txt)
            if "active" in classes or "no-margin-right" in classes:
                if 1 <= val <= 12:
                    db_num = val
            elif 1 <= val <= 35:
                main_nums.append(val)

        if len(main_nums) < 5 or db_num is None:
            return []

        s1, s2, s3, s4, s5 = sorted(main_nums[:5])
        return [dict(
            ky=ky, ngay=str(ngay), buoi=buoi,
            s1=s1, s2=s2, s3=s3, s4=s4, s5=s5, db=db_num,
            tong=s1 + s2 + s3 + s4 + s5,
        )]
    except Exception as e:
        print(f"[crawler] vietlott detail error: {e}")
        return []


def fetch_history_vietlott(n: int = 20) -> list[dict]:
    """
    Crawl lịch sử từ trang winning-number-535 của vietlott.vn.
    Trả về list kết quả (mới nhất trước), tối đa n kỳ.
    Trang này hiển thị khoảng 8 kỳ gần nhất.
    """
    try:
        res = SESSION.get(VIETLOTT_HISTORY_URL, timeout=TIMEOUT)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        results = []
        table = soup.find("table")
        if not table:
            return []

        rows = table.find_all("tr")
        for row in rows[1:]:  # skip header
            parsed = _parse_history_row(row)
            if parsed:
                results.append(parsed)
            if len(results) >= n:
                break

        return results
    except Exception as e:
        print(f"[crawler] vietlott history error: {e}")
        return []


def fetch_backup(n: int = 1) -> list[dict]:
    """
    Crawl từ ketquadientoan.com.
    Dùng selector: .box_kqxsdt .title_tt (header) + .box_ketqua .ball_lotto (numbers).
    """
    try:
        res = SESSION.get(BACKUP_URL, timeout=TIMEOUT)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        return _parse_ketquadientoan(soup, n)
    except Exception as e:
        print(f"[crawler] backup error: {e}")
        return []


def _parse_ketquadientoan(soup, n: int) -> list[dict]:
    """Parse HTML từ ketquadientoan.com."""
    results = []
    blocks = soup.select(".box_kqxsdt")
    for block in blocks:
        title_el = block.select_one(".title_tt")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        # "Kỳ vé #00583 | Thứ năm, 16/04/2026 - 13H"
        ky_m   = re.search(r"#(\d+)", title)
        date_m = re.search(r"(\d{2}/\d{2}/\d{4})", title)
        if not ky_m or not date_m:
            continue
        ky   = int(ky_m.group(1))
        ngay = datetime.strptime(date_m.group(1), "%d/%m/%Y").date()
        buoi = "S" if re.search(r"13H", title, re.IGNORECASE) else "T"

        # Main balls: .ball_lotto but NOT .ball_power2
        ketqua_el = block.select_one(".box_ketqua")
        if not ketqua_el:
            continue
        all_balls = ketqua_el.select(".ball_lotto")
        db_balls  = ketqua_el.select(".ball_power2")

        main_nums = []
        for b in all_balls:
            if "ball_power2" not in b.get("class", []):
                txt = b.get_text(strip=True)
                if txt.isdigit():
                    main_nums.append(int(txt))

        db_num = None
        for b in db_balls:
            txt = b.get_text(strip=True)
            if txt.isdigit():
                db_num = int(txt)
                break

        if len(main_nums) < 5 or db_num is None:
            continue

        s1, s2, s3, s4, s5 = sorted(main_nums[:5])
        results.append(dict(
            ky=ky, ngay=str(ngay), buoi=buoi,
            s1=s1, s2=s2, s3=s3, s4=s4, s5=s5, db=db_num,
            tong=s1 + s2 + s3 + s4 + s5,
        ))
        if len(results) >= n:
            break

    return results


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
    Crawl nhiều kỳ gần nhất từ vietlott.vn (history page) + backup ketquadientoan.com.
    Trả về số kỳ mới được lưu.
    """
    from datetime import date, timedelta

    saved = 0

    # Thử vietlott history page trước (cho tối đa ~8 kỳ)
    results = fetch_history_vietlott(n=n)

    # Nếu không đủ, crawl backup
    if len(results) < n:
        try:
            # Trang chính cho ngày hôm nay
            res = SESSION.get(BACKUP_URL, timeout=TIMEOUT)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            day_results = _parse_ketquadientoan(soup, n)
            seen_kys = {r["ky"] for r in results}
            for r in day_results:
                if r["ky"] not in seen_kys:
                    results.append(r)
                    seen_kys.add(r["ky"])

            # Crawl thêm các trang ngày trước đó nếu chưa đủ
            current = date.today()
            while len(results) < n:
                current -= timedelta(days=1)
                date_str = current.strftime("%d-%m-%Y")
                url = BACKUP_DATE_URL.format(date=date_str)
                try:
                    r2 = SESSION.get(url, timeout=TIMEOUT)
                    if r2.status_code == 404:
                        # Try going back more
                        continue
                    r2.raise_for_status()
                    soup2 = BeautifulSoup(r2.text, "html.parser")
                    day_r = _parse_ketquadientoan(soup2, 5)
                    for r in day_r:
                        if r["ky"] not in seen_kys:
                            results.append(r)
                            seen_kys.add(r["ky"])
                    # Stop if we've gone back 30 days
                    if (date.today() - current).days > 30:
                        break
                except Exception:
                    break
                time.sleep(0.5)
        except Exception as e:
            print(f"[crawler] bulk backup error: {e}")

    for r in results[:n]:
        if save_if_new(r, db_path):
            saved += 1
        time.sleep(0.2)

    print(f"[crawler] Đã lưu {saved}/{min(len(results), n)} kỳ mới.")
    return saved


if __name__ == "__main__":
    is_new, result = run_crawl()
    print(f"is_new={is_new}, result={result}")
