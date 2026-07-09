"""출력 엑셀 파일명 템플릿 해석 (순수 — Qt/네트워크 의존 없음).

사용자가 ②설정에서 정한 파일명 템플릿의 {DATE}를 대상 날짜(yymmdd)로 치환하고,
윈도우 파일명으로 안전하게 정리한 뒤 `.xlsx` 확장자를 붙인다. 비어 있으면 기본값 사용.
"""

DEFAULT_TEMPLATE = "{DATE} 공사현장 점검 우선순위 리스트"
_ILLEGAL = '\\/:*?"<>|'


def resolve_filename(template: str, date_yymmdd: str, *, default: str = DEFAULT_TEMPLATE) -> str:
    """템플릿 → 실제 파일명. {DATE}=date_yymmdd 치환, 금지문자 제거, .xlsx 부여."""
    t = (template or "").strip() or default
    t = t.replace("{DATE}", date_yymmdd)
    if t.lower().endswith(".xlsx"):     # 확장자 중복 방지
        t = t[:-5]
    for ch in _ILLEGAL:                 # 파일명 금지문자 → _
        t = t.replace(ch, "_")
    t = t.strip().strip(".").strip()    # 끝의 공백·점 제거(윈도우)
    if not t.strip("_ "):               # 의미있는 문자가 없으면(전부 _/공백) 기본값
        t = default.replace("{DATE}", date_yymmdd)
    return t + ".xlsx"
