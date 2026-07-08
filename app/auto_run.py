"""무인 자동 실행 — GUI 없이 저장된 설정대로 다운로드→저장→(메일) 후 종료.

Windows 작업 스케줄러 등에서 EXE를 `--auto` 인자로 실행하거나, 파일명에 `_auto`가
포함되면(예: KEPCO_RPA_auto.exe) 이 모드로 동작한다. 결과는 콘솔과 로그 파일에 남는다."""

import sys
from datetime import date, datetime
from pathlib import Path

from app.ui import config_store
from app.core.pipeline import run_auth_and_download
from app.core.engine import process
from app.core.excel_writer import write_excel
from app.core.date_util import resolve_target_date, date_formats
from app.core.mail_config import preset_to_mail_config
from app.adapters import auth, downloader, mailer
from app import app_paths


def is_auto_mode() -> bool:
    if "--auto" in sys.argv:
        return True
    exe = Path(sys.executable if getattr(sys, "frozen", False) else sys.argv[0])
    return "_auto" in exe.stem.lower()


def _log(msg: str):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    try:
        with open(app_paths.output_dir() / "자동실행.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def run_auto() -> int:
    """저장된 설정으로 1회 실행. 반환값 = 프로세스 종료코드(0=성공)."""
    preset = config_store.load_config()
    if not preset.department_code:
        _log("자동 실행 중단: 저장된 본부가 없습니다. 먼저 GUI에서 본부·설정을 저장하세요.")
        return 2

    d = resolve_target_date(preset.date_mode, preset.fixed_date, date.today())
    fmts = date_formats(d)
    _log(f"자동 실행 시작 — 대상 {fmts['ymd']} / 본부 {preset.department_code} / "
         f"가공저장={preset.do_process} / 메일={preset.do_mail}")

    def _dl(session, date_from, department_code):
        return downloader.download_excel_to_dataframe(
            session, date_from=date_from, department_code=department_code, on_status=_log)

    session, df = run_auth_and_download(
        auth.authenticate, _dl, date_from=fmts["ymd"],
        department_code=preset.department_code, auth_attempts=3)
    if df is None:
        _log("자동 실행 실패: 인증 또는 다운로드 실패")
        return 1

    try:
        if preset.do_process:
            out = str(app_paths.output_dir() / f"{fmts['yymmdd']} 공사현장 점검 우선순위 리스트.xlsx")
            write_excel(process(df, preset), out, preset.sheet_split_column)
        else:
            out = str(app_paths.output_dir() / f"{fmts['yymmdd']} 공사현장 점검 원본.xlsx")
            write_excel(df, out, "")
    except (ValueError, PermissionError, OSError) as e:
        _log(f"자동 실행 실패: 저장 오류 — {e}")
        return 1
    _log(f"저장 완료: {out}")

    if preset.do_mail:
        mc = preset_to_mail_config(preset)
        if mc["recipients"]:
            _log("메일 발송 중…")
            res = mailer.send_mail(session, mc, [out], fmts["yymmdd"], fmts["yy_mm_dd"])
            _log("메일 발송 " + ("완료" if res.get("success") else f"실패: {res.get('message')}"))
        else:
            _log("메일 수신자가 없어 발송을 건너뜁니다.")

    _log("자동 실행 종료")
    return 0
