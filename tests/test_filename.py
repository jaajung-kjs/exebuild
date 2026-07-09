from app.core.filename import resolve_filename, DEFAULT_TEMPLATE


def test_default_template_substitutes_date():
    assert resolve_filename(DEFAULT_TEMPLATE, "260709") == "260709 공사현장 점검 우선순위 리스트.xlsx"


def test_custom_template():
    assert resolve_filename("강원_점검_{DATE}", "260709") == "강원_점검_260709.xlsx"


def test_empty_uses_default():
    assert resolve_filename("", "260709") == "260709 공사현장 점검 우선순위 리스트.xlsx"
    assert resolve_filename("   ", "260709") == "260709 공사현장 점검 우선순위 리스트.xlsx"


def test_template_without_date_placeholder():
    assert resolve_filename("우리부서 점검표", "260709") == "우리부서 점검표.xlsx"


def test_illegal_chars_are_sanitized():
    assert resolve_filename('a/b:c*{DATE}', "260709") == "a_b_c_260709.xlsx"


def test_existing_xlsx_extension_not_doubled():
    assert resolve_filename("{DATE} 리스트.xlsx", "260709") == "260709 리스트.xlsx"


def test_trailing_dot_and_space_trimmed():
    # 확장자 붙이기 전 끝의 점·공백 제거(윈도우에서 문제)
    assert resolve_filename("{DATE} 리스트.  ", "260709") == "260709 리스트.xlsx"


def test_all_illegal_falls_back_to_default():
    assert resolve_filename('/:*?"<>|', "260709") == "260709 공사현장 점검 우선순위 리스트.xlsx"
