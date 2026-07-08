"""사외(외부) 메일 발송 가능 여부 진단 — 사내망에서 실행.

EXE를 다음처럼 실행하면 GUI 없이 PowerGate 인증 → 메일 서버 session/check →
receiverCheck.do 를 외부 주소로 호출하고, 외부발송 허용 여부를 나타내는 응답 필드를
그대로 출력한다. 결과는 콘솔과 실행 파일 옆 `사외메일진단.log` 에 남는다.

    KEPCO_RPA.exe --diag-external hong@naver.com
    KEPCO_RPA.exe --diag-external hong@naver.com --from myid@kepco.co.kr

핵심 판독:
- permission=false 또는 invalidReceiverList 에 외부주소가 들어감
    → 이 계정/망에서 외부발송이 막혀 있음(사내 자동 외부발송 불가 가능성 높음).
- hasExternalReceiver=true & permission=true
    → 서버는 외부수신자를 허용. 다음 단계는 '결재(승인) 필요 여부'와 실제 send.do 테스트.
"""

import re
import sys
from datetime import date, datetime

from app.adapters import auth, downloader, mailer
from app.adapters.config import MAIL_URL, HTTP_TIMEOUT
from app.core.pipeline import run_auth_and_download
from app.core.date_util import resolve_target_date, date_formats
from app.core.excel_writer import write_excel
from app.ui import config_store
from app import app_paths


def _log(msg: str):
    line = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(line)
    try:
        with open(app_paths.output_dir() / "사외메일진단.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _arg_value(argv, flag: str, default: str = "") -> str:
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


def _parse_recipients(raw: str) -> list:
    """콤마·세미콜론·공백으로 구분된 수신자 문자열 → 리스트."""
    return [p for p in re.split(r"[,;\s]+", (raw or "").strip()) if p]


def _receiver_check(session, recipients, fromaddr):
    data = [
        ("subject", "[진단] 외부발송 확인"),
        ("subjecthead", "-1"),
        ("content", "<html><body>진단</body></html>"),
        ("fromname", ""),
        ("fromaddr", fromaddr),
        ("attach_size", "0"),
        ("attach_list", ""),
    ]
    for r in recipients:
        data.append(("to", r))
    return session.post(
        f"{MAIL_URL}/mail/json/receiverCheck.do",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        timeout=HTTP_TIMEOUT,
    )


def _report(j: dict, ext: str):
    """receiverCheck 응답에서 외부발송 판독에 중요한 필드만 뽑아 출력·해석."""
    for k in ["permission", "hasExternalReceiver", "hasExReceiver", "send_only",
              "receiver_count", "invalidReceiverList", "account_type",
              "max_receiver_count", "prohibit_word_preview"]:
        _log(f"    {k} = {j.get(k)}")
    perm = bool(j.get("permission"))
    invalid = str(j.get("invalidReceiverList") or [])
    hasext = bool(j.get("hasExternalReceiver") or j.get("hasExReceiver"))
    if perm and ext not in invalid:
        note = "외부 수신자 발송이 서버상 허용됨"
        if not hasext:
            note += " (단, hasExternalReceiver=false — 서버가 외부로 인식 못 했을 수 있음)"
        _log(f"    ⇒ {note}. 다음 단계: 결재 필요 여부 + 실제 send.do 테스트.")
    else:
        _log("    ⇒ 외부발송 차단(permission=false 또는 거부 목록) — 사내 자동 외부발송 불가 가능성 높음.")


def run_external_diag(argv=None) -> int:
    argv = list(argv or sys.argv)
    ext = _arg_value(argv, "--diag-external")
    frm = _arg_value(argv, "--from")

    _log("=" * 56)
    _log("사외(외부) 메일 발송 가능 여부 진단")
    _log(f"메일 서버: {MAIL_URL}")
    if not ext:
        _log("[중단] 외부 이메일이 없습니다. 예) KEPCO_RPA.exe --diag-external hong@naver.com")
        return 2
    _log(f"외부 테스트 주소: {ext}")
    _log(f"발신주소(fromaddr): {frm or '(빈 값)'}")

    session = auth.authenticate()
    if session is None:
        _log("[실패] PowerGate 인증 실패 — PowerGate 실행/사내망 연결 확인")
        return 1
    session.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": MAIL_URL,
        "Referer": f"{MAIL_URL}/mail/list.do",
        "X-Requested-With": "XMLHttpRequest",
    })

    # 1) 메일 세션 확인
    try:
        ts = int(datetime.now().timestamp() * 1000)
        r = session.get(f"{MAIL_URL}/common/json/session/check.do?_={ts}", timeout=HTTP_TIMEOUT)
        alive = r.json().get("alive")
        _log(f"session/check.do → alive={alive}")
        if not alive:
            _log("[실패] 메일 세션이 살아있지 않음(웹메일 SSO 로그인이 필요할 수 있음)")
            return 1
    except Exception as e:  # noqa: BLE001
        _log(f"[실패] session/check.do 오류: {e}")
        return 1

    # 2) receiverCheck — 외부 주소로 발송 권한 확인
    cases = [("외부주소만", [ext])]
    if frm:
        cases.append(("외부+본인", [ext, frm]))
    for label, recips in cases:
        _log("-" * 56)
        _log(f"receiverCheck.do [{label}] → {recips}")
        try:
            resp = _receiver_check(session, recips, frm)
            _log(f"HTTP {resp.status_code}")
            try:
                _report(resp.json(), ext)
            except ValueError:
                _log(f"[비JSON 응답] {resp.text[:300]}")
        except Exception as e:  # noqa: BLE001
            _log(f"[실패] receiverCheck.do 오류: {e}")

    _log("=" * 56)
    _log("진단 종료 — permission / hasExternalReceiver / invalidReceiverList 값을 공유해 주세요.")
    _log("결과 파일: 사외메일진단.log (실행 파일과 같은 폴더)")
    return 0


def run_send_external_test(argv=None) -> int:
    """외부 주소로 실제 테스트 메일을 1통 발송한다(운영과 동일한 send_mail 경로).

        KEPCO_RPA.exe --diag-send-external jaajung@naver.com --from 본인id@kepco.co.kr

    send.do 응답(code/send_result_txt)을 출력하고, 외부 받은편지함 도착 여부를
    사용자가 직접 확인하게 한다. 도착하면 사내에서 자동 외부발송이 가능하다는 확증."""
    argv = list(argv or sys.argv)
    ext = _arg_value(argv, "--diag-send-external")
    frm = _arg_value(argv, "--from")

    _log("=" * 56)
    _log("사외(외부) 메일 실제 발송 테스트")
    _log(f"메일 서버: {MAIL_URL}")
    if not ext:
        _log("[중단] 외부 이메일이 없습니다. 예) KEPCO_RPA.exe --diag-send-external hong@naver.com --from myid@kepco.co.kr")
        return 2
    if not frm:
        _log("[중단] --from <본인 kepco 이메일> 이 필요합니다(발신주소).")
        return 2

    session = auth.authenticate()
    if session is None:
        _log("[실패] PowerGate 인증 실패 — PowerGate 실행/사내망 연결 확인")
        return 1

    stamp = datetime.now().strftime("%m-%d %H:%M:%S")
    mail_config = {
        "from_email": frm,
        "from_name": _arg_value(argv, "--fromname", "외부발송 진단"),
        "recipients": [ext],
        "subject": f"[진단] 외부발송 테스트 {stamp}",
        "body": f"사내망에서 보낸 외부발송 테스트입니다. ({stamp})",
    }
    _log(f"발신: {mail_config['from_name']} <{frm}>  →  수신: {ext}")
    _log(f"제목: {mail_config['subject']}")

    res = mailer.send_mail(session, mail_config, attachment_paths=[])
    _log(f"send.do 결과: success={res.get('success')} / {res.get('message')}")
    resp = res.get("response") or {}
    for k in ["code", "send_result_txt", "send_result_txt_desc", "sent_mail_key", "save_mail_key"]:
        if k in resp:
            _log(f"    {k} = {resp.get(k)}")

    _log("-" * 56)
    if res.get("success"):
        _log(f"서버는 발송 성공(code=1)으로 응답했습니다.")
        _log(f"⇒ 이제 {ext} 받은편지함(스팸함 포함)에 실제로 도착했는지 꼭 확인하세요.")
        _log("   도착함 = 사내 자동 외부발송 가능. 안 옴 = 게이트웨이에서 보류/차단(결재 등) 가능성.")
    else:
        _log("서버가 발송 실패로 응답 — 위 send_result_txt 메시지로 원인(결재/차단 등) 확인.")
    _log("결과 파일: 사외메일진단.log (실행 파일과 같은 폴더)")
    return 0 if res.get("success") else 1


def run_send_file_test(argv=None) -> int:
    """최종 목표 검증 — 엑셀을 기본 다운로드해 여러 수신자(사내·사외 혼합)에게 첨부 발송.

        KEPCO_RPA.exe --diag-send-file --from 본인id@kepco.co.kr \
            --to "a@kepco.co.kr, b@naver.com, c@kepco.co.kr"
        (선택) --dept 4200 --date 2026-07-10 --subject "..." --body "..."

    본부·날짜는 지정 안 하면 저장된 설정(프리셋)을 따른다. 가공 없이 원본 엑셀을
    받아 첨부하고, send.do 응답을 출력한다. 수신자 각자 받은편지함 도착을 확인."""
    argv = list(argv or sys.argv)
    frm = _arg_value(argv, "--from")
    recipients = _parse_recipients(_arg_value(argv, "--to"))

    _log("=" * 56)
    _log("파일 첨부 + 다중/혼합 수신자 발송 테스트")
    _log(f"메일 서버: {MAIL_URL}")
    if not frm:
        _log("[중단] --from <본인 kepco 이메일> 이 필요합니다(발신주소).")
        return 2
    if not recipients:
        _log('[중단] --to "a@kepco.co.kr, b@naver.com" 처럼 수신자를 지정하세요.')
        return 2

    preset = config_store.load_config()
    dept = _arg_value(argv, "--dept") or preset.department_code
    if not dept:
        _log("[중단] 본부 코드가 없습니다. GUI에서 본부를 저장하거나 --dept 4200 처럼 지정하세요.")
        return 2
    date_str = _arg_value(argv, "--date")
    if date_str:
        fmts = date_formats(datetime.strptime(date_str, "%Y-%m-%d").date())
    else:
        d = resolve_target_date(preset.date_mode, preset.fixed_date, date.today())
        fmts = date_formats(d)

    ext_cnt = sum(1 for r in recipients if "@kepco.co.kr" not in r.lower())
    _log(f"본부 {dept} / 대상일 {fmts['ymd']}")
    _log(f"수신자 {len(recipients)}명 (사내 {len(recipients) - ext_cnt} · 사외 {ext_cnt}): {recipients}")

    # 1) 기본 엑셀 다운로드(가공 없이 원본)
    def _dl(session, date_from, department_code):
        return downloader.download_excel_to_dataframe(
            session, date_from=date_from, department_code=department_code, on_status=_log)

    _log("엑셀 다운로드 중…")
    session, df = run_auth_and_download(
        auth.authenticate, _dl, date_from=fmts["ymd"], department_code=dept, auth_attempts=3)
    if df is None:
        _log("[실패] 인증 또는 다운로드 실패 — 첨부할 파일을 못 만들었습니다.")
        return 1
    out = str(app_paths.output_dir() / f"{fmts['yymmdd']} 외부발송 파일테스트(원본).xlsx")
    try:
        write_excel(df, out, "")
    except (ValueError, OSError) as e:
        _log(f"[실패] 엑셀 저장 오류: {e}")
        return 1
    _log(f"다운로드·저장 완료: {out} ({len(df)}행 × {len(df.columns)}열)")

    # 2) 그 파일을 첨부해 다중/혼합 수신자에게 발송
    stamp = datetime.now().strftime("%m-%d %H:%M:%S")
    mail_config = {
        "from_email": frm,
        "from_name": _arg_value(argv, "--fromname", "외부발송 진단"),
        "recipients": recipients,
        "subject": _arg_value(argv, "--subject", f"[진단] 파일첨부 발송 테스트 {stamp}"),
        "body": _arg_value(argv, "--body",
                           f"엑셀 첨부 + 다중/혼합 수신자 발송 테스트입니다. ({stamp})"),
    }
    _log(f"발신: {mail_config['from_name']} <{frm}>")
    _log(f"제목: {mail_config['subject']}")

    res = mailer.send_mail(session, mail_config, attachment_paths=[out],
                           date_yymmdd=fmts["yymmdd"], date_yy_mm_dd=fmts["yy_mm_dd"])
    _log(f"send.do 결과: success={res.get('success')} / {res.get('message')}")
    resp = res.get("response") or {}
    for k in ["code", "send_result_txt", "send_result_txt_desc", "sent_mail_key", "save_mail_key"]:
        if k in resp:
            _log(f"    {k} = {resp.get(k)}")

    _log("-" * 56)
    if res.get("success"):
        _log("서버는 발송 성공(code=1)으로 응답했습니다.")
        _log("⇒ 수신자 각자(사내·사외) 받은편지함에서 엑셀 첨부가 실제로 왔는지 확인하세요.")
        _log("   모두 도착 = 최종 목표(혼합 수신자 + 첨부 자동발송) 달성.")
    else:
        _log("서버가 발송 실패로 응답 — 위 send_result_txt 로 원인(첨부 용량/결재/차단 등) 확인.")
    _log("결과 파일: 사외메일진단.log (실행 파일과 같은 폴더)")
    return 0 if res.get("success") else 1
