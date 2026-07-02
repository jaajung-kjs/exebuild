"""
Excel download module for KEPCO Work Monitor
Returns DataFrame directly for in-memory processing
"""

import time
import requests
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from app.adapters.config import (
    WORK_MONITOR_URL, DOWNLOAD_TIMEOUT,
    PAGE, LIST_COUNT, DEPARTMENT_CODE
)

MIN_VALID_COLUMNS = 2


def is_valid_schema(df, min_columns: int = MIN_VALID_COLUMNS) -> bool:
    """다운로드된 DataFrame이 유효한 스키마인지 판정.
    열 개수가 부족하면(서버 오류 응답 등) False → 호출부가 재시도."""
    return len(df.columns) >= min_columns


def download_excel_to_dataframe(session, date_from=None, date_to=None,
                                department_code=None, on_status=None):
    """
    Download Excel from Work Monitor and return as DataFrame

    Args:
        session (requests.Session): Authenticated session
        date_from (str): Start date (YYYY-MM-DD)
        date_to (str): End date (YYYY-MM-DD)
        department_code (str): Department code
        on_status (callable): 진행/진단 메시지 콜백 (UI 로그 표시용)

    Returns:
        pandas.DataFrame: Downloaded data
        None: If download fails
    """
    def s(msg):
        print(msg)
        if on_status:
            on_status(msg)

    s("엑셀 다운로드 시작")

    # Use provided department_code or fallback to config
    if department_code is None:
        department_code = DEPARTMENT_CODE

    # Set date range
    if not date_from:
        tomorrow = datetime.now() + timedelta(days=1)
        date_from = tomorrow.strftime("%Y-%m-%d")
    if not date_to:
        date_to = date_from

    date_range = f"{date_from} ~ {date_to}"

    print(f"\n[설정]")
    print(f"  페이지: {PAGE}")
    print(f"  항목 수: {LIST_COUNT}개")
    print(f"  날짜 범위: {date_range}")
    print(f"  담당부서 코드: {department_code}")

    # safeRPA/excel_download.py 의 헤더를 그대로 사용 (검증된 동작 헤더)
    # Content-Type 은 세션이 아닌 POST 요청별로만 지정 → 세션 오염 방지
    # 브라우저 HAR과 동일한 헤더 (검증된 동작 헤더)
    # Content-Type 은 세션이 아닌 POST 요청별로만 지정 → 세션 오염 방지
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Origin': WORK_MONITOR_URL,
        'Referer': f'{WORK_MONITOR_URL}/WORK/DAYWORK/list.php',
        'Upgrade-Insecure-Requests': '1',
    })

    try:
        print(f"\n[다운로드] 요청 중...")

        # Request parameters from HAR
        data = {
            'page': str(PAGE),
            'listCnt': str(LIST_COUNT),
            'query_type': 'ALL',
            'gubun1': '',
            'gubun2': 'null',
            'dateRange': date_range,
            'selectOne': department_code,
            'selectTwo': '',
            'selectDept': '',
            'keyword_gubun': '',
            'keyword': '',
            'stat_sel': '',
            'cancel_sel': '',
            'danger_sel': '',
            'day_select': '2'
        }

        # Download Excel (서버가 엑셀 생성에 수십 초~수 분 걸릴 수 있음)
        s(f"서버에 요청({LIST_COUNT}건) — 응답 대기 중… (최대 {DOWNLOAD_TIMEOUT}초)")
        t0 = time.monotonic()
        response = session.post(
            f'{WORK_MONITOR_URL}/WORK/DAYWORK/excel_extract.php',
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            stream=True,
            timeout=DOWNLOAD_TIMEOUT
        )
        body = response.content   # 여기서 전체 수신 완료까지 대기
        elapsed = time.monotonic() - t0
        ctype = response.headers.get('Content-Type', '')
        s(f"응답 수신: {elapsed:.1f}초 · 상태 {response.status_code} · {len(body)}바이트 · {ctype}")

        if response.status_code != 200:
            s(f"[실패] HTTP 오류 {response.status_code} — {response.text[:150]}")
            return None
        if len(body) == 0:
            s("[실패] 빈 응답 — 해당 날짜에 데이터가 없을 수 있습니다.")
            return None

        first_bytes = body[:100]
        is_html = b'<' in first_bytes or b'html' in first_bytes.lower()
        try:
            if is_html:
                dfs = pd.read_html(BytesIO(body), encoding='euc-kr', header=0)
                if not dfs:
                    s("[실패] HTML에서 표를 찾지 못함")
                    return None
                df = dfs[0]
            else:
                df = pd.read_excel(BytesIO(body), engine='xlrd')
        except Exception as e:  # noqa: BLE001
            s(f"[실패] 응답 파싱 오류: {e} · 앞부분: {first_bytes[:60]!r}")
            return None

        if not is_valid_schema(df):
            first_value = str(df.iloc[0, 0]) if len(df) > 0 else ''
            s(f"[실패] 예상과 다른 응답 (열 {len(df.columns)}개) — 내용: {first_value[:100]}")
            return None

        s(f"[성공] {len(df)}행 × {len(df.columns)}열 ({elapsed:.1f}초)")
        return df

    except requests.exceptions.Timeout:
        s(f"[실패] 타임아웃 — 서버가 {DOWNLOAD_TIMEOUT}초 안에 응답하지 않음")
        return None

    except requests.exceptions.RequestException as e:
        s(f"[실패] 네트워크 오류: {e}")
        return None

    except Exception as e:
        s(f"[실패] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return None
