"""
seed_sample.py — Seed 20 kỳ mẫu để test dashboard mà không cần crawl thật.

Chạy:
    python seed_sample.py
"""
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from db import init_db, get_conn, DB_PATH
from engine import recalculate_scores

SAMPLE_DATA = [
    # (ky, ngay, buoi, s1,s2,s3,s4,s5, db)
    (581, "2026-04-15", "S",  1, 15, 20, 32, 35,  8),
    (580, "2026-04-14", "T",  3,  7, 18, 24, 30, 12),
    (579, "2026-04-14", "S",  5, 11, 16, 28, 33,  4),
    (578, "2026-04-13", "T",  2,  9, 14, 22, 31,  7),
    (577, "2026-04-13", "S",  6, 13, 19, 27, 34,  3),
    (576, "2026-04-12", "T",  4, 10, 17, 25, 29,  9),
    (575, "2026-04-12", "S",  8, 12, 21, 26, 35,  2),
    (574, "2026-04-11", "T",  1,  6, 15, 23, 32, 11),
    (573, "2026-04-11", "S",  3,  9, 18, 30, 34,  5),
    (572, "2026-04-10", "T",  7, 14, 20, 28, 33,  1),
    (571, "2026-04-10", "S",  2, 11, 16, 24, 31,  6),
    (570, "2026-04-09", "T",  5, 13, 19, 27, 35, 10),
    (569, "2026-04-09", "S",  4,  8, 17, 22, 29,  8),
    (568, "2026-04-08", "T",  6, 10, 21, 25, 32, 12),
    (567, "2026-04-08", "S",  1,  7, 15, 26, 30,  4),
    (566, "2026-04-07", "T",  3, 12, 18, 28, 34,  9),
    (565, "2026-04-07", "S",  9, 14, 20, 31, 33,  2),
    (564, "2026-04-06", "T",  2,  8, 16, 24, 35,  7),
    (563, "2026-04-06", "S",  5, 11, 19, 27, 32,  3),
    (562, "2026-04-05", "T",  4,  6, 17, 23, 30, 11),
]


def seed():
    init_db()
    con = get_conn()
    saved = 0
    for row in SAMPLE_DATA:
        ky, ngay, buoi, s1, s2, s3, s4, s5, db = row
        try:
            con.execute(
                "INSERT OR IGNORE INTO results (ky,ngay,buoi,s1,s2,s3,s4,s5,db,tong) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (ky, ngay, buoi, s1, s2, s3, s4, s5, db, s1+s2+s3+s4+s5),
            )
            if con.execute("SELECT changes()").fetchone()[0]:
                saved += 1
        except Exception as e:
            print(f"  Skip {ky}: {e}")
    con.commit()
    con.close()
    print(f"Seeded {saved} rows.")
    recalculate_scores()
    print("Scores recalculated.")


if __name__ == "__main__":
    seed()
