"""날짜 기본값 계산과 파이프라인용 포맷 (순수)"""

from datetime import date, datetime, timedelta


def resolve_default_date(today: date, offset: int) -> date:
    """today + offset일. offset: 0=오늘, 1=내일, -1=어제 …"""
    return today + timedelta(days=offset)


def resolve_target_date(mode: str, fixed_date: str, today: date) -> date:
    """설정의 날짜 모드로 대상 날짜 계산.
    mode: 'today' | 'tomorrow' | 'fixed'. fixed면 fixed_date(YYYY-MM-DD) 사용,
    파싱 실패/그 외에는 내일."""
    if mode == "today":
        return today
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
