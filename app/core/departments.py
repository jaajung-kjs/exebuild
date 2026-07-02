"""전국 본부↔부서코드 매핑 (하드코딩 고정 목록)"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Department:
    code: str
    name: str
    group: str  # "지역본부" | "건설본부" | "본사"


DEPARTMENTS: list[Department] = [
    # 지역본부 (15)
    Department("3970", "서울본부", "지역본부"),
    Department("3800", "남서울본부", "지역본부"),
    Department("4000", "인천본부", "지역본부"),
    Department("3900", "경기본부", "지역본부"),
    Department("3420", "경기북부본부", "지역본부"),
    Department("4200", "강원본부", "지역본부"),
    Department("4500", "충북본부", "지역본부"),
    Department("4600", "대전세종충남본부", "지역본부"),
    Department("4800", "전북본부", "지역본부"),
    Department("5000", "광주전남본부", "지역본부"),
    Department("5200", "대구본부", "지역본부"),
    Department("5250", "경북본부", "지역본부"),
    Department("5500", "부산울산본부", "지역본부"),
    Department("5700", "경남본부", "지역본부"),
    Department("5900", "제주본부", "지역본부"),
    # 건설본부 (4)
    Department("6220", "경인건설본부", "건설본부"),
    Department("6486", "중부건설본부", "건설본부"),
    Department("6250", "남부건설본부", "건설본부"),
    Department("0147", "HVDC건설본부", "건설본부"),
    # 본사 (10)
    Department("0459", "기획부사장", "본사"),
    Department("0499", "전력혁신본부", "본사"),
    Department("0469", "경영관리본부", "본사"),
    Department("0479", "상생협력본부", "본사"),
    Department("0485", "안전&영업배전부사장", "본사"),
    Department("0464", "영업본부", "본사"),
    Department("0483", "기술혁신본부", "본사"),
    Department("0481", "전력계통본부", "본사"),
    Department("0905", "해외원전사업본부", "본사"),
    Department("0903", "원전수출본부", "본사"),
]


def all_departments() -> list[Department]:
    return list(DEPARTMENTS)


def name_for_code(code: str) -> str | None:
    for d in DEPARTMENTS:
        if d.code == code:
            return d.name
    return None


def code_for_name(name: str) -> str | None:
    for d in DEPARTMENTS:
        if d.name == name:
            return d.code
    return None


def grouped() -> dict[str, list[Department]]:
    result: dict[str, list[Department]] = {"지역본부": [], "건설본부": [], "본사": []}
    for d in DEPARTMENTS:
        result[d.group].append(d)
    return result
