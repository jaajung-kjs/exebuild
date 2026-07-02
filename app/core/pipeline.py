"""인증+다운로드 재시도 오케스트레이션 (순수 — 콜러블 주입).

UI 워커가 실제 auth/downloader 함수를 주입해 호출한다. 열 스키마 이상은
downloader가 None을 반환하므로 여기서 재시도로 처리된다."""

import time


def run_auth_and_download(authenticate, download, *, date_from, department_code,
                          max_retries=10, delay=3, sleep=time.sleep, on_status=None):
    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            sleep(delay)
        if on_status:
            on_status(f"인증+다운로드 시도 {attempt}/{max_retries}…")
        session = authenticate()
        if session is None:
            continue
        df = download(session, date_from, department_code)
        if df is not None:
            return session, df
    return None, None
