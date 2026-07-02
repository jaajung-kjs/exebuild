"""규칙 엔진 — 원본 DataFrame + Preset → 가공된 DataFrame (순수 함수)"""

import pandas as pd

from app.core.settings import Preset, Rule, Filter

PRIORITY_LABELS = {1: "1순위", 2: "2순위", 3: "3순위"}


def apply_filters(df: pd.DataFrame, filters: list[Filter]) -> pd.DataFrame:
    """필터를 AND로 결합해 행을 선별. 존재하지 않는 열 필터는 무시."""
    result = df
    for f in filters:
        if f.column not in result.columns:
            continue
        col = result[f.column]
        if f.op == "not_null":
            mask = col.notna() & (col.astype(str).str.strip() != "")
        elif f.op == "equals":
            mask = col.astype(str) == f.value
        elif f.op == "not_equals":
            mask = col.astype(str) != f.value
        elif f.op == "contains":
            mask = col.astype(str).str.contains(f.value, regex=False, na=False)
        else:
            continue
        result = result[mask]
    return result


def apply_drop(df: pd.DataFrame, drop_columns: list[str]) -> pd.DataFrame:
    """지정된 이름의 열만 제거. 존재하지 않는 이름은 무시."""
    return df.drop(columns=drop_columns, errors="ignore")
