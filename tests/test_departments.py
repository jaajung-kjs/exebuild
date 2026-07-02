from app.core import departments as dep


def test_has_29_departments():
    assert len(dep.all_departments()) == 29


def test_name_for_code():
    assert dep.name_for_code("4200") == "강원본부"
    assert dep.name_for_code("6220") == "경인건설본부"
    assert dep.name_for_code("9999") is None


def test_code_for_name():
    assert dep.code_for_name("경남본부") == "5700"
    assert dep.code_for_name("없는본부") is None


def test_grouped_keys_and_counts():
    g = dep.grouped()
    assert list(g.keys()) == ["지역본부", "건설본부", "본사"]
    assert len(g["지역본부"]) == 15
    assert len(g["건설본부"]) == 4
    assert len(g["본사"]) == 10


def test_all_codes_unique():
    codes = [d.code for d in dep.all_departments()]
    assert len(codes) == len(set(codes))
