import pandas as pd
from app.core.engine import apply_filters, apply_drop
from app.core.settings import Filter


def _df():
    return pd.DataFrame({
        "지사": ["강릉", None, "원주"],
        "공사명": ["활선 작업", "일반 점검", "변전 점검"],
        "상태": ["예정", "취소", "예정"],
    })


def test_not_null_filter_drops_null_rows():
    out = apply_filters(_df(), [Filter(column="지사", op="not_null")])
    assert list(out["지사"]) == ["강릉", "원주"]


def test_equals_filter():
    out = apply_filters(_df(), [Filter(column="상태", op="equals", value="예정")])
    assert len(out) == 2
    assert set(out["상태"]) == {"예정"}


def test_contains_and_not_equals_combined_as_and():
    out = apply_filters(_df(), [
        Filter(column="공사명", op="contains", value="점검"),
        Filter(column="상태", op="not_equals", value="취소"),
    ])
    assert list(out["공사명"]) == ["변전 점검"]


def test_filter_on_missing_column_is_ignored():
    out = apply_filters(_df(), [Filter(column="없는열", op="not_null")])
    assert len(out) == 3


def test_apply_drop_removes_named_columns_only():
    out = apply_drop(_df(), ["상태", "없는열"])
    assert list(out.columns) == ["지사", "공사명"]


def test_is_empty_selects_null_and_blank_rows():
    df = pd.DataFrame({"지사": ["강릉", None, "  ", "원주"]})
    out = apply_filters(df, [Filter(column="지사", op="is_empty")])
    assert len(out) == 2  # None + 공백


def test_starts_with_and_ends_with():
    starts = apply_filters(_df(), [Filter(column="공사명", op="starts_with", value="변전")])
    assert list(starts["공사명"]) == ["변전 점검"]
    ends = apply_filters(_df(), [Filter(column="공사명", op="ends_with", value="점검")])
    assert list(ends["공사명"]) == ["일반 점검", "변전 점검"]


def test_in_list_matches_any_value():
    out = apply_filters(_df(), [Filter(column="지사", op="in_list", value="강릉, 원주")])
    assert list(out["지사"]) == ["강릉", "원주"]


def test_or_mode_keeps_rows_matching_any_condition():
    out = apply_filters(
        _df(),
        [Filter(column="지사", op="equals", value="강릉"),
         Filter(column="상태", op="equals", value="취소")],
        mode="or",
    )
    # 지사=강릉(0행) 또는 상태=취소(1행)
    assert list(out["공사명"]) == ["활선 작업", "일반 점검"]
