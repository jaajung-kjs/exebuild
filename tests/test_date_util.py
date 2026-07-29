from datetime import date
from app.core.date_util import (
    resolve_default_date,
    date_formats,
    resolve_target_date,
    next_business_day,
)


# 가짜 공휴일 집합 — 라이브러리에 의존하지 않는 결정론적 테스트용
def _fake_holiday(holidays):
    hset = set(holidays)
    return lambda d: d in hset


def test_next_business_day_already_business_day():
    # 2026-07-29 = 수요일, 비공휴일 → 그대로
    d = date(2026, 7, 29)
    assert next_business_day(d, is_holiday=_fake_holiday([])) == d


def test_next_business_day_skips_weekend():
    # 2026-07-25 = 토요일 → 월요일 2026-07-27
    assert next_business_day(date(2026, 7, 25), is_holiday=_fake_holiday([])) == date(2026, 7, 27)
    # 2026-07-26 = 일요일 → 월요일
    assert next_business_day(date(2026, 7, 26), is_holiday=_fake_holiday([])) == date(2026, 7, 27)


def test_next_business_day_skips_weekend_and_holiday():
    # 토(7/25) 시작 + 월(7/27)이 공휴일 → 화요일 7/28
    is_hol = _fake_holiday([date(2026, 7, 27)])
    assert next_business_day(date(2026, 7, 25), is_holiday=is_hol) == date(2026, 7, 28)


def test_next_business_day_skips_consecutive_holidays():
    # 화(7/28)부터 목(7/30)까지 연속 공휴일 → 금요일 7/31
    is_hol = _fake_holiday([date(2026, 7, 28), date(2026, 7, 29), date(2026, 7, 30)])
    # 시작 7/28(화, 공휴일)
    assert next_business_day(date(2026, 7, 28), is_holiday=is_hol) == date(2026, 7, 31)


def test_resolve_target_date_tomorrow_bizday_weekday():
    # 2026-07-29(수) → 내일 7/30(목, 평일) 그대로
    today = date(2026, 7, 29)
    assert resolve_target_date(
        "tomorrow_bizday", "", today, is_holiday=_fake_holiday([])
    ) == date(2026, 7, 30)


def test_resolve_target_date_tomorrow_bizday_over_weekend():
    # 2026-07-24(금) → 내일 7/25(토) → 월요일 7/27
    today = date(2026, 7, 24)
    assert resolve_target_date(
        "tomorrow_bizday", "", today, is_holiday=_fake_holiday([])
    ) == date(2026, 7, 27)


def test_is_holiday_real_library_substitute_holiday():
    # 라이브러리 계약 스모크: 2026 삼일절(3/1 일)의 대체공휴일 3/2(월)를 공휴일로 인식
    from app.core.date_util import is_holiday
    assert is_holiday(date(2026, 3, 1)) is True       # 삼일절
    assert is_holiday(date(2026, 3, 2)) is True        # 대체공휴일
    assert is_holiday(date(2026, 7, 29)) is False      # 평범한 수요일


def test_resolve_target_date_tomorrow_bizday_over_holiday():
    # 금(7/24) → 내일 토(7/25) → 월(7/27)이 공휴일 → 화(7/28)
    today = date(2026, 7, 24)
    assert resolve_target_date(
        "tomorrow_bizday", "", today, is_holiday=_fake_holiday([date(2026, 7, 27)])
    ) == date(2026, 7, 28)


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
