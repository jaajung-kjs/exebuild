import pandas as pd
import pytest
import requests
from app.adapters.downloader import is_valid_schema, download_excel_to_dataframe
from app.core.pipeline import SchemaExhaustedError


def test_single_column_is_invalid():
    df = pd.DataFrame({"오류": ["서버 오류 메시지"]})
    assert is_valid_schema(df) is False


def test_multi_column_is_valid():
    df = pd.DataFrame({"지사": ["강릉"], "공사명": ["활선"]})
    assert is_valid_schema(df) is True


def test_custom_min_columns():
    df = pd.DataFrame({"a": [1], "b": [2]})
    assert is_valid_schema(df, min_columns=3) is False


# --- 스키마 이상(열 1개) 응답 재시도 ---

BAD_HTML = b"<table><tr><th>msg</th></tr><tr><td>server busy</td></tr></table>"
GOOD_HTML = b"<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"


class _Resp:
    def __init__(self, body, status=200):
        self.content = body
        self.status_code = status
        self.headers = {"Content-Type": "text/html"}
        self.text = body.decode("ascii", "ignore")


class _Session:
    def __init__(self, bodies):
        self._bodies = list(bodies)
        self.headers = {}
        self.calls = 0

    def post(self, *a, **k):
        self.calls += 1
        return self._bodies.pop(0)


def test_retries_on_single_column_then_succeeds():
    sess = _Session([_Resp(BAD_HTML), _Resp(BAD_HTML), _Resp(GOOD_HTML)])
    slept = []
    df = download_excel_to_dataframe(
        sess, date_from="2025-03-01", department_code="4200",
        schema_retries=3, retry_delay=0, sleep=lambda _: slept.append(1),
    )
    assert df is not None and len(df.columns) == 2
    assert sess.calls == 3        # 잘못된 응답 2번 → 세 번째에 성공
    assert len(slept) == 2        # 재요청 사이 대기 2회


def test_raises_after_schema_retries_exhausted():
    # 재요청을 다 써도 열 부족 → 재인증 신호(SchemaExhaustedError)
    sess = _Session([_Resp(BAD_HTML)] * 3)
    with pytest.raises(SchemaExhaustedError):
        download_excel_to_dataframe(
            sess, date_from="2025-03-01", department_code="4200",
            schema_retries=3, retry_delay=0, sleep=lambda _: None,
        )
    assert sess.calls == 3        # schema_retries 만큼만 재요청


def test_timeout_is_not_retried():
    class _TimeoutSession:
        def __init__(self):
            self.headers = {}
            self.calls = 0

        def post(self, *a, **k):
            self.calls += 1
            raise requests.exceptions.Timeout()

    sess = _TimeoutSession()
    df = download_excel_to_dataframe(
        sess, date_from="2025-03-01", department_code="4200",
        schema_retries=3, retry_delay=0, sleep=lambda _: None,
    )
    assert df is None
    assert sess.calls == 1        # 타임아웃은 재요청 안 함(서버 중복 생성 방지)
