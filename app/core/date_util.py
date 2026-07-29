"""날짜 기본값 계산과 파이프라인용 포맷 (순수)"""

from datetime import date, datetime, timedelta


def resolve_default_date(today: date, offset: int) -> date:
    """today + offset일. offset: 0=오늘, 1=내일, -1=어제 …"""
    return today + timedelta(days=offset)


def is_holiday(d: date) -> bool:
    """한국 공휴일(대체공휴일 포함) 여부. holidays 라이브러리로 오프라인 계산.

    holidays는 이 함수 안에서 지연 임포트한다 — 코어의 다른 순수 함수가
    라이브러리에 끌려가지 않게 하고, 라이브러리가 없어도 나머지는 동작하게."""
    import holidays  # noqa: PLC0415 (지연 임포트 의도적)

    return d in holidays.SouthKorea(years=[d.year])


def next_business_day(d: date, is_holiday=is_holiday) -> date:
    """d 이상(포함)의 가장 빠른 영업일. 토·일 또는 공휴일이면 하루씩 전진.

    is_holiday는 주입 가능 — 단위 테스트가 라이브러리 없이 결정론적으로 검증."""
    cur = d
    while cur.weekday() >= 5 or is_holiday(cur):   # 5=토, 6=일
        cur += timedelta(days=1)
    return cur


def resolve_target_date(mode: str, fixed_date: str, today: date, is_holiday=is_holiday) -> date:
    """설정의 날짜 모드로 대상 날짜 계산.
    mode: 'today' | 'tomorrow' | 'tomorrow_bizday' | 'fixed'.
    fixed면 fixed_date(YYYY-MM-DD) 사용. tomorrow_bizday면 내일 이후 가장 빠른 영업일.
    파싱 실패/그 외에는 내일."""
    if mode == "today":
        return today
    if mode == "tomorrow_bizday":
        return next_business_day(today + timedelta(days=1), is_holiday=is_holiday)
    if mode == "fixed" and fixed_date:
        try:
            return datetime.strptime(fixed_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    return today + timedelta(days=1)


def date_formats(d: date) -> dict:
    """파이프라인 각 단계가 쓰는 3가지 날짜 문자열."""
    return {
        "ymd": d.strftime("%Y-%m-%d"),        # downloader date_from
        "yymmdd": d.strftime("%y%m%d"),       # 파일명, 메일 제목 {DATE}
        "yy_mm_dd": d.strftime("'%y-%m-%d"),  # 메일 본문 {DATE}
    }
