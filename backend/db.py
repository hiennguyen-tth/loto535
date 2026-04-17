"""
db.py — SQLite helper for LottoAI (Lotto 5/35, Mega 6/45, Power 6/55)
"""
import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "data/lotto535.db")

# ─── Lotto 5/35 ───────────────────────────────────────
DDL = """
CREATE TABLE IF NOT EXISTS results (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ky         INTEGER UNIQUE NOT NULL,
    ngay       DATE NOT NULL,
    buoi       TEXT NOT NULL CHECK(buoi IN ('S','T')),
    s1         INTEGER NOT NULL CHECK(s1 BETWEEN 1 AND 35),
    s2         INTEGER NOT NULL CHECK(s2 BETWEEN 1 AND 35),
    s3         INTEGER NOT NULL CHECK(s3 BETWEEN 1 AND 35),
    s4         INTEGER NOT NULL CHECK(s4 BETWEEN 1 AND 35),
    s5         INTEGER NOT NULL CHECK(s5 BETWEEN 1 AND 35),
    db         INTEGER NOT NULL CHECK(db BETWEEN 1 AND 12),
    tong       INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scoring_cache (
    so          INTEGER PRIMARY KEY CHECK(so BETWEEN 1 AND 35),
    freq_total  INTEGER,
    freq_30     INTEGER,
    gap         INTEGER,
    score       REAL,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scoring_db (
    db          INTEGER PRIMARY KEY CHECK(db BETWEEN 1 AND 12),
    freq_total  INTEGER,
    freq_30     INTEGER,
    gap         INTEGER,
    score       REAL,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_results_ky   ON results(ky  DESC);
CREATE INDEX IF NOT EXISTS idx_results_ngay ON results(ngay DESC);
"""

# ─── Mega 6/45 ────────────────────────────────────────
DDL_645 = """
CREATE TABLE IF NOT EXISTS results_645 (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ky         INTEGER UNIQUE NOT NULL,
    ngay       DATE NOT NULL,
    s1         INTEGER NOT NULL CHECK(s1 BETWEEN 1 AND 45),
    s2         INTEGER NOT NULL CHECK(s2 BETWEEN 1 AND 45),
    s3         INTEGER NOT NULL CHECK(s3 BETWEEN 1 AND 45),
    s4         INTEGER NOT NULL CHECK(s4 BETWEEN 1 AND 45),
    s5         INTEGER NOT NULL CHECK(s5 BETWEEN 1 AND 45),
    s6         INTEGER NOT NULL CHECK(s6 BETWEEN 1 AND 45),
    tong       INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scoring_645 (
    so          INTEGER PRIMARY KEY CHECK(so BETWEEN 1 AND 45),
    freq_total  INTEGER,
    freq_30     INTEGER,
    gap         INTEGER,
    score       REAL,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_results_645_ky   ON results_645(ky   DESC);
CREATE INDEX IF NOT EXISTS idx_results_645_ngay ON results_645(ngay DESC);
"""

# ─── Power 6/55 ───────────────────────────────────────
DDL_655 = """
CREATE TABLE IF NOT EXISTS results_655 (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ky         INTEGER UNIQUE NOT NULL,
    ngay       DATE NOT NULL,
    s1         INTEGER NOT NULL CHECK(s1 BETWEEN 1 AND 55),
    s2         INTEGER NOT NULL CHECK(s2 BETWEEN 1 AND 55),
    s3         INTEGER NOT NULL CHECK(s3 BETWEEN 1 AND 55),
    s4         INTEGER NOT NULL CHECK(s4 BETWEEN 1 AND 55),
    s5         INTEGER NOT NULL CHECK(s5 BETWEEN 1 AND 55),
    s6         INTEGER NOT NULL CHECK(s6 BETWEEN 1 AND 55),
    power      INTEGER NOT NULL CHECK(power BETWEEN 1 AND 55),
    tong       INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scoring_655 (
    so          INTEGER PRIMARY KEY CHECK(so BETWEEN 1 AND 55),
    freq_total  INTEGER,
    freq_30     INTEGER,
    gap         INTEGER,
    score       REAL,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scoring_655_power (
    so          INTEGER PRIMARY KEY CHECK(so BETWEEN 1 AND 55),
    freq_total  INTEGER,
    freq_30     INTEGER,
    gap         INTEGER,
    score       REAL,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_results_655_ky   ON results_655(ky   DESC);
CREATE INDEX IF NOT EXISTS idx_results_655_ngay ON results_655(ngay DESC);
"""


def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def init_db(db_path: str = DB_PATH) -> None:
    con = get_conn(db_path)
    con.executescript(DDL)
    con.executescript(DDL_645)
    con.executescript(DDL_655)
    con.commit()
    con.close()
    print(f"[db] Initialized: {db_path}")


def query(sql: str, params=(), db_path: str = DB_PATH) -> list[dict]:
    con = get_conn(db_path)
    cur = con.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def execute(sql: str, params=(), db_path: str = DB_PATH) -> int:
    """Execute a write statement, return rowcount."""
    con = get_conn(db_path)
    cur = con.execute(sql, params)
    con.commit()
    affected = cur.rowcount
    con.close()
    return affected


if __name__ == "__main__":
    init_db()
