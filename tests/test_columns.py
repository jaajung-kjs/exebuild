from app.core.columns import WORK_MONITOR_COLUMNS


def test_31_columns_no_dupes():
    assert len(WORK_MONITOR_COLUMNS) == 31
    assert len(set(WORK_MONITOR_COLUMNS)) == 31


def test_known_columns_present():
    for c in ("공사/용역명", "협력회사", "작업예정일시", "활선작업여부", "취소 유/무"):
        assert c in WORK_MONITOR_COLUMNS
