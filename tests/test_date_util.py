from datetime import date
from app.core.date_util import resolve_default_date, date_formats


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
