import pandas as pd
from app.core.pipeline import run_auth_and_download


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
    assert calls == []  # 재시도 없음 → sleep 없음


def test_retries_then_succeeds():
    df = pd.DataFrame({"a": [1], "b": [2]})
    attempts = {"n": 0}

    def auth():
        return "S"

    def dl(s, date_from, department_code):
        attempts["n"] += 1
        return None if attempts["n"] < 3 else df

    statuses = []
    session, out = run_auth_and_download(
        authenticate=auth, download=dl,
        date_from="2025-03-01", department_code="4200",
        max_retries=5, sleep=lambda _: None,
        on_status=statuses.append,
    )
    assert out is df and attempts["n"] == 3
    assert len(statuses) == 3  # 시도마다 상태 1회


def test_gives_up_after_max_retries():
    session, out = run_auth_and_download(
        authenticate=lambda: None,       # 인증 계속 실패
        download=lambda *a, **k: None,
        date_from="2025-03-01", department_code="4200",
        max_retries=4, sleep=lambda _: None,
    )
    assert session is None and out is None


def test_download_called_with_department_code_not_date_to():
    # 실제 downloader 시그니처를 흉내: (session, date_from=None, date_to=None, department_code=None)
    seen = {}

    def real_like_download(session, date_from=None, date_to=None, department_code=None):
        seen["date_from"] = date_from
        seen["date_to"] = date_to
        seen["department_code"] = department_code
        import pandas as pd
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
