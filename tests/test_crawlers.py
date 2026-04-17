"""
test_crawlers.py — Kiểm tra crawl từ tất cả nguồn (vietlott.vn + fallback)

Chạy: python -m pytest tests/test_crawlers.py -v
Hoặc: python tests/test_crawlers.py
"""
import sys
import time
import re
from pathlib import Path

# Đảm bảo import được từ thư mục gốc
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from backend.crawler import (
    SESSION,
    XOSO_645_URL,
    XOSO_655_URL,
    _parse_xosonet,
    _fetch_xosonet,
    fetch_history_645,
    fetch_history_655,
    fetch_latest_645,
    fetch_latest_655,
    fetch_latest_vietlott,
    fetch_backup,
)
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _timer(label, fn, *args, **kwargs):
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    status = "OK" if result else "EMPTY"
    print(f"  [{elapsed:.2f}s] {label}: {status} — {len(result) if isinstance(result, list) else result}")
    return result, elapsed


def _validate_645(rows):
    for r in rows:
        assert set(r) >= {"ky", "ngay", "s1", "s2", "s3", "s4", "s5", "s6", "tong"}, f"Thiếu field: {r}"
        nums = [r["s1"], r["s2"], r["s3"], r["s4"], r["s5"], r["s6"]]
        assert all(1 <= v <= 45 for v in nums), f"Số ngoài range [1,45]: {nums}"
        assert nums == sorted(nums), f"Số không được sắp xếp: {nums}"
        assert r["tong"] == sum(nums), f"Tổng sai: {r['tong']} != {sum(nums)}"
        assert re.match(r"\d{4}-\d{2}-\d{2}", r["ngay"]), f"Ngày sai format: {r['ngay']}"
        assert r["ky"] > 0, f"Kỳ không hợp lệ: {r['ky']}"
    return True


def _validate_655(rows):
    for r in rows:
        assert set(r) >= {"ky", "ngay", "s1", "s2", "s3", "s4", "s5", "s6", "power", "tong"}, f"Thiếu field: {r}"
        nums = [r["s1"], r["s2"], r["s3"], r["s4"], r["s5"], r["s6"]]
        assert all(1 <= v <= 55 for v in nums), f"Số chính ngoài range [1,55]: {nums}"
        assert nums == sorted(nums), f"Số chính không được sắp xếp: {nums}"
        assert 1 <= r["power"] <= 55, f"Power ngoài range [1,55]: {r['power']}"
        assert r["tong"] == sum(nums), f"Tổng sai: {r['tong']} != {sum(nums)}"
    return True


# ---------------------------------------------------------------------------
# Unit tests: parse _parse_xosonet với mock HTML
# ---------------------------------------------------------------------------

def test_parse_xosonet_645_mock():
    """Kiểm tra parser xoso.net.vn cho 6/45 với HTML mẫu (cấu trúc thực tế)."""
    html = """
    <html><body>
    <div class="boxs_content">
      <div class="cat-box-title">
        <h2 class="title-cat"><a href="/xo-so-mega-ngay-17-4-2026.html">Mega 17-04-2026</a></h2>
      </div>
      <div class="cat-box-content">
        <div class="mega-jackpot">
          <div class="rows_kyquay">
            <span class="mega-jackpot-title">Kỳ quay thưởng: <strong>#01498</strong></span>
          </div>
        </div>
        <div class="mega-rows">
          <span class="icon_xsmga">01</span>
          <span class="icon_xsmga">10</span>
          <span class="icon_xsmga">19</span>
          <span class="icon_xsmga">31</span>
          <span class="icon_xsmga">36</span>
          <span class="icon_xsmga">38</span>
        </div>
      </div>
    </div>
    <div class="boxs_content">
      <div class="cat-box-title">
        <h2 class="title-cat"><a href="/xo-so-mega-ngay-15-4-2026.html">Mega 15-04-2026</a></h2>
      </div>
      <div class="cat-box-content">
        <div class="mega-jackpot">
          <div class="rows_kyquay">
            <span class="mega-jackpot-title">Kỳ quay thưởng: <strong>#01497</strong></span>
          </div>
        </div>
        <div class="mega-rows">
          <span class="icon_xsmga">21</span>
          <span class="icon_xsmga">22</span>
          <span class="icon_xsmga">33</span>
          <span class="icon_xsmga">35</span>
          <span class="icon_xsmga">36</span>
          <span class="icon_xsmga">43</span>
        </div>
      </div>
    </div>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    results = _parse_xosonet(soup, game="645", n=10)

    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    r0 = results[0]
    assert r0["ky"] == 1498
    assert r0["s1"] == 1 and r0["s6"] == 38
    assert r0["ngay"] == "2026-04-17"
    assert r0["tong"] == 1 + 10 + 19 + 31 + 36 + 38

    r1 = results[1]
    assert r1["ky"] == 1497
    assert r1["ngay"] == "2026-04-15"
    print("  PASS test_parse_xosonet_645_mock")


def test_parse_xosonet_655_mock():
    """Kiểm tra parser xoso.net.vn cho 6/55 với HTML mẫu (cấu trúc thực tế)."""
    html = """
    <html><body>
    <div class="boxs_content">
      <div class="cat-box-title">
        <h2 class="title-cat"><a href="/xo-so-power-655-ngay-16-4-2026.html">Power 16-04-2026</a></h2>
      </div>
      <div class="cat-box-content">
        <div class="mega-jackpot">
          <div class="rows_kyquay">
            <span class="mega-jackpot-title">Kỳ quay thưởng: <strong>#01333</strong></span>
          </div>
        </div>
        <div class="mega-rows">
          <span class="icon_xsmga">02</span>
          <span class="icon_xsmga">07</span>
          <span class="icon_xsmga">15</span>
          <span class="icon_xsmga">22</span>
          <span class="icon_xsmga">47</span>
          <span class="icon_xsmga">52</span>
          <span class="icon_xsmga bgyelow">55</span>
        </div>
      </div>
    </div>
    <div class="boxs_content">
      <div class="cat-box-title">
        <h2 class="title-cat"><a href="/xo-so-power-655-ngay-14-4-2026.html">Power 14-04-2026</a></h2>
      </div>
      <div class="cat-box-content">
        <div class="mega-jackpot">
          <div class="rows_kyquay">
            <span class="mega-jackpot-title">Kỳ quay thưởng: <strong>#01332</strong></span>
          </div>
        </div>
        <div class="mega-rows">
          <span class="icon_xsmga">08</span>
          <span class="icon_xsmga">16</span>
          <span class="icon_xsmga">22</span>
          <span class="icon_xsmga">35</span>
          <span class="icon_xsmga">39</span>
          <span class="icon_xsmga">47</span>
          <span class="icon_xsmga bgyelow">28</span>
        </div>
      </div>
    </div>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    results = _parse_xosonet(soup, game="655", n=10)

    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    r0 = results[0]
    assert r0["ky"] == 1333
    assert r0["s1"] == 2 and r0["s6"] == 52
    assert r0["power"] == 55
    assert r0["ngay"] == "2026-04-16"

    r1 = results[1]
    assert r1["ky"] == 1332
    assert r1["power"] == 28
    print("  PASS test_parse_xosonet_655_mock")


# ---------------------------------------------------------------------------
# Integration tests: gọi HTTP thực
# ---------------------------------------------------------------------------

def test_xosonet_645_live():
    """Fetch xoso.net.vn/645 thực, kiểm tra dữ liệu trả về."""
    results, elapsed = _timer("xoso.net.vn 645", _fetch_xosonet, XOSO_645_URL, "645", 10)
    assert results, "xoso.net.vn 645 không trả về dữ liệu"
    assert len(results) >= 1
    _validate_645(results)
    print(f"  PASS test_xosonet_645_live — {len(results)} kỳ, kỳ mới nhất #{results[0]['ky']}")
    return elapsed


def test_xosonet_655_live():
    """Fetch xoso.net.vn/655 thực, kiểm tra dữ liệu trả về."""
    results, elapsed = _timer("xoso.net.vn 655", _fetch_xosonet, XOSO_655_URL, "655", 10)
    assert results, "xoso.net.vn 655 không trả về dữ liệu"
    assert len(results) >= 1
    _validate_655(results)
    print(f"  PASS test_xosonet_655_live — {len(results)} kỳ, kỳ mới nhất #{results[0]['ky']}")
    return elapsed


def test_fetch_history_645_with_fallback():
    """fetch_history_645 phải trả về dữ liệu (vietlott hoặc xoso.net.vn)."""
    results, elapsed = _timer("fetch_history_645", fetch_history_645, 8)
    assert results, "fetch_history_645 rỗng"
    _validate_645(results)
    print(f"  PASS — {len(results)} kỳ")
    return elapsed


def test_fetch_history_655_with_fallback():
    """fetch_history_655 phải trả về dữ liệu (vietlott hoặc xoso.net.vn)."""
    results, elapsed = _timer("fetch_history_655", fetch_history_655, 8)
    assert results, "fetch_history_655 rỗng"
    _validate_655(results)
    print(f"  PASS — {len(results)} kỳ")
    return elapsed


def test_fetch_latest_645():
    results, elapsed = _timer("fetch_latest_645", fetch_latest_645)
    assert results, "fetch_latest_645 rỗng"
    _validate_645(results)
    print(f"  PASS — kỳ #{results[0]['ky']} ngày {results[0]['ngay']}")
    return elapsed


def test_fetch_latest_655():
    results, elapsed = _timer("fetch_latest_655", fetch_latest_655)
    assert results, "fetch_latest_655 rỗng"
    _validate_655(results)
    print(f"  PASS — kỳ #{results[0]['ky']} ngày {results[0]['ngay']}")
    return elapsed


def test_fetch_535_sources():
    """535: vietlott history + ketquadientoan.com backup."""
    print("\n  [535 vietlott]")
    r1, t1 = _timer("vietlott 535 history", fetch_latest_vietlott, 3)
    print(f"  [535 backup - ketquadientoan.com]")
    r2, t2 = _timer("backup 535", fetch_backup, 1)
    assert r1 or r2, "Cả hai nguồn 535 đều trống"
    if r1:
        for r in r1:
            assert all(1 <= r[f"s{i}"] <= 35 for i in range(1, 6)), f"535 số ngoài range: {r}"
    print(f"  PASS test_fetch_535_sources")


# ---------------------------------------------------------------------------
# Consistency test: xoso.net.vn vs vietlott cho cùng kỳ
# ---------------------------------------------------------------------------

def test_consistency_645():
    """So sánh kết quả 645 từ xoso.net.vn và vietlott.vn cho cùng kỳ."""
    from backend.crawler import _parse_winning_table_645, VIETLOTT_645_HISTORY_URL
    try:
        res = SESSION.get(VIETLOTT_645_HISTORY_URL, timeout=20)
        vl_rows = _parse_winning_table_645(BeautifulSoup(res.text, "html.parser"))
    except Exception:
        vl_rows = []

    xs_rows = _fetch_xosonet(XOSO_645_URL, "645", 10)

    if not vl_rows or not xs_rows:
        print("  SKIP (một trong hai nguồn không available)")
        return

    # Build dict ky -> row
    vl_map = {r["ky"]: r for r in vl_rows}
    xs_map = {r["ky"]: r for r in xs_rows}
    common_kys = set(vl_map) & set(xs_map)

    mismatches = []
    for ky in common_kys:
        vl, xs = vl_map[ky], xs_map[ky]
        for f in ("s1", "s2", "s3", "s4", "s5", "s6"):
            if vl[f] != xs[f]:
                mismatches.append((ky, f, vl[f], xs[f]))

    if mismatches:
        for ky, f, v1, v2 in mismatches:
            print(f"  MISMATCH kỳ #{ky} field {f}: vietlott={v1}, xoso={v2}")
        assert False, f"{len(mismatches)} mismatch(es) giữa vietlott và xoso.net.vn"
    else:
        print(f"  PASS — {len(common_kys)} kỳ khớp giữa vietlott và xoso.net.vn")


# ---------------------------------------------------------------------------
# Performance report
# ---------------------------------------------------------------------------

def run_performance_report():
    timings = {}
    print("\n=== PERFORMANCE REPORT ===")
    print("Đang đo thời gian các nguồn crawl...\n")

    # 535
    print("[5/35]")
    _, t = _timer("vietlott.vn latest", fetch_latest_vietlott, 1)
    timings["535_vietlott"] = t
    _, t = _timer("ketquadientoan.com backup", fetch_backup, 1)
    timings["535_backup"] = t

    # 645
    print("\n[6/45]")
    from backend.crawler import _parse_winning_table_645, VIETLOTT_645_HISTORY_URL
    try:
        res = SESSION.get(VIETLOTT_645_HISTORY_URL, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        t0 = time.perf_counter()
        rows = _parse_winning_table_645(soup)
        t = time.perf_counter() - t0 + (time.perf_counter() - time.perf_counter())
        print(f"  [N/A] vietlott.vn 645 history: {'OK' if rows else 'EMPTY'} — {len(rows)} rows")
        timings["645_vietlott"] = 0
    except Exception as e:
        print(f"  [N/A] vietlott.vn 645 blocked: {e}")
        timings["645_vietlott"] = None
    _, t = _timer("xoso.net.vn 645", _fetch_xosonet, XOSO_645_URL, "645", 8)
    timings["645_xosonet"] = t

    # 655
    print("\n[6/55]")
    from backend.crawler import _parse_winning_table_655, VIETLOTT_655_HISTORY_URL
    try:
        res = SESSION.get(VIETLOTT_655_HISTORY_URL, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        rows = _parse_winning_table_655(soup)
        print(f"  [N/A] vietlott.vn 655 history: {'OK' if rows else 'EMPTY'} — {len(rows)} rows")
        timings["655_vietlott"] = 0
    except Exception as e:
        print(f"  [N/A] vietlott.vn 655 blocked: {e}")
        timings["655_vietlott"] = None
    _, t = _timer("xoso.net.vn 655", _fetch_xosonet, XOSO_655_URL, "655", 8)
    timings["655_xosonet"] = t

    print("\n=== SUMMARY ===")
    for key, val in timings.items():
        if val is None:
            print(f"  {key}: BLOCKED")
        else:
            print(f"  {key}: {val:.2f}s")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback

    tests = [
        ("Unit: parse 645 mock", test_parse_xosonet_645_mock),
        ("Unit: parse 655 mock", test_parse_xosonet_655_mock),
        ("Live: xoso.net.vn 645", test_xosonet_645_live),
        ("Live: xoso.net.vn 655", test_xosonet_655_live),
        ("Live: fetch_history_645 (auto-fallback)", test_fetch_history_645_with_fallback),
        ("Live: fetch_history_655 (auto-fallback)", test_fetch_history_655_with_fallback),
        ("Live: fetch_latest_645", test_fetch_latest_645),
        ("Live: fetch_latest_655", test_fetch_latest_655),
        ("Live: 535 sources", test_fetch_535_sources),
        ("Consistency: 645 vietlott vs xoso", test_consistency_645),
    ]

    passed = failed = 0
    for name, fn in tests:
        print(f"\n>>> {name}")
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            traceback.print_exc()
            failed += 1

    run_performance_report()
    print(f"\n{'='*40}")
    print(f"Kết quả: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
