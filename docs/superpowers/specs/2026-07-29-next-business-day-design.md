# "내일(주말·공휴일 제외)" 날짜 모드 설계

작성일: 2026-07-29

## 목적

①실행 화면의 날짜 모드에 **"내일(주말·공휴일 제외)"** 를 신설한다.
선택하면 대상 날짜를 **내일**로 잡되, 그 날이 토·일요일이거나 공휴일(대체공휴일 포함)이면
**그 이후 가장 빠른 영업일**로 민다.

- 예) 금요일 실행 → 내일=토요일 → **월요일**
- 예) 월요일이 공휴일 → **화요일**

## 범위

- **추가**: 콤보박스 항목 하나(`"tomorrow_bizday"`). 오늘·특정날짜와 상호배타.
- **보정 대상은 "내일"뿐**: `오늘`·`특정 날짜` 모드는 영업일 보정을 하지 **않는다**(기존 그대로).
- UI 요소 증가 없음(별도 체크박스 아님 — 죽은 컨트롤/애매한 상태를 피하려 카테고리로).
- YAGNI: 이전 영업일·N영업일 후 등은 만들지 않는다.

## 공휴일 판정

- 파이썬 `holidays` 라이브러리(`holidays.SouthKorea`) 사용.
- **완전 오프라인**: 순수 파이썬 계산으로 설날·추석(음력)과 **대체공휴일**까지 자동 처리.
  네트워크 불필요 → 사내망 오프라인 환경에 적합. 매년 수동 관리 불필요.
- 하드코딩 목록 대비: 동일하게 오프라인이면서 매년 갱신이 필요 없음(방치 시 노후화 없음).

## 변경 사항

### core — `app/core/date_util.py` (순수, 주입 가능)

```python
def is_holiday(d: date) -> bool
    # 기본 구현: holidays.SouthKorea 조회. holidays는 함수 안에서 지연 임포트
    # (코어의 다른 순수 함수가 라이브러리에 끌려가지 않도록).

def next_business_day(d, is_holiday=is_holiday) -> date
    # d 이상(포함)의 가장 빠른 영업일. 토·일 또는 is_holiday(d)이면 하루씩 전진.
```

- `resolve_target_date(mode, fixed_date, today)`에 분기 추가:
  `mode == "tomorrow_bizday"` → `next_business_day(today + 1일)`.
- `is_holiday`를 **주입 가능한 인자**로 둔다 → 단위 테스트는 `holidays` 없이
  가짜 공휴일 집합으로 결정론적 검증(오프라인 테스트 원칙 유지).

### UI — `app/ui/extract_view.py`

- 콤보박스에 `"내일(주말·공휴일 제외)"`(데이터 `"tomorrow_bizday"`)를 **"내일" 바로 뒤**에 추가.
- `_on_date_mode` / `_target_date`가 이 모드일 때 계산된 영업일을 날짜 선택기에
  표시(비활성 = 읽기전용, 오늘·내일과 동일). 사용자가 실제 대상일을 눈으로 확인.
- `apply_preset` / `write_into`는 `date_mode` 문자열만 저장 → **새 필드 불필요**.

### settings — `app/core/settings.py`

- `date_mode` 주석에 `"tomorrow_bizday"` 추가(값 목록 갱신). 저장 스키마 변경 없음(하위호환).

### 빌드 — `build_exe.spec`

- `holidays`는 국가 모듈을 동적 로딩하므로 `collect_submodules('holidays')`를
  `hiddenimports`에 추가(EXE에서 `SouthKorea` 누락 방지). 데이터 파일은 없음.

### 의존성 — `requirements.txt`

- `holidays` 추가.

## 테스트 (`tests/`)

- `next_business_day`
  - 금요일 → 월요일(주말 건너뜀)
  - 공휴일이 월요일이면 → 화요일(주말+공휴일 연속 건너뜀)
  - 이미 평일·비공휴일이면 그대로 반환
  - 주입한 가짜 `is_holiday`로 검증(라이브러리 비의존)
- `resolve_target_date`
  - `"tomorrow_bizday"`: 내일이 평일이면 내일, 주말/공휴일이면 다음 영업일
  - 기존 `today`/`tomorrow`/`fixed` 회귀 무변화
- (선택) `holidays.SouthKorea`가 2026 삼일절 대체공휴일(3/2)을 공휴일로 보는지
  1건 스모크(라이브러리 계약 확인).

## 회귀/하위호환

- 기존 프리셋(레지스트리)의 `date_mode` 값은 그대로 동작. 새 값은 선택 시에만 저장.
- 오늘·특정날짜 동작 불변.
