from datetime import date
from app.core.date_util import resolve_default_date, date_formats, resolve_target_date


def test_resolve_target_date_modes():
    today = date(2026, 7, 3)
    assert resolve_target_date("today", "", today) == date(2026, 7, 3)
    assert resolve_target_date("tomorrow", "", today) == date(2026, 7, 4)
    assert resolve_target_date("fixed", "2026-08-15", today) == date(2026, 8, 15)
    # fixed인데 값이 이상하면 내일
    assert resolve_target_date("fixed", "bad", today) == date(2026, 7, 4)
    # 알 수 없는 모드 → 내일
    assert resolve_target_date("", "", today) == date(2026, 7, 4)


def test_resolve_default_date_offsets():
    base = date(2026, 3, 1)
    assert resolve_default_date(base, 0) == date(2026, 3, 1)
    assert resolve_default_date(base, 1) == date(2026, 3, 2)
    assert resolve_default_date(base, -1) == date(2026, 2, 28)


def test_date_formats():
    f = date_formats(date(2025, 3, 1))
    assert f["ymd"] == "2025-03-01"
    assert f["yymmdd"] == "250301"
    assert f["yy_mm_dd"] == "'25-03-01"
