"""
KEPCO Work Monitor 엑셀 다운로드 프로그램
단일 페이지 다운로드 테스트 버전
"""

import asyncio
import websockets
import requests
from datetime import datetime, timedelta
import os


# ==========================================
# 설정 - 여기만 수정하세요
# ==========================================

# 다운로드 설정
PAGE = 1                    # 페이지 번호 (1부터 시작)
LIST_COUNT = 1000           # 페이지당 항목 수 (최대 100, 시도: 1000도 가능)

# 날짜 설정 (내일 날짜로 자동 설정)
tomorrow = datetime.now() + timedelta(days=1)
DATE_FROM = tomorrow.strftime("%Y-%m-%d")
DATE_TO = tomorrow.strftime("%Y-%m-%d")

# 담당부서
SELECT_ONE = "4200"         # 4200 = 강원본부

# 저장 경로
DOWNLOAD_PATH = "C:/Users/jsk/Downloads"  # 다운로드 폴더 경로

# 파일 형식 (xls 또는 xlsx)
FILE_FORMAT = "xlsx"        # xls 또는 xlsx 선택

# Work Monitor 서버
WORK_MONITOR_SERVER = "http://work-monitor.kepco.co.kr"

# ==========================================
# 메인 코드
# ==========================================


async def get_powergate_cookies():
    """PowerGate WebSocket 인증"""
    uri = "ws://127.0.0.1:21777"

    try:
        async with websockets.connect(uri, timeout=10) as ws:
            await ws.send(";;;GETCONFIGep;")
            response = await ws.recv()
            parts = response.split(';')

            if len(parts) >= 4 and parts[2] != "R":
                cookies = {
                    'pgsecuid': parts[1],
                    'pgsecuid2': f'"{parts[1]}"',
                    'opv': parts[3]
                }
                print(f"[성공] PowerGate 인증 완료")
                print(f"     세션: {parts[0][:20]}...")
                print(f"     ID: {parts[2]}\n")
                return cookies
            else:
                print("[실패] 응답 형식 오류")
                return None

    except Exception as e:
        print(f"[실패] PowerGate 오류: {e}")
        return None


def download_excel(cookies, page=1, list_count=100, date_from=None, date_to=None,
                   select_one="4200", download_path=None, file_format="xlsx"):
    """
    Work Monitor에서 엑셀 다운로드

    Args:
        cookies: PowerGate 쿠키
        page: 페이지 번호 (기본값: 1)
        list_count: 페이지당 항목 수 (기본값: 100, 최대 100, 시도: 1000)
        date_from: 시작 날짜 (YYYY-MM-DD)
        date_to: 종료 날짜 (YYYY-MM-DD)
        select_one: 담당부서 코드 (4200=강원본부)
        download_path: 저장 경로
        file_format: 파일 형식 ("xls" 또는 "xlsx")

    Returns:
        dict: {"success": bool, "message": str, "filepath": str}
    """

    print("=" * 60)
    print("WORK MONITOR 엑셀 다운로드")
    print("=" * 60)

    # 날짜 범위 설정
    if not date_from:
        date_from = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = date_from

    date_range = f"{date_from} ~ {date_to}"

    # 저장 경로 설정
    if not download_path:
        download_path = os.path.join(os.path.expanduser("~"), "Downloads")

    # 파일명 생성 (확장자는 file_format 따라감)
    filename_xls = f"사전신고정보_{date_from}.xls"
    filepath_xls = os.path.join(download_path, filename_xls)

    # xlsx로 저장하는 경우 최종 파일명
    if file_format.lower() == "xlsx":
        filename = f"사전신고정보_{date_from}.xlsx"
        filepath = os.path.join(download_path, filename)
    else:
        filename = filename_xls
        filepath = filepath_xls

    print(f"\n[설정]")
    print(f"  페이지: {page}")
    print(f"  항목 수: {list_count}개")
    print(f"  날짜 범위: {date_range}")
    print(f"  담당부서: {select_one} (강원본부)")
    print(f"  파일 형식: {file_format.upper()}")
    print(f"  저장 경로: {filepath}")

    # 세션 생성
    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Origin': WORK_MONITOR_SERVER,
        'Referer': f'{WORK_MONITOR_SERVER}/WORK/DAYWORK/list.php',
        'Upgrade-Insecure-Requests': '1',
    })

    try:
        # ==========================================
        # 엑셀 다운로드 요청
        # ==========================================
        print(f"\n[다운로드] 요청 중...")

        # HAR에서 추출한 완전한 파라미터
        data = {
            'page': str(page),
            'listCnt': str(list_count),
            'query_type': 'ALL',
            'gubun1': '',
            'gubun2': 'null',
            'dateRange': date_range,
            'selectOne': select_one,
            'selectTwo': '',
            'selectDept': '',
            'keyword_gubun': '',
            'keyword': '',
            'stat_sel': '',
            'cancel_sel': '',
            'danger_sel': '',
            'day_select': '2'
        }

        # 엑셀 다운로드 (stream=True로 큰 파일 처리)
        response = session.post(
            f'{WORK_MONITOR_SERVER}/WORK/DAYWORK/excel_extract.php',
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            stream=True,
            timeout=60
        )

        # 응답 확인
        if response.status_code == 200:
            # Content-Disposition 헤더에서 파일명 추출 시도
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                # 인코딩 문제 해결을 위해 원본 파일명 대신 우리가 만든 파일명 사용
                pass

            # 파일 저장 (먼저 xls로 다운로드)
            print(f"[저장] 파일 다운로드 중...")

            with open(filepath_xls, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # 파일 크기 확인
            file_size = os.path.getsize(filepath_xls)

            if file_size > 0:
                # xlsx 변환이 필요한 경우
                if file_format.lower() == "xlsx":
                    print(f"[변환] HTML → XLSX 변환 중...")
                    try:
                        import pandas as pd

                        # 파일이 HTML인지 확인
                        with open(filepath_xls, 'rb') as f:
                            first_bytes = f.read(100)
                            is_html = b'<' in first_bytes or b'html' in first_bytes.lower()

                        if is_html:
                            # HTML 테이블 읽기
                            print(f"[감지] HTML 형식 파일")
                            # header=0을 명시하여 첫 번째 행을 컬럼명으로 사용
                            dfs = pd.read_html(filepath_xls, encoding='euc-kr', header=0)

                            if dfs:
                                # 첫 번째 테이블 사용
                                df = dfs[0]

                                # xlsx로 저장
                                df.to_excel(filepath, index=False, engine='openpyxl')

                                # 원본 파일 삭제
                                os.remove(filepath_xls)

                                # 최종 파일 크기
                                file_size = os.path.getsize(filepath)

                                print(f"[성공] XLSX 변환 완료!")
                            else:
                                print(f"[경고] HTML 테이블을 찾을 수 없습니다")
                                filepath = filepath_xls
                                filename = filename_xls
                        else:
                            # 실제 Excel 파일인 경우
                            df = pd.read_excel(filepath_xls, engine='xlrd')
                            df.to_excel(filepath, index=False, engine='openpyxl')
                            os.remove(filepath_xls)
                            file_size = os.path.getsize(filepath)
                            print(f"[성공] XLSX 변환 완료!")

                    except ImportError:
                        print(f"\n[경고] pandas 또는 openpyxl 미설치")
                        print(f"        HTML 파일로 저장됩니다")
                        print(f"        XLSX 변환을 원하면:")
                        print(f"        pip install pandas openpyxl lxml")
                        # 원본 파일을 그대로 사용
                        filepath = filepath_xls
                        filename = filename_xls

                    except Exception as e:
                        print(f"\n[경고] 변환 실패: {e}")
                        print(f"        원본 파일로 저장됩니다")
                        # 원본 파일을 그대로 사용
                        filepath = filepath_xls
                        filename = filename_xls

                print(f"\n[성공] 다운로드 완료!")
                print(f"        파일명: {filename}")
                print(f"        크기: {file_size:,} bytes")
                print(f"        경로: {filepath}")
                print("=" * 60)
                return {
                    "success": True,
                    "message": "다운로드 완료",
                    "filepath": filepath,
                    "filesize": file_size
                }
            else:
                os.remove(filepath_xls)  # 빈 파일 삭제
                print(f"\n[실패] 빈 파일 (데이터 없음)")
                print(f"        해당 날짜에 데이터가 없을 수 있습니다")
                print("=" * 60)
                return {
                    "success": False,
                    "message": "빈 파일 (데이터 없음)"
                }
        else:
            print(f"\n[실패] HTTP 오류")
            print(f"        상태 코드: {response.status_code}")
            print(f"        응답: {response.text[:200]}")
            print("=" * 60)
            return {
                "success": False,
                "message": f"HTTP {response.status_code}"
            }

    except requests.exceptions.Timeout:
        print(f"\n[실패] 타임아웃 (60초 초과)")
        print("=" * 60)
        return {"success": False, "message": "타임아웃"}

    except requests.exceptions.RequestException as e:
        print(f"\n[실패] 네트워크 오류: {e}")
        print("=" * 60)
        return {"success": False, "message": str(e)}

    except Exception as e:
        print(f"\n[실패] 예상치 못한 오류: {e}")
        print("=" * 60)
        return {"success": False, "message": str(e)}


async def main():
    """메인 실행"""
    print("\n" + "=" * 60)
    print("KEPCO WORK MONITOR 엑셀 다운로드 프로그램")
    print("=" * 60)
    print(f"시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 쿠키 획득
    print("=" * 60)
    print("인증")
    print("=" * 60)

    cookies = await get_powergate_cookies()

    if not cookies:
        print("\n[실패] 쿠키를 가져올 수 없습니다")
        print("\n해결 방법:")
        print("  1. PowerGate가 실행 중인지 확인")
        print("  2. 작업 관리자에서 PowerGate 프로세스 확인")
        print("  3. PowerGate를 재시작하고 다시 시도")
        return

    # 엑셀 다운로드
    result = download_excel(
        cookies=cookies,
        page=PAGE,
        list_count=LIST_COUNT,
        date_from=DATE_FROM,
        date_to=DATE_TO,
        select_one=SELECT_ONE,
        download_path=DOWNLOAD_PATH,
        file_format=FILE_FORMAT
    )

    # 결과
    print("\n" + "=" * 60)
    print("완료")
    print("=" * 60)
    print(f"종료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"결과: {'성공' if result['success'] else '실패'}")

    if result['success']:
        print(f"\n다운로드된 파일:")
        print(f"  {result['filepath']}")
        print(f"\n다음 테스트:")
        print(f"  1. 파일을 열어서 데이터 확인")
        print(f"  2. LIST_COUNT를 1000으로 변경해서 테스트")
        print(f"  3. PAGE를 2로 변경해서 다음 페이지 테스트")

    print("=" * 60)


if __name__ == '__main__':
    """
    사용 방법:

    1. 설정 수정 (17-33번째 줄)
       - PAGE: 페이지 번호 (1부터 시작)
       - LIST_COUNT: 페이지당 항목 수 (1000 권장!)
       - DATE_FROM/DATE_TO: 날짜 (기본: 내일)
       - SELECT_ONE: 담당부서 코드 (4200=강원본부)
       - DOWNLOAD_PATH: 저장 경로
       - FILE_FORMAT: 파일 형식 ("xls" 또는 "xlsx")

    2. XLSX 변환을 원하는 경우 (선택사항):
       pip install pandas openpyxl lxml

    3. PowerGate 실행 확인

    4. 실행:
       python excel_download.py

    파일 형식:
    - FILE_FORMAT = "xls"  → XLS 파일 그대로 다운로드
    - FILE_FORMAT = "xlsx" → XLS 다운로드 후 XLSX로 변환

    참고:
    - LIST_COUNT=1000으로 설정 (대량 다운로드 가능!)
    - 날짜는 내일로 자동 설정됨
    - 서버는 HTML 형식으로 파일을 전송
    - XLSX 변환: HTML → pandas → Excel
    - 필요 라이브러리: pandas, openpyxl, lxml
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n사용자가 중단했습니다")
