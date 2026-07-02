"""③ 메일 뷰 — 수신자·제목·본문 입력 후 발송."""

from datetime import date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPlainTextEdit,
    QPushButton, QLabel, QMessageBox,
)

from app.core.mail_config import preset_to_mail_config
from app.core.date_util import date_formats
from app.ui.workers import MailWorker


class MailView(QWidget):
    def __init__(self, state, main):
        super().__init__()
        self.state = state
        self.main = main
        self._worker = None

        v = QVBoxLayout(self)
        v.setContentsMargins(28, 24, 28, 24)
        v.addWidget(QLabel("③ 메일 전송", objectName="H1"))
        v.addWidget(QLabel("생성된 엑셀을 첨부해 발송합니다. 제목/본문의 {DATE}는 대상 날짜로 치환됩니다.",
                           objectName="Hint"))

        form = QFormLayout()
        self.from_name = QLineEdit()
        self.from_email = QLineEdit()
        self.recipients = QPlainTextEdit()
        self.recipients.setPlaceholderText("수신자 이메일 (줄바꿈으로 여러 명)")
        self.recipients.setFixedHeight(80)
        self.subject = QLineEdit()
        self.body = QPlainTextEdit()
        form.addRow("발신자 이름", self.from_name)
        form.addRow("발신자 이메일", self.from_email)
        form.addRow("수신자", self.recipients)
        form.addRow("제목", self.subject)
        form.addRow("본문", self.body)
        v.addLayout(form)

        self.send_btn = QPushButton("메일 발송")
        self.send_btn.clicked.connect(self._send)
        v.addWidget(self.send_btn)

        self.log = QPlainTextEdit(objectName="StatusLog", readOnly=True)
        self.log.setFixedHeight(90)
        v.addWidget(self.log)

    def apply_preset(self, preset):
        self.from_name.setText(preset.mail_from_name)
        self.from_email.setText(preset.mail_from_email)
        self.recipients.setPlainText("\n".join(preset.mail_recipients))
        self.subject.setText(preset.mail_subject)
        self.body.setPlainText(preset.mail_body)

    def write_into(self, preset):
        preset.mail_from_name = self.from_name.text().strip()
        preset.mail_from_email = self.from_email.text().strip()
        preset.mail_recipients = [
            ln.strip() for ln in self.recipients.toPlainText().splitlines() if ln.strip()
        ]
        preset.mail_subject = self.subject.text()
        preset.mail_body = self.body.toPlainText()

    def _send(self):
        if not self.state.output_path:
            QMessageBox.warning(self, "메일", "먼저 ②설정에서 엑셀을 생성하세요.")
            return
        self.write_into(self.state.preset)
        mc = preset_to_mail_config(self.state.preset)
        if not mc["recipients"]:
            QMessageBox.warning(self, "메일", "수신자를 입력하세요.")
            return
        d = getattr(self.state, "target_date", None) or date.today()
        fmts = date_formats(d)
        self.send_btn.setEnabled(False)
        self.log.clear()
        self._worker = MailWorker(self.state.session, mc, self.state.output_path,
                                  fmts["yymmdd"], fmts["yy_mm_dd"])
        self._worker.status.connect(self.log.appendPlainText)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_done(self, result):
        self.send_btn.setEnabled(True)
        if result.get("success"):
            self.log.appendPlainText("✅ 발송 완료")
            QMessageBox.information(self, "메일", "발송 완료!")
        else:
            msg = result.get("message", "실패")
            self.log.appendPlainText("❌ " + msg)
            QMessageBox.warning(self, "메일", f"발송 실패: {msg}\n엑셀은 저장되어 있습니다:\n{self.state.output_path}")

    def _on_failed(self, msg):
        self.send_btn.setEnabled(True)
        self.log.appendPlainText("❌ " + msg)
