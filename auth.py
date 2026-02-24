"""
PowerGate authentication module
Handles WebSocket communication for SSO authentication
"""

import asyncio
import time
import websockets
import requests
from config import POWERGATE_WS_URI, WORK_MONITOR_URL, WEBSOCKET_TIMEOUT, HTTP_TIMEOUT

MAX_AUTH_RETRIES = 10
AUTH_RETRY_DELAY = 2  # seconds


async def get_powergate_cookies():
    """
    Connect to PowerGate and retrieve authentication cookies

    Returns:
        dict: Authentication cookies {pgsecuid, pgsecuid2, opv}
        None: If authentication fails
    """
    try:
        async with websockets.connect(POWERGATE_WS_URI, timeout=WEBSOCKET_TIMEOUT) as ws:
            # Send authentication request
            await ws.send(";;;GETCONFIGep;")

            # Receive response
            response = await ws.recv()
            print(f"[인증] PowerGate 응답 수신")

            # Parse response: {session};{uid};{user_id};{opv}
            parts = response.split(';')

            if len(parts) >= 4:
                session_val = parts[0]
                uid = parts[1]
                opv = parts[3]

                cookies = {
                    'pgsecuid': session_val,
                    'pgsecuid2': uid,
                    'opv': opv
                }

                print(f"[인증] 쿠키 획득 성공")
                return cookies
            else:
                print(f"[인증 오류] 응답 형식 오류: {response}")
                return None

    except asyncio.TimeoutError:
        print(f"[인증 오류] PowerGate 연결 시간 초과")
        return None
    except Exception as e:
        print(f"[인증 오류] {str(e)}")
        return None


def create_authenticated_session(cookies):
    """
    Create a requests Session with authentication cookies

    Args:
        cookies (dict): Authentication cookies from get_powergate_cookies()

    Returns:
        requests.Session: Authenticated session object
    """
    session = requests.Session()

    # Set cookies
    for key, value in cookies.items():
        session.cookies.set(key, value)

    # Set headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    })

    return session


def validate_session(session):
    """
    Validate session by making a GET request to Work Monitor

    Args:
        session (requests.Session): Session to validate

    Returns:
        bool: True if session is valid
    """
    try:
        resp = session.get(
            f'{WORK_MONITOR_URL}/WORK/DAYWORK/list.php',
            timeout=HTTP_TIMEOUT,
            allow_redirects=False
        )

        # 리다이렉트(302) → 로그인 페이지로 이동 = 인증 실패
        if resp.status_code in (301, 302):
            print(f"[인증 검증] 실패 — 로그인 페이지로 리다이렉트 (HTTP {resp.status_code})")
            return False

        # 200이지만 응답 내용이 너무 짧으면 실패
        if resp.status_code == 200 and len(resp.content) < 500:
            print(f"[인증 검증] 실패 — 응답이 비정상적으로 짧음 ({len(resp.content)} bytes)")
            return False

        if resp.status_code == 200:
            print(f"[인증 검증] 성공 — Work Monitor 접근 확인")
            return True

        print(f"[인증 검증] 실패 — HTTP {resp.status_code}")
        return False

    except Exception as e:
        print(f"[인증 검증] 실패 — {str(e)}")
        return False


def authenticate():
    """
    Complete authentication workflow with retry

    최대 MAX_AUTH_RETRIES회까지 재시도:
    1. PowerGate WebSocket에서 쿠키 획득
    2. 세션 생성
    3. Work Monitor GET 요청으로 세션 유효성 검증

    Returns:
        requests.Session: Authenticated and validated session
        None: If all retries exhausted
    """
    for attempt in range(1, MAX_AUTH_RETRIES + 1):
        if attempt > 1:
            print(f"\n  🔄 인증 재시도 {attempt}/{MAX_AUTH_RETRIES} ({AUTH_RETRY_DELAY}초 대기 후)...")
            time.sleep(AUTH_RETRY_DELAY)
        else:
            print("[인증] PowerGate 인증 시작...")

        # 1. Get cookies via WebSocket
        cookies = asyncio.run(get_powergate_cookies())

        if cookies is None:
            print(f"  ⚠️  쿠키 획득 실패")
            continue

        # 2. Create session
        session = create_authenticated_session(cookies)

        # 3. Validate session with actual HTTP request
        if validate_session(session):
            print("[인증 완료] 세션 생성 및 검증 완료\n")
            return session

        print(f"  ⚠️  세션 검증 실패 — SSO 인증 미완료 가능성")

    print(f"\n[인증 실패] {MAX_AUTH_RETRIES}회 시도 후에도 인증에 실패했습니다")
    return None
