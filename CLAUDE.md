# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KEPCO RPA automation system for construction project inspection workflows. Downloads inspection data from Work Monitor, classifies priorities using keyword rules, generates multi-sheet Excel reports, and sends them via BizMail. Deployed as a standalone EXE for KEPCO intranet users.

All UI text, comments, and documentation are in Korean.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Build standalone EXE (사내망 Windows에서 실행)
pip install pyinstaller
pyinstaller build_exe.spec
# Output: dist/KEPCO_RPA.exe
```

There are no tests or linting configured.

## Architecture

### Pipeline Flow

```
main.py (orchestrator)
  ├── read_target_date()      ← 분류표.xlsx N2 (비어있으면 내일)
  ├── read_department_code()   ← 분류표.xlsx M2 (비어있으면 "4200")
  │
  ├── [1/3] 인증 + 다운로드 (재시도 루프, 최대 10회)
  │     ├── auth.authenticate()                    ← PowerGate WSS 쿠키 획득 (재시도 없음, 실패 시 None)
  │     └── downloader.download_excel_to_dataframe() ← Work Monitor HTTP (열 ≤1이면 실패)
  │         └── 인증 또는 다운로드 실패 시 → main.py 루프가 재인증부터 다시 시도
  │
  ├── [2/3] 데이터 가공
  │     ├── processor.load_classification_and_mail_config()
  │     └── processor.process_dataframe()          ← 분류 + Excel 생성
  │
  └── [3/3] 메일 전송
        └── mailer.send_bizmail()                  ← KEPCO BizMail
```

### Module Responsibilities

- **main.py** - Orchestrator. Reads target date (N2) and department code (M2) from `분류표.xlsx`. Runs 3-step pipeline with auth+download retry loop.
- **auth.py** - Connects to local PowerGate via WebSocket (`ws://127.0.0.1:21777`), extracts SSO cookies (`pgsecuid`, `pgsecuid2`, `opv`), and creates a `requests.Session`. A single attempt — no session validation, no internal retry; returns `None` on WebSocket failure or malformed response. The auth+download retry loop lives entirely in `main.py`.
- **downloader.py** - POSTs to Work Monitor's `/WORK/DAYWORK/excel_extract.php`. Auto-detects HTML vs Excel response format. Validates DataFrame column count (≤1 column = server error). Returns a `pandas.DataFrame`.
- **processor.py** - Core business logic. Loads classification keywords and mail config from `분류표.xlsx`. Determines priority (1순위/2순위/3순위) per row based on category type and keyword matching. Generates formatted multi-sheet Excel (one sheet per D-column unique value). Accepts `target_date_yymmdd` parameter for filename.
- **mailer.py** - Uploads attachment, validates recipients, sends via BizMail REST API. Uses list-of-tuples (not dict) for form data to support multiple recipients with the same `'to'` key. Accepts `date_yymmdd`, `date_yy_mm_dd` parameters for subject/body.
- **config.py** - Centralized paths, URLs, timeouts. `get_base_dir()` handles both script and PyInstaller exe contexts.

### Retry & Validation Strategy

Two failure modes are handled:

1. **SSO 미완료 / 인증 실패** (PowerGate 초기화 타이밍): `auth.authenticate()`가 쿠키 획득 실패 시 `None` 반환. 검증·재시도는 `auth.py` 안에 없고, `main.py` 루프가 재인증부터 다시 시도 (최대 10회, 3초 간격)
2. **서버 일시 오류** (Work Monitor 내부 오류): `downloader.py`가 DataFrame 열 개수 검증 (≤1이면 None 반환), `main.py`가 재인증부터 다시 시도 (최대 10회)

> 참고: `main.py`의 재시도 루프는 `MAX_RETRIES=10`, `RETRY_DELAY=3`초로, 인증·다운로드를 한 단위로 묶어 재시도한다. 세션 검증 목적의 별도 GET 요청은 존재하지 않는다.

### Critical Data File: 분류표.xlsx

This Excel file drives all business rules and is the only file end-users edit:

- **Sheet 1**: Classification keywords (A-F columns by category), special override rules (I-K columns)
- **Sheet 2**: Mail config — sender (A2, B2), recipients (D2:D*n*), subject (E2), body (F2)
- **Cell M2**: Department code (overrides `config.DEPARTMENT_CODE` fallback)
- **Cell N2**: Target date (YYYY-MM-DD format or Excel date, empty = tomorrow)

Subject and body support `{DATE}` placeholder (auto-replaced with target date).

### Date Parameter Flow

Target date is read once from `분류표.xlsx` N2 and passed through the entire pipeline:

| Format | Usage | Example |
|--------|-------|---------|
| `YYYY-MM-DD` | downloader `date_from` | `2025-03-01` |
| `YYMMDD` | processor filename, mailer subject `{DATE}` | `250301` |
| `'YY-MM-DD` | mailer body `{DATE}` | `'25-03-01` |

### Priority Classification Logic (processor.py)

1. Determine category type from H열 (배전/송전/변전/토건/ICT/기타)
2. Search combined text (H열 + F열 + O열) against category-specific keyword lists
3. Apply special override rules from I-K columns (exact or substring match)
4. Default to 3순위 if no keywords match

### Key Technical Decisions

- **In-memory processing**: DataFrame stays in memory; only one disk write for the final Excel output
- **HTML detection**: Work Monitor sometimes returns HTML tables instead of Excel — `downloader.py` handles both via content-type sniffing
- **Column validation**: Server errors return 1-column DataFrame with error message — detected and treated as download failure
- **Multi-recipient fix**: BizMail API requires each recipient as a separate `'to'` form field — uses `list[tuple]` instead of `dict`
- **Path abstraction**: `config.get_base_dir()` uses `sys.frozen` to detect PyInstaller runtime
- **Centralized date**: All modules receive date from `main.py` instead of independently calculating tomorrow

## Internal URLs (KEPCO Intranet Only)

- Work Monitor: `http://work-monitor.kepco.co.kr`
- BizMail: `http://bizmail.kepco.co.kr`
- PowerGate WebSocket: `ws://127.0.0.1:21777`
