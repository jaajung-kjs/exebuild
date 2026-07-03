"""프리셋 데이터 모델 — 모든 사용자 설정을 담는 직렬화 가능한 구조"""

from dataclasses import dataclass, field, asdict


@dataclass
class Rule:
    column: str
    keyword: str
    match: str = "contains"   # "contains" | "equals"
    priority: int = 3         # 1 | 2 | 3
    color: str = "#FFFFFF"    # 해당 순위 행 배경색 (헥사)


@dataclass
class Filter:
    column: str
    op: str                   # "not_null" | "equals" | "contains" | "not_equals"
    value: str = ""           # not_null이면 무시


@dataclass
class Preset:
    name: str
    department_code: str
    default_date_offset: int = 1        # (구) 0=오늘, 1=내일 — date_mode로 대체
    date_mode: str = "tomorrow"         # "today" | "tomorrow" | "fixed"
    fixed_date: str = ""                # date_mode=="fixed"일 때 YYYY-MM-DD
    do_process: bool = True             # ①실행 '2. 설정 적용해서 저장' 체크 상태
    do_mail: bool = False               # ①실행 '3. 메일 발송' 체크 상태
    drop_columns: list[str] = field(default_factory=list)
    sheet_split_column: str = ""        # 지사 시트 분리 기준 열(헤더명)
    rules: list[Rule] = field(default_factory=list)
    filters: list[Filter] = field(default_factory=list)
    filter_mode: str = "and"            # "and"(모두 만족) | "or"(하나라도 만족)
    sort: str = "none"                  # "none" | "priority" | "<열이름>"
    mail_from_name: str = ""
    mail_from_email: str = ""
    mail_recipients: list[str] = field(default_factory=list)
    mail_subject: str = ""
    mail_body: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Preset":
        data = dict(d)
        data["rules"] = [Rule(**r) for r in data.get("rules", [])]
        data["filters"] = [Filter(**f) for f in data.get("filters", [])]
        # 알 수 없는 키는 무시하고 정의된 필드만 사용
        known = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)
