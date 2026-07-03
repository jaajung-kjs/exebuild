import pandas as pd
import pytest
from app.core.engine import assign_priority, sort_df, process
from app.core.settings import Preset, Rule, Filter


def _df():
    return pd.DataFrame({
        "지사": ["강릉", "원주", "속초"],
        "공사명": ["활선 작업", "변전 점검", "일반 보수"],
        "담당자": ["김", "이", "박"],
    })


def test_assign_priority_non_overlapping_rules():
    rules = [
        Rule(column="공사명", keyword="점검", match="contains", priority=2, color="#F7B9AF"),
        Rule(column="공사명", keyword="활선", match="contains", priority=1, color="#FFFF00"),
    ]
    out = assign_priority(_df(), rules)
    assert list(out["점검순위"]) == ["1순위", "2순위", "3순위"]
    assert list(out["_row_color"]) == ["#FFFF00", "#F7B9AF", ""]


def test_assign_priority_overlap_takes_most_important():
    # 한 행이 1순위·2순위 규칙에 모두 매칭되면 더 중요한 1순위로 처리(그 규칙의 색)
    df = pd.DataFrame({"공사명": ["활선 점검 작업"]})
    rules = [
        Rule(column="공사명", keyword="점검", match="contains", priority=2, color="#F7B9AF"),
        Rule(column="공사명", keyword="활선", match="contains", priority=1, color="#FFFF00"),
    ]
    out = assign_priority(df, rules)
    assert list(out["점검순위"]) == ["1순위"]
    assert list(out["_row_color"]) == ["#FFFF00"]


def test_assign_priority_overlap_is_order_independent():
    # 규칙 순서를 뒤집어도 결과가 같아야 함(중요한 순위가 이김)
    df = pd.DataFrame({"공사명": ["활선 점검 작업"]})
    rules = [
        Rule(column="공사명", keyword="활선", match="contains", priority=1, color="#FFFF00"),
        Rule(column="공사명", keyword="점검", match="contains", priority=2, color="#F7B9AF"),
    ]
    out = assign_priority(df, rules)
    assert list(out["점검순위"]) == ["1순위"]
    assert list(out["_row_color"]) == ["#FFFF00"]


def test_assign_priority_equals_match():
    rules = [Rule(column="지사", keyword="원주", match="equals", priority=1, color="#FFFF00")]
    out = assign_priority(_df(), rules)
    assert list(out["점검순위"]) == ["3순위", "1순위", "3순위"]


def test_assign_priority_no_rules_all_third():
    out = assign_priority(_df(), [])
    assert list(out["점검순위"]) == ["3순위", "3순위", "3순위"]


def test_sort_by_priority():
    df = assign_priority(_df(), [
        Rule(column="공사명", keyword="활선", priority=1, color="#FFFF00"),
        Rule(column="공사명", keyword="변전", priority=2, color="#F7B9AF"),
    ])
    out = sort_df(df, "priority")
    assert list(out["점검순위"]) == ["1순위", "2순위", "3순위"]


def test_sort_none_keeps_order():
    df = assign_priority(_df(), [])
    out = sort_df(df, "none")
    assert list(out["지사"]) == ["강릉", "원주", "속초"]


def test_process_rejects_duplicate_headers():
    df = pd.DataFrame([[1, 2], [3, 4]], columns=["지사", "지사"])
    with pytest.raises(ValueError, match="중복된 열 이름"):
        process(df, Preset(name="t", department_code="4200"))


def test_assign_priority_ignores_out_of_range_priority():
    rules = [Rule(column="공사명", keyword="활선", priority=5, color="#FFFF00")]
    out = assign_priority(_df(), rules)
    assert list(out["점검순위"]) == ["3순위", "3순위", "3순위"]
    assert list(out["_row_color"]) == ["", "", ""]


def test_sort_by_priority_reorders_shuffled_input():
    df = pd.DataFrame({
        "지사": ["속초", "강릉", "원주"],
        "공사명": ["일반 보수", "활선 작업", "변전 점검"],
    })
    ranked = assign_priority(df, [
        Rule(column="공사명", keyword="활선", priority=1, color="#FFFF00"),
        Rule(column="공사명", keyword="변전", priority=2, color="#F7B9AF"),
    ])
    out = sort_df(ranked, "priority")
    assert list(out["점검순위"]) == ["1순위", "2순위", "3순위"]
    assert list(out["지사"]) == ["강릉", "원주", "속초"]


def test_process_without_rules_adds_no_priority_column():
    preset = Preset(name="t", department_code="4200")   # 규칙 없음
    out = process(_df(), preset)
    assert "점검순위" not in out.columns
    assert "_row_color" not in out.columns
    assert len(out) == 3


def test_process_applies_filter_priority_drop_sort():
    preset = Preset(
        name="t", department_code="4200",
        filters=[Filter(column="담당자", op="not_null")],
        rules=[Rule(column="공사명", keyword="활선", priority=1, color="#FFFF00")],
        drop_columns=["담당자"],
        sort="priority",
    )
    out = process(_df(), preset)
    assert "담당자" not in out.columns          # drop 적용
    assert "점검순위" in out.columns
    assert out.iloc[0]["점검순위"] == "1순위"     # priority 정렬로 활선 행이 맨 위
    assert list(out.columns).count("_row_color") == 1
