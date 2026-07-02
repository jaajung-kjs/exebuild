from app.core.settings import Rule, Filter, Preset


def test_defaults():
    p = Preset(name="강원", department_code="4200")
    assert p.default_date_offset == 1
    assert p.sort == "none"
    assert p.rules == []
    assert p.drop_columns == []


def test_roundtrip_serialization():
    p = Preset(
        name="강원본부 기본",
        department_code="4200",
        default_date_offset=0,
        drop_columns=["담당자", "장비"],
        sheet_split_column="지사",
        rules=[Rule(column="공사명", keyword="활선", match="contains", priority=1, color="#FFFF00")],
        filters=[Filter(column="지사", op="not_null")],
        sort="priority",
        mail_from_name="홍길동",
        mail_from_email="hong@kepco.co.kr",
        mail_recipients=["a@kepco.co.kr", "b@kepco.co.kr"],
        mail_subject="{DATE} 점검 리스트",
        mail_body="본문 {DATE}",
    )
    d = p.to_dict()
    p2 = Preset.from_dict(d)
    assert p2 == p
    assert isinstance(p2.rules[0], Rule)
    assert isinstance(p2.filters[0], Filter)


def test_from_dict_tolerates_missing_optionals():
    p = Preset.from_dict({"name": "x", "department_code": "4200"})
    assert p.name == "x"
    assert p.rules == []
    assert p.mail_recipients == []
