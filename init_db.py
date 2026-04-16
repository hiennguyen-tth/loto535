"""
init_db.py — Khởi tạo SQLite database.

Chạy:
    python init_db.py
"""
import sys
import os

# Ensure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from db import init_db

if __name__ == "__main__":
    init_db()
    print("Done.")
