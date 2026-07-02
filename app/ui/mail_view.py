"""③ 메일 설정 뷰 (베타) — 발신·수신·제목·본문 편집·저장.

설정 편집 전용. 실제 발송은 ①실행 화면에서 '3. 메일 발송'을 체크해 실행한다."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPlainTextEdit, QPushButton, QLabel,
)


class MailView(QWidget):
    def __init__(self, state, main):
        super().__init__()
        self.state = state
        self.main = main

        v = QVBoxLayout(self)
        v.setContentsMargins(32, 28, 32, 28)
        v.setSpacing(6)
        v.addWidget(QLabel("메일 설정 (베타)", objectName="H1"))
        v.addWidget(QLabel(
            "선택 기능입니다. 여기서 수신자·제목·본문을 정해 저장해 두면, "
            "①실행 화면에서 ‘3. 메일 발송’을 체크했을 때 이 설정으로 발송됩니다. "
            "제목·본문의 {DATE}는 대상 날짜로 치환됩니다.", objectName="Hint"))
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

        v.addSpacing(10)
        bottom = QHBoxLayout()
        bottom.addWidget(QLabel("발송은 ①실행 화면에서 ‘3. 메일 발송’ 체크 후 실행합니다.",
                                objectName="Hint"))
        bottom.addStretch(1)
        self.save_btn = QPushButton("설정 저장", objectName="Primary")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(lambda: self.main._save_config())
        bottom.addWidget(self.save_btn)
        v.addLayout(bottom)
        v.addStretch(1)

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
