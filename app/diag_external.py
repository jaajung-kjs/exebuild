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

import sys
from datetime import datetime

from app.adapters import auth
from app.adapters.config import MAIL_URL, HTTP_TIMEOUT
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
