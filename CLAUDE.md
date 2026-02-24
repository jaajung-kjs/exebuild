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

# Build standalone EXE
pip install pyinstaller
pyinstaller build_exe.spec
# Output: dist/KEPCO_RPA.exe
```

There are no tests or linting configured.

## Architecture

### Pipeline Flow

```
auth.authenticate()  →  downloader.download_excel_to_dataframe()  →  processor.process_dataframe()  →  mailer.send_bizmail()
   (PowerGate WSS)         (Work Monitor HTTP)                        (Classify + Excel)                (KEPCO BizMail)
```

A single `requests.Session` with PowerGate SSO cookies is created at startup and reused across all HTTP calls.

### Module Responsibilities

- **main.py** - Orchestrator. Reads department code from `분류표.xlsx` cell M2, then runs the 4-step pipeline.
- **auth.py** - Connects to local PowerGate via WebSocket (`ws://127.0.0.1:21777`), extracts SSO cookies (`pgsecuid`, `pgsecuid2`, `opv`), returns an authenticated `requests.Session`.
- **downloader.py** - POSTs to Work Monitor's `/WORK/DAYWORK/excel_extract.php`. Auto-detects HTML vs Excel response format. Returns a `pandas.DataFrame`.
- **processor.py** - Core business logic. Loads classification keywords and mail config from `분류표.xlsx`. Determines priority (1순위/2순위/3순위) per row based on category type and keyword matching. Generates formatted multi-sheet Excel (one sheet per D-column unique value).
- **mailer.py** - Uploads attachment, validates recipients, sends via BizMail REST API. Uses list-of-tuples (not dict) for form data to support multiple recipients with the same `'to'` key.
- **config.py** - Centralized paths, URLs, timeouts. `get_base_dir()` handles both script and PyInstaller exe contexts.

### Critical Data File: 분류표.xlsx

This Excel file drives all business rules and is the only file end-users edit:

- **Sheet 1**: Classification keywords (A-F columns by category), special override rules (I-K columns)
- **Sheet 2**: Mail config — sender (A2, B2), recipients (D2:D*n*), subject (E2), body (F2)
- **Cell M2**: Department code (overrides `config.DEPARTMENT_CODE` fallback)

Subject and body support `{DATE}` placeholder (auto-replaced with tomorrow's date).

### Priority Classification Logic (processor.py)

1. Determine category type from H열 (배전/송전/변전/토건/ICT/기타)
2. Search combined text (H열 + F열 + O열) against category-specific keyword lists
3. Apply special override rules from I-K columns (exact or substring match)
4. Default to 3순위 if no keywords match

### Key Technical Decisions

- **In-memory processing**: DataFrame stays in memory; only one disk write for the final Excel output
- **HTML detection**: Work Monitor sometimes returns HTML tables instead of Excel — `downloader.py` handles both via content-type sniffing
- **Multi-recipient fix**: BizMail API requires each recipient as a separate `'to'` form field — uses `list[tuple]` instead of `dict`
- **Path abstraction**: `config.get_base_dir()` uses `sys.frozen` to detect PyInstaller runtime

## Internal URLs (KEPCO Intranet Only)

- Work Monitor: `http://work-monitor.kepco.co.kr`
- BizMail: `http://bizmail.kepco.co.kr`
- PowerGate WebSocket: `ws://127.0.0.1:21777`
