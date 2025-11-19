"""
PowerGate authentication module
Handles WebSocket communication for SSO authentication
"""

import asyncio
import websockets
import requests
from config import POWERGATE_WS_URI, WEBSOCKET_TIMEOUT


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
                session = parts[0]
                uid = parts[1]
                opv = parts[3]

                cookies = {
                    'pgsecuid': session,
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


def authenticate():
    """
    Complete authentication workflow

    Returns:
        requests.Session: Authenticated session
        None: If authentication fails
    """
    print("[인증] PowerGate 인증 시작...")

    # Get cookies via WebSocket
    cookies = asyncio.run(get_powergate_cookies())

    if cookies is None:
        print("[인증 실패] PowerGate 연결 실패")
        return None

    # Create authenticated session
    session = create_authenticated_session(cookies)
    print("[인증 완료] 세션 생성 완료\n")

    return session
