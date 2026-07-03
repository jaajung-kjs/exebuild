"""규칙 엔진 — 원본 DataFrame + Preset → 가공된 DataFrame (순수 함수)"""

import re

import pandas as pd

from app.core.settings import Preset, Rule, Filter

PRIORITY_LABELS = {1: "1순위", 2: "2순위", 3: "3순위"}


def _filter_mask(col: pd.Series, op: str, value: str):
    """단일 필터 조건의 불리언 마스크. 지원하지 않는 op이면 None."""
    s = col.astype(str)
    if op == "not_null":
        return col.notna() & (s.str.strip() != "")
    if op == "is_empty":
        return col.isna() | (s.str.strip() == "")
    if op == "equals":
        return s == value
    if op == "not_equals":
        return s != value
    if op == "contains":
        return s.str.contains(value, regex=False, na=False)
    if op == "starts_with":
        return s.str.startswith(value, na=False)
    if op == "ends_with":
        return s.str.endswith(value, na=False)
    if op == "in_list":
        vals = [v.strip() for v in re.split(r"[,\n]", value) if v.strip()]
        return s.isin(vals)
    return None


def apply_filters(df: pd.DataFrame, filters: list[Filter], mode: str = "and") -> pd.DataFrame:
    """필터로 행을 선별. mode='and'(모두 만족) 또는 'or'(하나라도 만족).
    존재하지 않는 열·지원하지 않는 조건은 무시."""
    masks = []
    for f in filters:
        if f.column not in df.columns:
            continue
        m = _filter_mask(df[f.column], f.op, f.value)
        if m is not None:
            masks.append(m)
    if not masks:
        return df
    combined = masks[0]
    for m in masks[1:]:
        combined = (combined | m) if mode == "or" else (combined & m)
    return df[combined]


def apply_drop(df: pd.DataFrame, drop_columns: list[str]) -> pd.DataFrame:
    """지정된 이름의 열만 제거. 존재하지 않는 이름은 무시."""
    return df.drop(columns=drop_columns, errors="ignore")


def assign_priority(df: pd.DataFrame, rules: list[Rule]) -> pd.DataFrame:
    """각 행에 규칙 적용. 여러 규칙에 겹쳐 매칭되면 가장 중요한(번호가 작은)
    순위가 이긴다(규칙 나열 순서와 무관). 같은 순위끼리 겹치면 먼저 나열된
    규칙의 색을 쓴다. 매칭 없으면 3순위·무색.
    열 '점검순위'(라벨)와 내부 열 '_row_color'(헥사) 추가."""
    labels: list[str] = []
    colors: list[str] = []
    for _, row in df.iterrows():
        best_priority = None   # None = 아직 매칭 없음
        best_color = ""
        for rule in rules:
            if rule.column not in df.columns:
                continue
            value = row[rule.column]
            value = "" if pd.isna(value) else str(value)
            if rule.match == "equals":
                hit = value == rule.keyword
            else:  # contains
                hit = rule.keyword in value
            if hit and rule.priority in PRIORITY_LABELS:
                # 더 중요한(번호가 작은) 순위만 채택. 동점이면 먼저 나온 규칙 유지.
                if best_priority is None or rule.priority < best_priority:
                    best_priority = rule.priority
                    best_color = rule.color
        if best_priority is None:
            labels.append("3순위")
            colors.append("")
        else:
            labels.append(PRIORITY_LABELS[best_priority])
            colors.append(best_color)
    out = df.copy()
    out["점검순위"] = labels
    out["_row_color"] = colors
    return out


def sort_df(df: pd.DataFrame, sort: str) -> pd.DataFrame:
    """정렬. 'none'=원순서, 'priority'=1→2→3순위, 그 외=해당 열 오름차순."""
    if sort == "none" or not sort:
        return df
    if sort == "priority":
        if "점검순위" not in df.columns:
            return df
        order = {"1순위": 0, "2순위": 1, "3순위": 2}
        key = df["점검순위"].map(order).fillna(9)
        return df.assign(_ord=key).sort_values("_ord", kind="stable").drop(columns="_ord")
    if sort in df.columns:
        return df.sort_values(by=sort, kind="stable")
    return df


def process(df: pd.DataFrame, preset: Preset) -> pd.DataFrame:
    """전체 파이프라인: 필터 → 우선순위 → drop → 정렬.
    (우선순위·필터를 drop보다 먼저 실행해 drop된 열도 규칙에 사용 가능)"""
    dups = df.columns[df.columns.duplicated()].unique().tolist()
    if dups:
        raise ValueError(f"중복된 열 이름이 있어 처리할 수 없습니다: {dups}")
    out = apply_filters(df, preset.filters, preset.filter_mode)
    if preset.rules:                       # 규칙이 있을 때만 '점검순위' 열 추가·색칠
        out = assign_priority(out, preset.rules)
    out = apply_drop(out, preset.drop_columns)
    out = sort_df(out, preset.sort)
    return out.reset_index(drop=True)
