"""
Excel download module for KEPCO Work Monitor
Returns DataFrame directly for in-memory processing
"""

import requests
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from config import (
    WORK_MONITOR_URL, HTTP_TIMEOUT,
    PAGE, LIST_COUNT, DEPARTMENT_CODE
)


def download_excel_to_dataframe(session, date_from=None, date_to=None, department_code=None):
    """
    Download Excel from Work Monitor and return as DataFrame

    Args:
        session (requests.Session): Authenticated session
        date_from (str): Start date (YYYY-MM-DD), default: tomorrow
        date_to (str): End date (YYYY-MM-DD), default: tomorrow
        department_code (str): Department code, default: from config.DEPARTMENT_CODE

    Returns:
        pandas.DataFrame: Downloaded data
        None: If download fails
    """
    print("=" * 60)
    print("엑셀 다운로드")
    print("=" * 60)

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
    print(f"  담당부서: {department_code} (강원본부)")

    # Update session headers
    session.headers.update({
        'Origin': WORK_MONITOR_URL,
        'Referer': f'{WORK_MONITOR_URL}/WORK/DAYWORK/list.php',
        'Content-Type': 'application/x-www-form-urlencoded',
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

        # Download Excel
        response = session.post(
            f'{WORK_MONITOR_URL}/WORK/DAYWORK/excel_extract.php',
            data=data,
            stream=True,
            timeout=HTTP_TIMEOUT
        )

        if response.status_code == 200:
            # Read content into memory
            content = BytesIO(response.content)

            # Check if empty
            if len(response.content) == 0:
                print(f"\n[실패] 빈 파일 (데이터 없음)")
                print(f"        해당 날짜에 데이터가 없을 수 있습니다")
                return None

            # Check if HTML format (server returns HTML table)
            first_bytes = response.content[:100]
            is_html = b'<' in first_bytes or b'html' in first_bytes.lower()

            if is_html:
                print(f"[감지] HTML 형식 파일")
                print(f"[변환] HTML → DataFrame 변환 중...")

                # Read HTML table with first row as header
                dfs = pd.read_html(
                    BytesIO(response.content),
                    encoding='euc-kr',
                    header=0
                )

                if dfs and len(dfs) > 0:
                    df = dfs[0]
                    print(f"[성공] DataFrame 생성 완료!")
                    print(f"        행 수: {len(df)}")
                    print(f"        열 수: {len(df.columns)}")
                    print("=" * 60 + "\n")
                    return df
                else:
                    print(f"[실패] HTML 테이블을 찾을 수 없습니다")
                    return None
            else:
                # Read as Excel file
                print(f"[변환] Excel → DataFrame 변환 중...")
                df = pd.read_excel(content, engine='xlrd')
                print(f"[성공] DataFrame 생성 완료!")
                print(f"        행 수: {len(df)}")
                print(f"        열 수: {len(df.columns)}")
                print("=" * 60 + "\n")
                return df

        else:
            print(f"\n[실패] HTTP 오류")
            print(f"        상태 코드: {response.status_code}")
            print(f"        응답: {response.text[:200]}")
            return None

    except requests.exceptions.Timeout:
        print(f"\n[실패] 타임아웃 ({HTTP_TIMEOUT}초 초과)")
        return None

    except requests.exceptions.RequestException as e:
        print(f"\n[실패] 네트워크 오류: {e}")
        return None

    except Exception as e:
        print(f"\n[실패] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return None
