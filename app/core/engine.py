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


def assign_priority(df: pd.DataFrame, rules: list[Rule]) -> pd.DataFrame:
    """각 행에 규칙을 순차 적용(뒤 규칙이 우선). 매칭 없으면 3순위.
    열 '점검순위'(라벨)와 내부 열 '_row_color'(헥사) 추가."""
    labels: list[str] = []
    colors: list[str] = []
    for _, row in df.iterrows():
        priority = 3
        color = ""
        for rule in rules:
            if rule.column not in df.columns:
                continue
            value = row[rule.column]
            value = "" if pd.isna(value) else str(value)
            if rule.match == "equals":
                hit = value == rule.keyword
            else:  # contains
                hit = rule.keyword in value
            if hit:
                priority = rule.priority
                color = rule.color
        labels.append(PRIORITY_LABELS.get(priority, "3순위"))
        colors.append(color)
    out = df.copy()
    out["점검순위"] = labels
    out["_row_color"] = colors
    return out


def sort_df(df: pd.DataFrame, sort: str) -> pd.DataFrame:
    """정렬. 'none'=원순서, 'priority'=1→2→3순위, 그 외=해당 열 오름차순."""
    if sort == "none" or not sort:
        return df
    if sort == "priority":
        order = {"1순위": 0, "2순위": 1, "3순위": 2}
        key = df["점검순위"].map(order).fillna(9)
        return df.assign(_ord=key).sort_values("_ord", kind="stable").drop(columns="_ord")
    if sort in df.columns:
        return df.sort_values(by=sort, kind="stable")
    return df


def process(df: pd.DataFrame, preset: Preset) -> pd.DataFrame:
    """전체 파이프라인: 필터 → 우선순위 → drop → 정렬.
    (우선순위·필터를 drop보다 먼저 실행해 drop된 열도 규칙에 사용 가능)"""
    out = apply_filters(df, preset.filters)
    out = assign_priority(out, preset.rules)
    out = apply_drop(out, preset.drop_columns)
    out = sort_df(out, preset.sort)
    return out.reset_index(drop=True)
