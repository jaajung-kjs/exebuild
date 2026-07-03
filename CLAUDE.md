# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KEPCO 공사현장 점검 우선순위 리스트 생성기. Work Monitor에서 점검 데이터를 내려받아
사용자가 정한 규칙(강조·필터·정렬)으로 가공하고, 다중 시트 Excel로 저장하며, 선택적으로
BizMail로 발송하는 **대화형 PySide6 데스크톱 앱**. 사내망 Windows용 단일 EXE로 배포된다.

모든 UI 텍스트·주석·문서는 한국어.

## Commands

```bash
pip install -r requirements.txt   # 의존성 (PySide6, requests, websockets, pandas, openpyxl, xlrd, lxml)
python -m app.main                # 앱 실행 (GUI)
pytest -q                         # 순수 로직 단위 테스트 (사내망 불필요)
pyinstaller build_exe.spec        # 단일 EXE 빌드 (사내망 Windows) → dist/KEPCO_RPA.exe
```

GitHub Actions(`.github/workflows/build-exe.yml`)가 `main` 푸시 시 Windows EXE를 빌드해
아티팩트로 올린다.

## Architecture

3계층. UI는 코어를 호출만 하고, 코어는 네트워크·Qt에 의존하지 않는 순수 함수라 오프라인
단위 테스트가 가능하다.

```
app/
  main.py                진입점 (QApplication)
  app_paths.py           출력 폴더 경로
  ui/  (PySide6)
    main_window.py       사이드바 + 스택 + [설정 저장]
    extract_view.py      ① 실행 — 유일한 실행 진입점(다운로드·저장·메일)
    configure_view.py    ② 설정 — 넣을 항목·강조 규칙·필터·정렬 편집(문장형)
    mail_view.py         ③ 메일 설정(베타) — 발신·수신·제목·본문 편집
    workers.py           DownloadWorker / MailWorker (QThread, UI 비차단)
    config_store.py      QSettings(윈도우 레지스트리) 단일 설정 자동 저장·복원
    state.py             AppState (df·session·preset·target_date)
    theme.qss            테마
  core/  (순수 로직 — Qt/네트워크 의존 없음)
    engine.py            df + Preset → 가공 df (필터·강조·drop·정렬)
    excel_writer.py      가공 df → 지사별 다중 시트 서식 xlsx
    settings.py          Preset/Rule/Filter 데이터클래스 (+ to_dict/from_dict)
    departments.py       본부 29개 ↔ 부서코드 매핑
    date_util.py         날짜 계산·포맷
    mail_config.py       Preset → mailer용 mail_config dict
    pipeline.py          인증+다운로드 재시도 오케스트레이션(콜러블 주입, 순수)
  adapters/  (사내망 연동, 기존 검증된 코드)
    auth.py              PowerGate WebSocket SSO → requests.Session
    downloader.py        Work Monitor HTTP → pandas.DataFrame (HTML/Excel 자동 감지)
    mailer.py            BizMail REST 발송
    config.py            URL·타임아웃 상수, get_base_dir()/get_output_dir()
tests/                   core·pipeline·downloader 스키마 단위 테스트
```

### 실행 흐름 (실제 실행은 ① 화면에서만)

```
① 실행: 날짜·본부 선택 + 단계 체크 [②정렬·가공 저장 / ③메일] + [▶ 실행]
   ├─ pipeline.run_auth_and_download(auth, downloader) → 세션 + DataFrame (메모리)
   ├─ ② 미체크 → excel_writer.write_excel(원본)          → 원본 저장
   ├─ ② 체크  → engine.process(df, preset) → write_excel → 가공 저장
   │           (설정이 없으면 ②설정 화면으로 안내)
   └─ ③ 체크  → MailWorker(mailer.send_bizmail)          → 메일 발송
② 설정 / ③ 메일 = 설정 편집·저장 전용 ([설정 저장]만, 실행 버튼 없음)
```

## Key Decisions

- **실행 단일 진입점**: 다운로드·저장·메일은 오직 ① 실행 화면에서. ②③은 설정 편집·저장만.
- **설정은 파일이 아니라 레지스트리**: `config_store`가 QSettings(윈도우 레지스트리)에 단일
  설정을 저장·자동복원. 새 파일을 만들지 않아 **사내 DRM의 영향을 받지 않는다**. 다중 프리셋
  없음(한 설정을 계속 사용).
- **인메모리 처리**: 다운로드는 디스크 파일을 만들지 않는다. 앱이 만드는 파일은 결과 엑셀뿐.
- **강조 규칙 있을 때만** 결과에 "점검순위" 열 추가(+행 색). 규칙 없으면 원본 유지.
- **범용 규칙 엔진**: `[열] + 키워드 + 매칭(contains/equals) → 순위 + 색`. 필터는 열별 조건
  (not_null/is_empty/contains/equals/not_equals/starts_with/ends_with/in_list) + AND/OR 결합.
- **열은 헤더명으로 매칭**(열 문자 아님) → Work Monitor 열 순서 변경에 강함.
- **중복 헤더 방어**: `engine.process`는 중복 열 이름이 있으면 `ValueError`(호출부에서 안내).
- **QThread 워커**: 인증·다운로드·메일은 워커에서 실행, 시그널로 UI에 상태 전달.
- **재시도**: `pipeline.run_auth_and_download`가 인증+다운로드를 최대 10회 재시도. 열 스키마
  이상(`downloader.is_valid_schema`)도 다운로드 실패로 보고 재시도.

## 무인 자동 실행 (작업 스케줄러용)

`app/auto_run.py`. EXE를 `--auto` 인자로 실행하거나 파일명에 `_auto`가 포함되면
(예: `KEPCO_RPA_auto.exe`) GUI 없이 저장된 설정대로 다운로드→저장→(메일)을 1회
수행하고 종료한다. 결과는 실행 파일 옆 `자동실행.log`에 기록. 종료코드 0=성공.
실행 단계(가공 저장/메일)와 본부·날짜는 모두 프리셋(레지스트리)에서 읽는다.

## Internal URLs (KEPCO Intranet Only)

- Work Monitor: `http://work-monitor.kepco.co.kr` (엑셀 다운로드; 서버 생성이 느려 다운로드 타임아웃 300초)
- 웹메일(SSO): `http://mail.kepco.co.kr` (session/check → uploadFile → receiverCheck → send). **발신자(fromaddr/fromname)는 요청에 반드시 실어야 함** — SSO 쿠키만으로는 서버가 발신주소를 채우지 않으므로 ③메일 설정에서 직접 입력한다.
- PowerGate WebSocket: `ws://127.0.0.1:21777`

설정 저장 위치(런타임): `HKEY_CURRENT_USER\Software\KEPCO\점검리스트생성기` (레지스트리)

## 참고

- 설계·구현 계획 문서: `docs/superpowers/`
- 수동 통합 검증 체크리스트(사내망 Windows): `docs/manual-verification-plan2.md`
- 테스트/린팅: `pytest`만 구성됨(린터 없음). UI는 수동 검증.
