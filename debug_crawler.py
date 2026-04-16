"""
debug_crawler.py — Tải HTML từ vietlott.vn để inspect CSS selector.

Chạy:
    python debug_crawler.py
Sau đó mở debug.html và Ctrl+F tìm số kỳ mới nhất.
"""
import requests
from bs4 import BeautifulSoup

URL = "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/535.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

res  = requests.get(URL, headers=HEADERS, timeout=20)
soup = BeautifulSoup(res.text, "html.parser")

with open("debug.html", "w", encoding="utf-8") as f:
    f.write(soup.prettify())

print("Đã lưu debug.html — mở file và Ctrl+F tìm số kỳ mới nhất để tìm đúng CSS selector.")
print("HTTP status:", res.status_code)
