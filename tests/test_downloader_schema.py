import pandas as pd
from app.adapters.downloader import is_valid_schema


def test_single_column_is_invalid():
    df = pd.DataFrame({"오류": ["서버 오류 메시지"]})
    assert is_valid_schema(df) is False


def test_multi_column_is_valid():
    df = pd.DataFrame({"지사": ["강릉"], "공사명": ["활선"]})
    assert is_valid_schema(df) is True


def test_custom_min_columns():
    df = pd.DataFrame({"a": [1], "b": [2]})
    assert is_valid_schema(df, min_columns=3) is False
