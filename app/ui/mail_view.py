"""③ 메일 뷰 — 수신자·제목·본문 입력 후 발송."""

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPlainTextEdit, QPushButton, QLabel, QMessageBox,
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
        v.setContentsMargins(32, 28, 32, 28)
        v.setSpacing(6)
        v.addWidget(QLabel("메일 전송 (베타)", objectName="H1"))
        v.addWidget(QLabel("선택 기능입니다. 저장한 엑셀을 첨부해 발송합니다. 제목·본문의 {DATE}는 대상 날짜로 치환됩니다.",
                           objectName="Hint"))
        v.addSpacing(16)

        card = QFrame(objectName="Card")
        form = QFormLayout(card)
        form.setContentsMargins(22, 22, 22, 22)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.from_name = QLineEdit()
        self.from_name.setMinimumHeight(34)
        self.from_email = QLineEdit()
        self.from_email.setMinimumHeight(34)
        self.recipients = QPlainTextEdit()
        self.recipients.setPlaceholderText("수신자 이메일 (줄바꿈으로 여러 명)")
        self.recipients.setFixedHeight(76)
        self.subject = QLineEdit()
        self.subject.setMinimumHeight(34)
        self.body = QPlainTextEdit()
        self.body.setMinimumHeight(150)
        form.addRow("발신자 이름", self.from_name)
        form.addRow("발신자 이메일", self.from_email)
        form.addRow("수신자", self.recipients)
        form.addRow("제목", self.subject)
        form.addRow("본문", self.body)
        v.addWidget(card)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.send_btn = QPushButton("메일 발송", objectName="Primary")
        self.send_btn.setMinimumHeight(38)
        self.send_btn.clicked.connect(self._send)
        btn_row.addWidget(self.send_btn)
        v.addSpacing(6)
        v.addLayout(btn_row)

        v.addSpacing(14)
        v.addWidget(QLabel("진행 상태", objectName="SectionLabel"))
        v.addSpacing(4)
        self.log = QPlainTextEdit(objectName="StatusLog", readOnly=True)
        self.log.setPlaceholderText("대기 중 — [메일 발송]을 누르면 전송 진행 상태가 표시됩니다.")
        self.log.setFixedHeight(96)
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
