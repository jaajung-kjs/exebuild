# 단일 대화형 EXE 재설계 — 설계 문서

- 작성일: 2026-07-02
- 대상: KEPCO RPA 자동화 시스템 (공사현장 점검 우선순위 리스트 생성기)
- 상태: 승인됨 (구현 계획 작성 예정)

## 1. 배경과 목표

현재 시스템은 `분류표.xlsx` 설정 파일에 의존하는 **콘솔 배치 스크립트**이며, 본부마다
진입점 파일을 포크(`main.py`, `main_경남.py`)하고 빌드 스펙을 수정해야 한다. 우선순위
분류 로직이 코드에 하드코딩되어 있어 사용자가 커스터마이즈할 수 없다.

**목표:** 모든 본부를 하나로 커버하는 **단일 대화형 데스크톱 EXE**. 사용자가 UI에서
날짜·본부를 고르고, 컬럼 drop·우선순위 규칙·필터·색을 직접 설정해 엑셀을 생성하고
메일까지 보낸다. 설정은 앱 프리셋으로 저장·재사용한다.

### 사용자 워크플로 (3단계)

1. **추출** — 날짜 + 본부 선택 → [불러오기]. 정렬·분류 없이 원본 데이터를 받아옴.
   기본 산출물은 지사(D열)별 시트 분리까지.
2. **설정** — 샘플 미리보기를 보며 커스터마이즈: 제외할 컬럼, 우선순위 규칙
   (열+키워드→순위+색), 필터(예: D열 not null), 정렬 → [엑셀 생성].
3. **메일** — 수신자·제목·본문 확인 → [발송].

## 2. 확정된 설계 결정

| 항목 | 결정 |
|------|------|
| 형태 | 단일 대화형 데스크톱 EXE (배치 스크립트 아님) |
| UI 스택 | **PySide6 (Qt)** — 정성 들인 비즈니스 앱 수준의 세련된 UI |
| 앱 레이아웃 | **좌측 사이드바 네비게이션** (①추출 / ②설정 / ③메일 + 프리셋) |
| 설정 화면 배치 | **상단 접이식 설정 섹션 + 하단 가로 전체 샘플 미리보기** |
| 미리보기 | **샘플만** (상위 N행, 예: 20행). 전체(1000행+)는 생성 시점에만 처리 |
| 우선순위 로직 | **범용 규칙 빌더** (`[열] 포함/일치 [키워드] → N순위 + 색`). 기존 대분류 키워드·특별규칙·서울본부 룰은 폐기 |
| 본부 선택 | 29개 본부↔부서코드 **하드코딩**, 그룹(지역/건설/본사)으로 표시 |
| 설정 파일 | `분류표.xlsx` **완전 폐기**. 모든 설정이 앱 프리셋(JSON)으로 이동 |
| 날짜 | 매번 선택하되 프리셋이 기본값(offset) 정의. 기본 채움값 = 오늘+offset |
| 열 스키마 이상 | **경고 아님 → 다운로드 실패로 간주 → 자동 재시도** (최종 실패 시에만 보고) |

## 3. 아키텍처 (3계층)

```
UI 계층 (신규, PySide6)      app/ui/
  main_window · extract_view · configure_view · mail_view · preset_bar · workers · style.qss
코어 계층 (신규 + processor 분해)  app/core/
  settings · preset_store · engine · excel_writer · departments
어댑터 계층 (기존 재사용)     app/adapters/
  auth · downloader(+스키마검증) · mailer · config(URL·타임아웃)
```

**핵심 원칙:** `core/engine.py`는 사내망·UI에 의존하지 않는 **순수 함수**. 사내망 없이
단위 테스트 가능하고, UI 스레드를 막지 않으며, 향후 배치 모드로도 재사용 가능.

### 데이터 흐름 (한 방향)

```
[본부·날짜] →auth+download→ df(원본)
  →(UI: 샘플 미리보기)→ [사용자 설정(Preset)]
  →engine.apply(df, preset)→ df(가공)
  →excel_writer→ result.xlsx
  →mailer.send→ 발송
설정은 언제든 preset_store로 저장/로드
```

### 기존 코드 처리 방침

| 파일 | 처리 |
|------|------|
| `auth.py`, `downloader.py`, `mailer.py` | `app/adapters/`로 이동, 함수 시그니처 유지. downloader에 스키마 검증 추가. UI는 QThread 워커에서 호출 |
| `processor.py` | **분해**: 가공로직→`core/engine.py`, Excel 서식→`core/excel_writer.py`. 기존 우선순위 로직은 범용 규칙 엔진으로 대체 |
| `main.py`, `main_경남.py` | **폐기** (진입점이 `app/main.py` GUI로 대체) |
| `config.py`의 M2/N2·분류표 로직 | **폐기**. URL·타임아웃 상수만 `adapters/config.py`로 유지 |
| `분류표.xlsx` | **폐기** (설정이 프리셋으로 이동) |

## 4. 데이터 모델 (프리셋)

```python
# app/core/settings.py
@dataclass
class Rule:
    column: str            # 대상 열 헤더명
    keyword: str
    match: str             # "contains" | "equals"
    priority: int          # 1 | 2 | 3
    color: str             # "#FFFF00" 등 (해당 순위 행 배경색)

@dataclass
class Filter:
    column: str
    op: str                # "not_null" | "equals" | "contains" | "not_equals"
    value: str = ""        # not_null이면 무시

@dataclass
class Preset:
    name: str
    department_code: str
    default_date_offset: int = 1   # 0=오늘, 1=내일, -1=어제, 2=모레 …
    drop_columns: list[str] = field(default_factory=list)
    sheet_split_column: str = ""   # 지사 시트 분리 기준 열 (기본: 지사/D열)
    rules: list[Rule] = field(default_factory=list)      # 위→아래 순차, 뒤가 우선
    filters: list[Filter] = field(default_factory=list)  # AND 결합
    sort: str = "none"             # "none" | "priority" | "<열이름>"
    # 메일
    mail_from_name: str = ""
    mail_from_email: str = ""
    mail_recipients: list[str] = field(default_factory=list)
    mail_subject: str = ""         # {DATE} 치환
    mail_body: str = ""            # {DATE} 치환
```

**저장:** EXE 옆 `presets/<이름>.json`. 앱 시작 시 스캔 → 사이드바 드롭다운. 저장/덮어쓰기/삭제
지원. 본부별 프리셋을 각각 저장해 EXE 포크 없이 전 본부 커버.

**날짜:** 프리셋에 절대날짜 저장 안 함. 추출 화면 진입 시 `오늘 + default_date_offset`로 날짜
선택기 미리 채움, 사용자가 변경 가능. `{DATE}`는 기존 3포맷(`YYMMDD`/`YYYY-MM-DD`/`'YY-MM-DD`)으로 치환.

### 본부 매핑 (`app/core/departments.py`)

```
[지역본부] 3970 서울 · 3800 남서울 · 4000 인천 · 3900 경기 · 3420 경기북부 ·
          4200 강원 · 4500 충북 · 4600 대전세종충남 · 4800 전북 · 5000 광주전남 ·
          5200 대구 · 5250 경북 · 5500 부산울산 · 5700 경남 · 5900 제주
[건설본부] 6220 경인 · 6486 중부 · 6250 남부 · 0147 HVDC
[본사]     0459 기획부사장 · 0499 전력혁신 · 0469 경영관리 · 0479 상생협력 ·
          0485 안전&영업배전 · 0464 영업 · 0483 기술혁신 · 0481 전력계통 ·
          0905 해외원전사업 · 0903 원전수출
```

## 5. 우선순위 규칙 엔진 (`core/engine.py`)

- 입력: 원본 df + Preset. 출력: 가공된 df(+ `점검순위` 열).
- 처리 순서: ① 필터 적용(AND) → ② drop 컬럼 → ③ 각 행에 규칙 순차 적용(뒤 규칙이
  우선)해 순위 결정, 매칭 없으면 3순위 → ④ 정렬(none/priority/열이름).
- 규칙·필터·시트분리 열은 **열 문자가 아닌 실제 헤더명 기준**으로 매칭 → 서버 열 순서
  변경에 강함.
- 색은 규칙에서 지정한 순위별 색을 `excel_writer`가 행 배경에 적용.

## 6. 엑셀 출력 (`core/excel_writer.py`)

- 기존 `processor.py`의 서식 로직 재사용: 지사(분리 열)별 시트 + 메인 시트, 헤더 스타일,
  순위별 행 색, 테두리, 틀고정, 자동필터, 열 너비.
- 파일명: `YYMMDD 공사현장 점검 우선순위 리스트.xlsx`, EXE 옆에 저장.

## 7. 스레딩 · 에러 처리 · 상태 표시

- **QThread 워커**로 인증·다운로드·메일 실행 → UI 멈춤 방지. 진행 상황은 시그널로
  **진행바 + 상태 로그 패널**에 중계. 기존 `print`는 콘솔 로그로 유지.
- **재시도 루프 이전:** 현재 `main.py`의 "인증+다운로드 10회 재시도"를 다운로드 워커
  안으로 이동. UI에 "인증 시도 3/10…" 표시, [취소] 가능.
- **열 스키마 검증:** 다운로드 직후 컬럼 수/핵심 헤더 확인. 불일치 시 `None` 반환 →
  재시도 루프가 자동 재시도. 10회 모두 실패할 때만 최종 모달로 보고.

| 단계 | 실패 시 UI |
|------|-----------|
| PowerGate 미실행 | 모달 "PowerGate 실행 후 재시도" + [재시도] |
| 다운로드 실패(빈/1열/스키마 불일치) | 자동 재시도, 소진 시 상태 패널 경고 + 데이터 없음 안내 |
| 규칙/필터 오류(없는 열) | 인라인 빨간 표시, [엑셀 생성] 비활성 |
| 엑셀 저장 실패(파일 열림) | 모달 "파일 닫고 재시도" |
| 메일 발송 실패 | 모달 + "엑셀은 저장됨: <경로>" |

## 8. 테스트 전략

- `core/`(engine·excel_writer·settings·departments) + downloader의 스키마 검증 함수 →
  **pytest 단위 테스트** (사내망 불필요).
  - 규칙 적용, 필터(not_null 등), drop, 정렬, 색 매핑, {DATE} 치환, 프리셋 직렬화.
- **골든 스냅샷:** 샘플 원본 df + 프리셋 → 기대 결과 df 고정, 회귀 방지.
- 어댑터(네트워크 의존)와 UI는 자동화 제외(수동 확인).

## 9. 최종 파일 구조

```
app/
  main.py                  진입점 (QApplication)
  ui/  main_window · extract_view · configure_view · mail_view · preset_bar · workers · style.qss
  core/ settings · preset_store · engine · excel_writer · departments
  adapters/ auth · downloader(+스키마검증) · mailer · config
tests/ test_engine · test_filters · test_settings · test_departments
presets/                   런타임 생성(사용자 프리셋)
build_exe.spec             진입점 app/main.py로 갱신
requirements.txt           + PySide6, pytest
```

**빌드:** PyInstaller 단일 EXE. `--windowed`(콘솔 숨김) 검토(로그는 UI 패널). 프리셋은
EXE 옆 `presets/`에 외부 저장.

## 10. 폐기 대상

`main.py`(구), `main_경남.py`, `processor.py`(분해 후 삭제), `분류표.xlsx` 및 M2/N2 로직.

## 11. 범위에서 제외 (YAGNI)

- 전체 데이터 그리드 편집(라이브 스프레드시트) — 샘플 미리보기로 충분.
- 서울본부식 고급 룰(시간대·제재현황·와일드카드) — 범용 규칙으로 대체, 필요 시 후속.
- 다국어 — 한국어 전용 유지.
- 프리셋 내보내기/가져오기(본부 간 공유) — JSON 파일 복사로 대체 가능, 후속 검토.
```
