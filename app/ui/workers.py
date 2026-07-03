"""네트워크 작업용 QThread 워커 (UI 스레드 비차단)."""

from PySide6.QtCore import QThread, Signal

from app.core.pipeline import run_auth_and_download
from app.adapters import auth, downloader, mailer


class DownloadWorker(QThread):
    status = Signal(str)
    done = Signal(object, object)   # (session, df)
    failed = Signal(str)

    def __init__(self, date_from: str, department_code: str):
        super().__init__()
        self._date_from = date_from
        self._dept = department_code

    def run(self):
        try:
            # 인증은 1회(느린 엑셀 생성은 넉넉한 타임아웃으로 대기). 단, 서버가 데이터
            # 대신 열 1개짜리 오류/안내 페이지를 주면 downloader가 같은 세션으로 빠르게
            # 재요청한다(재인증 불필요 — 서버측 일시 문제 대응).
            self.status.emit("인증 중…")

            def _download(session, date_from, department_code):
                # 다운로드 진단 메시지를 UI 로그로 그대로 전달
                return downloader.download_excel_to_dataframe(
                    session, date_from=date_from, department_code=department_code,
                    on_status=self.status.emit)

            session, df = run_auth_and_download(
                authenticate=auth.authenticate,
                download=_download,
                date_from=self._date_from,
                department_code=self._dept,
                max_retries=1,
            )
            if df is None:
                self.failed.emit(
                    "인증 또는 다운로드에 실패했습니다.\n"
                    "· PowerGate 실행\n· 사내망 연결\n· 해당 날짜 데이터 유무를 확인한 뒤 "
                    "다시 [실행]하세요."
                )
            else:
                self.done.emit(session, df)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(f"예상치 못한 오류: {e}")


class MailWorker(QThread):
    status = Signal(str)
    done = Signal(dict)
    failed = Signal(str)

    def __init__(self, session, mail_config: dict, attachment_path: str,
                 date_yymmdd: str, date_yy_mm_dd: str):
        super().__init__()
        self._session = session
        self._mail_config = mail_config
        self._attachment = attachment_path
        self._yymmdd = date_yymmdd
        self._yy_mm_dd = date_yy_mm_dd

    def run(self):
        try:
            self.status.emit("메일 전송 중…")
            result = mailer.send_bizmail(
                session=self._session,
                mail_config=self._mail_config,
                attachment_paths=[self._attachment] if self._attachment else [],
                date_yymmdd=self._yymmdd,
                date_yy_mm_dd=self._yy_mm_dd,
            )
            self.done.emit(result)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(f"메일 전송 오류: {e}")
