"""
import_excel.py — Import lịch sử từ file Excel vào SQLite.

Dùng:
    python import_excel.py path/to/file.xlsx

Cột mong đợi trong sheet DATA: Kỳ, Buổi, Ngày, S1, S2, S3, S4, S5, DB
"""
import sys
import os
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

try:
    import pandas as pd
except ImportError:
    print("Cần cài pandas: pip install pandas openpyxl")
    sys.exit(1)

from db import init_db, get_conn, DB_PATH


def import_excel(xlsx_path: str, sheet: str = "DATA", db_path: str = DB_PATH) -> int:
    init_db(db_path)

    df = pd.read_excel(xlsx_path, sheet_name=sheet)
    df = df.rename(columns=str.strip)

    # Normalize column names (case-insensitive)
    col_map = {c.lower(): c for c in df.columns}
    needed  = {"kỳ": "ky", "buổi": "buoi", "ngày": "ngay",
                "s1": "s1", "s2": "s2", "s3": "s3", "s4": "s4", "s5": "s5", "db": "db"}

    rename = {}
    for vi_key, py_key in needed.items():
        matched = next((c for c in df.columns if c.lower().strip() == vi_key), None)
        if matched:
            rename[matched] = py_key

    df = df.rename(columns=rename)

    required_cols = {"ky", "buoi", "ngay", "s1", "s2", "s3", "s4", "s5", "db"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"Thiếu cột: {missing}. Các cột hiện có: {list(df.columns)}")
        sys.exit(1)

    df = df.dropna(subset=["s1"])
    saved = 0
    con = get_conn(db_path)

    for _, row in df.iterrows():
        try:
            s_nums = sorted([int(row.s1), int(row.s2), int(row.s3),
                             int(row.s4), int(row.s5)])
            s1, s2, s3, s4, s5 = s_nums
            db_num = int(row.db)
            ky     = int(row.ky)
            ngay   = str(row.ngay)[:10]
            buoi   = str(row.buoi).strip().upper()
            if buoi not in ("S", "T"):
                buoi = "S" if "13" in str(row.buoi) else "T"

            con.execute(
                """
                INSERT OR IGNORE INTO results (ky,ngay,buoi,s1,s2,s3,s4,s5,db,tong)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (ky, ngay, buoi, s1, s2, s3, s4, s5, db_num, s1+s2+s3+s4+s5),
            )
            if con.execute("SELECT changes()").fetchone()[0]:
                saved += 1
        except Exception as e:
            print(f"  Skip dòng {_}: {e}")

    con.commit()
    con.close()
    print(f"Import xong! Đã lưu {saved} kỳ mới vào {db_path}")
    return saved


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_excel.py path/to/file.xlsx [sheet_name]")
        sys.exit(1)

    xlsx  = sys.argv[1]
    sheet = sys.argv[2] if len(sys.argv) > 2 else "DATA"
    import_excel(xlsx, sheet)
