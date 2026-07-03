"""인증+다운로드 재시도 오케스트레이션 (순수 — 콜러블 주입).

UI 워커가 실제 auth/downloader 함수를 주입해 호출한다. 2단계 재시도 구조:

1. downloader 내부: 열 개수가 부족한(서버가 데이터 대신 오류/안내 페이지를 준)
   응답이면 같은 세션으로 빠르게 재요청(재인증 불필요 — 서버측 일시 문제 대응).
   그 재요청까지 모두 실패하면 `SchemaExhaustedError`를 던진다.
2. 여기(pipeline): SchemaExhaustedError가 오면 세션 문제일 수 있으니 재인증 후
   다시 시도한다(총 auth_attempts회). 타임아웃/네트워크/데이터 없음(download가
   None 반환)은 재인증해도 소용없으므로 즉시 종료한다.
"""

import time


class SchemaExhaustedError(Exception):
    """downloader가 같은 세션 재요청을 모두 소진했는데도 열 개수가 계속 부족.
    세션 만료 등 인증 문제일 수 있어 pipeline이 재인증 후 재시도하도록 신호."""


def run_auth_and_download(authenticate, download, *, date_from, department_code,
                          auth_attempts=3, delay=3, sleep=time.sleep, on_status=None):
    for attempt in range(1, auth_attempts + 1):
        if attempt > 1:
            if on_status:
                on_status(f"재인증 후 다시 시도… ({attempt}/{auth_attempts})")
            sleep(delay)
        session = authenticate()
        if session is None:
            continue   # 인증 실패(PowerGate 등) → 재인증
        try:
            df = download(session, date_from=date_from, department_code=department_code)
        except SchemaExhaustedError:
            # 재요청을 다 써도 열 이상 → 세션 문제일 수 있으니 재인증 후 재시도
            continue
        if df is not None:
            return session, df
        # None = 타임아웃/네트워크/데이터 없음 → 재인증해도 소용없음, 종료
        return None, None
    return None, None
