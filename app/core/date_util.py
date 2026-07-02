"""날짜 기본값 계산과 파이프라인용 포맷 (순수)"""

from datetime import date, timedelta


def resolve_default_date(today: date, offset: int) -> date:
    """today + offset일. offset: 0=오늘, 1=내일, -1=어제 …"""
    return today + timedelta(days=offset)


def date_formats(d: date) -> dict:
    """파이프라인 각 단계가 쓰는 3가지 날짜 문자열."""
    return {
        "ymd": d.strftime("%Y-%m-%d"),        # downloader date_from
        "yymmdd": d.strftime("%y%m%d"),       # 파일명, 메일 제목 {DATE}
        "yy_mm_dd": d.strftime("'%y-%m-%d"),  # 메일 본문 {DATE}
    }
