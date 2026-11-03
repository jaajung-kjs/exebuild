"""고위험 작업시간 추출 — '안전대책' 칸의 시간 표현을 표준형으로 바꿔 별도 열로 옮긴다.

(경남본부 요청) 안전대책 안에 적힌 시간은 양식이 정해져 있지 않으므로, 시간으로 읽히는
표현은 라벨 유무와 관계없이 모두 '고위험 작업시간' 열로 옮기고 안전대책에서는 지운다.

표준형
    범위      09:00 ~ 11:30
    자정 넘김 22:00 ~ 익일 02:00
    열린 범위 13:00 ~  /  ~ 11:00
    단일 시각 14:00
    여러 개   09:00 ~ 10:00, 14:00 ~ 15:00   (중복은 한 번만)

읽을 수 있는 표기
    09:00~11:30 / 9:00-11:30 / 09：00∼11：30 / 09:00:00 / 0900~1130(범위일 때만)
    9시~11시 / 9시 30분 / 9시 반 / 정오 / 자정
    오전·오후·새벽·아침·낮·저녁·밤 / AM·PM (끝 시각의 오전·오후 생략은 앞을 따름)
    ~부터 ~까지 / ~이후 / ~이전 / 익일·다음날
    앞의 라벨('고위험 작업시간:', '작업시간', '시간:')과 뒤의 '(2시간)'·'사이'·'동안'·'중'·'에'도 함께 지움

옮기지 않는 것: '2시간마다' 같은 소요시간, 전화번호, 날짜, 연도·금액, 없는 시각(25:00 등)
"""

import re

import pandas as pd

SAFETY_COL = "안전대책"
HIGH_RISK_COL = "고위험 작업시간"

# ---------- 패턴 ----------
_PRE = r"(?:오전|오후|새벽|아침|낮|저녁|밤|AM|PM|A\.M\.|P\.M\.)"
_POST = r"(?:AM|PM|A\.M\.|P\.M\.)"
_UNIT_AFTER_4 = r"(?:년|월|일|원|명|개|대|건|호|번|회|톤|m|k|t|%)"
_CORE = (
    r"(?:\d{1,2}\s*[:：]\s*\d{2}(?:\s*[:：]\s*\d{2})?(?![\d:：])"     # 09:00, 09:00:00
    r"|\d{1,2}\s*시(?!간)(?:\s*\d{1,2}\s*분|\s*반)?"                   # 9시, 9시 30분, 9시 반
    rf"|\d{{1,2}}(?=\s*{_POST})"                                        # 9AM
    r"|정오|자정"
    rf"|\d{{4}}(?!\d|\s*{_UNIT_AFTER_4}))"                             # 0900 (범위에서만 인정)
)
_POINT = rf"(?:{_PRE}\s*)?{_CORE}(?:\s*{_POST})?"
_TILDE = r"[~∼～〜]"
_SEP = rf"\s*(?:{_TILDE}|[-–—]|부터)\s*{_TILDE}?\s*"
_NEXTDAY = r"(?:(?P<nd>익일|다음\s*날|명일)\s*)?"

_LABEL = (r"(?:(?<![가-힣])(?:(?:고위험|위험)\s*(?:작업\s*)?(?:시간)?|(?:작업\s*)?시간)"
          r"\s*[:：]?\s*)?")
_START = r"(?<![\d:：\-/.])"
_BODY = (
    rf"(?:(?P<a>{_POINT}){_SEP}{_NEXTDAY}(?P<b>{_POINT})(?![\d\-])(?:\s*까지)?"   # 범위
    rf"|(?P<s>{_POINT})\s*(?:이후|부터|{_TILDE})"                                 # 13:00 ~
    rf"|{_TILDE}\s*(?P<e1>{_POINT})|(?P<e2>{_POINT})\s*(?:까지|이전)"              # ~ 11:00
    rf"|(?P<one>{_POINT}))"                                                        # 14:00
)
_TAIL = (
    r"(?:\s*\(\s*(?:\d+\s*시간(?:\s*\d+\s*분)?|\d+\s*분)\s*\)"   # (2시간)
    r"|[^\S\n]*(?:사이|동안)(?![가-힣])"
    r"|[^\S\n]+중(?![가-힣])"
    r"|에(?:는)?(?![가-힣]))?"
)
_TIME_RE = re.compile(_LABEL + _START + _BODY + _TAIL, re.I)

_POINT_RE = re.compile(
    rf"(?:(?P<pre>{_PRE})\s*)?"
    r"(?:(?P<h>\d{1,2})\s*[:：]\s*(?P<m>\d{2})(?:\s*[:：]\s*\d{2})?"
    r"|(?P<h2>\d{1,2})\s*시(?:\s*(?P<m2>\d{1,2})\s*분|\s*(?P<half>반))?"
    r"|(?P<named>정오|자정)"
    rf"|(?P<h1>\d{{1,2}})(?=\s*{_POST})"
    r"|(?P<h4>\d{2})(?P<m4>\d{2}))"
    rf"(?:\s*(?P<post>{_POST}))?",
    re.I,
)

_AM_WORDS = {"오전", "새벽", "아침", "am", "a.m."}
_PM_WORDS = {"오후", "저녁", "pm", "p.m."}


class _Point:
    """파싱된 시각. ampm은 오전·오후 등이 명시된 경우만."""

    def __init__(self, h, m, ampm, four_digit, midnight=False):
        self.h, self.m, self.ampm = h, m, ampm
        self.four_digit = four_digit
        self.midnight = midnight          # '자정'

    @property
    def minutes(self):
        return self.h * 60 + self.m


def _apply_ampm(h, word):
    w = word.lower()
    if w in _PM_WORDS:
        return h + 12 if h < 12 else h
    if w == "낮":
        return h + 12 if 1 <= h <= 6 else h
    if w == "밤":
        if h == 12:
            return 0
        return h + 12 if 6 <= h < 12 else h
    if w in _AM_WORDS:
        return 0 if h == 12 else h
    return h


def _parse_point(text):
    m = _POINT_RE.fullmatch(text.strip())
    if not m:
        return None
    word = m.group("pre") or m.group("post")
    if m.group("named"):
        return _Point(12, 0, None, False) if m.group("named") == "정오" \
            else _Point(0, 0, None, False, midnight=True)
    if m.group("h") is not None:
        h, mi, four = int(m.group("h")), int(m.group("m")), False
    elif m.group("h2") is not None:
        h = int(m.group("h2"))
        mi = 30 if m.group("half") else int(m.group("m2") or 0)
        four = False
    elif m.group("h1") is not None:
        h, mi, four = int(m.group("h1")), 0, False
    else:
        h, mi, four = int(m.group("h4")), int(m.group("m4")), True
    if word:
        if h > 12 and word.lower() not in _PM_WORDS:   # '오전 15시' 같은 모순
            return None
        h = _apply_ampm(h, word)
    if not (0 <= h <= 24 and 0 <= mi <= 59) or (h == 24 and mi):
        return None
    return _Point(h, mi, word, four)


def _fmt(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _fmt_range(a, b, next_day_word):
    start = a.minutes
    if b.midnight and not next_day_word:
        end = 24 * 60
    else:
        end = b.minutes
        # 끝의 오전·오후 생략 → 앞의 '오후'를 따른다 (오후 2시 ~ 4시)
        if b.ampm is None and a.ampm and a.h >= 12 and b.h < 12 and end + 720 >= start:
            end += 720
    overnight = bool(next_day_word)
    if not overnight and end < start:
        if b.ampm is None and start < 720 and end < 720 and end + 720 > start:
            end += 720                     # 9시~2시 → 09:00 ~ 14:00
        else:
            overnight = True               # 22:00~02:00 → 익일
    return f"{_fmt(start)} ~ {'익일 ' if overnight else ''}{_fmt(end)}"


def _standardize(m):
    """정규식 매치 → 표준형 문자열. 시간이 아니면 None."""
    if m.group("a"):
        a, b = _parse_point(m.group("a")), _parse_point(m.group("b"))
        if not a or not b:
            return None
        return _fmt_range(a, b, m.group("nd"))
    for key, pattern in (("s", "{} ~"), ("e1", "~ {}"), ("e2", "~ {}"), ("one", "{}")):
        if m.group(key):
            p = _parse_point(m.group(key))
            if not p or p.four_digit:      # 4자리 숫자는 범위일 때만 시간으로 본다
                return None
            minutes = 24 * 60 if (p.midnight and key in ("e1", "e2")) else p.minutes
            return pattern.format(_fmt(minutes))
    return None


# ---------- 남은 안전대책 정리 ----------
_SEP_CH = r"[,，/·;]"
_EMPTY_BRACKET = re.compile(r"[\(\[<【][\s,，/·;:：]*[\)\]>】]")
_BULLET_ONLY = re.compile(r"(?:\d+|[가나다라마바사아자차카타파하])\s*[.)]|[①-⑳\-•※]")


def _tidy_line(line):
    line = re.sub(r"[ \t]+", " ", line)
    line = _EMPTY_BRACKET.sub("", line)
    line = re.sub(rf"\s*({_SEP_CH})(?:\s*{_SEP_CH})+", r"\1", line)   # 연속 구분자
    line = re.sub(rf"\s+({_SEP_CH})", r"\1", line)
    line = re.sub(r"^[\s,，/·;:：~]+|[\s,，/·;:：~]+$", "", line)          # 앞뒤 구분자
    return line


def _tidy(text):
    lines = [_tidy_line(l) for l in text.splitlines()]
    # 빈 줄과 번호만 남은 줄('2.', '3)', '-', '•')은 지운다
    return "\n".join(l for l in lines if l and not _BULLET_ONLY.fullmatch(l))


# ---------- 공개 함수 ----------
def split_high_risk_time(text):
    """(표준형 시간 문자열, 시간을 뺀 안전대책). 시간이 없으면 ('', 원문 그대로)."""
    if text is None or (not isinstance(text, str) and pd.isna(text)):
        return "", text
    s = str(text)
    found = []

    def repl(m):
        std = _standardize(m)
        if std is None:
            return m.group(0)
        if std not in found:
            found.append(std)
        return "\n" if "\n" in m.group(0) else " "

    rest = _TIME_RE.sub(repl, s)
    if not found:
        return "", text
    return ", ".join(found), _tidy(rest)


def extract_high_risk_time(df: pd.DataFrame) -> pd.DataFrame:
    """'안전대책' 바로 오른쪽에 '고위험 작업시간' 열을 추가한 새 DataFrame.
    '안전대책' 열이 없으면 그대로 돌려준다."""
    if SAFETY_COL not in df.columns:
        return df
    pairs = [split_high_risk_time(v) for v in df[SAFETY_COL]]
    out = df.copy()
    out[SAFETY_COL] = [rest for _, rest in pairs]
    if HIGH_RISK_COL in out.columns:
        out = out.drop(columns=[HIGH_RISK_COL])
    out.insert(out.columns.get_loc(SAFETY_COL) + 1, HIGH_RISK_COL, [t for t, _ in pairs])
    return out
