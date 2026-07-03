import pandas as pd
from app.core.pipeline import run_auth_and_download, SchemaExhaustedError


def test_succeeds_first_try():
    df = pd.DataFrame({"a": [1], "b": [2]})
    calls = []
    session, out = run_auth_and_download(
        authenticate=lambda: "SESSION",
        download=lambda s, date_from, department_code: df,
        date_from="2025-03-01", department_code="4200",
        sleep=lambda _: calls.append("slept"),
    )
    assert session == "SESSION" and out is df
    assert calls == []  # 재인증 없음 → sleep 없음


def test_reauths_on_schema_exhausted_then_succeeds():
    # downloader가 재요청을 다 써도 열 부족 → SchemaExhaustedError → 재인증 후 재시도
    df = pd.DataFrame({"a": [1], "b": [2]})
    auth_calls = {"n": 0}
    dl_calls = {"n": 0}

    def auth():
        auth_calls["n"] += 1
        return f"S{auth_calls['n']}"

    def dl(s, date_from, department_code):
        dl_calls["n"] += 1
        if dl_calls["n"] < 3:
            raise SchemaExhaustedError("열 1개")
        return df

    session, out = run_auth_and_download(
        authenticate=auth, download=dl,
        date_from="2025-03-01", department_code="4200",
        auth_attempts=3, sleep=lambda _: None,
    )
    assert out is df
    assert auth_calls["n"] == 3   # 매 시도마다 재인증
    assert dl_calls["n"] == 3


def test_gives_up_after_auth_attempts_on_persistent_schema_error():
    auth_calls = {"n": 0}

    def auth():
        auth_calls["n"] += 1
        return "S"

    def dl(s, date_from, department_code):
        raise SchemaExhaustedError("열 1개")

    session, out = run_auth_and_download(
        authenticate=auth, download=dl,
        date_from="2025-03-01", department_code="4200",
        auth_attempts=3, sleep=lambda _: None,
    )
    assert session is None and out is None
    assert auth_calls["n"] == 3   # 재인증 3회까지만


def test_none_download_gives_up_without_reauth():
    # None = 타임아웃/네트워크/데이터 없음 → 재인증해도 소용없으니 즉시 종료
    auth_calls = {"n": 0}

    def auth():
        auth_calls["n"] += 1
        return "S"

    session, out = run_auth_and_download(
        authenticate=auth, download=lambda *a, **k: None,
        date_from="2025-03-01", department_code="4200",
        auth_attempts=3, sleep=lambda _: None,
    )
    assert session is None and out is None
    assert auth_calls["n"] == 1   # 재인증 안 함


def test_gives_up_after_auth_attempts_when_auth_fails():
    session, out = run_auth_and_download(
        authenticate=lambda: None,       # 인증 계속 실패
        download=lambda *a, **k: None,
        date_from="2025-03-01", department_code="4200",
        auth_attempts=4, sleep=lambda _: None,
    )
    assert session is None and out is None


def test_download_called_with_department_code_not_date_to():
    # 실제 downloader 시그니처를 흉내: (session, date_from=None, date_to=None, department_code=None)
    seen = {}

    def real_like_download(session, date_from=None, date_to=None, department_code=None):
        seen["date_from"] = date_from
        seen["date_to"] = date_to
        seen["department_code"] = department_code
        return pd.DataFrame({"a": [1], "b": [2]})

    run_auth_and_download(
        authenticate=lambda: "S",
        download=real_like_download,
        date_from="2025-03-01", department_code="4200",
        sleep=lambda _: None,
    )
    assert seen["department_code"] == "4200"   # 본부 코드가 올바른 파라미터로 전달
    assert seen["date_to"] is None             # date_to로 새어들어가면 안 됨
    assert seen["date_from"] == "2025-03-01"
