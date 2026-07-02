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
            session, df = run_auth_and_download(
                authenticate=auth.authenticate,
                download=downloader.download_excel_to_dataframe,
                date_from=self._date_from,
                department_code=self._dept,
                on_status=self.status.emit,
            )
            if df is None:
                self.failed.emit(
                    "인증+다운로드에 실패했습니다.\n"
                    "· PowerGate 실행 여부\n· 사내망 연결\n· 해당 날짜 데이터 유무를 확인하세요."
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
