"""③ 메일 설정 뷰 — 수신자·제목·본문(서식) 편집·저장.

설정 편집 전용. 실제 발송은 ①실행 화면에서 '3. 메일 발송'을 체크해 실행한다.
발신자는 SSO 로그인된 사용자로 자동 지정된다. 본문은 굵기·글씨색·크기 서식을
지원하는 리치텍스트(HTML)로 저장된다."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCharFormat, QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPlainTextEdit, QTextEdit, QComboBox, QPushButton, QLabel, QColorDialog,
)

FONT_SIZES = ["10", "11", "12", "14", "16", "18", "20", "24", "28"]


class MailView(QWidget):
    def __init__(self, state, main):
        super().__init__()
        self.state = state
        self.main = main

        v = QVBoxLayout(self)
        v.setContentsMargins(32, 28, 32, 28)
        v.setSpacing(6)
        v.addWidget(QLabel("메일 설정", objectName="H1"))
        v.addWidget(QLabel(
            "수신자·제목·본문을 정해 저장해 두면, ①실행 화면에서 ‘3. 메일 발송’을 "
            "체크했을 때 이 설정으로 발송됩니다. 제목·본문의 {DATE}는 대상 날짜로 치환됩니다.",
            objectName="Hint"))
        v.addSpacing(16)

        card = QFrame(objectName="Card")
        form = QFormLayout(card)
        form.setContentsMargins(22, 22, 22, 22)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        sender_note = QLabel("현재 SSO 로그인된 사용자 메일로 자동 발송됩니다.", objectName="Hint")
        self.recipients = QPlainTextEdit()
        self.recipients.setPlaceholderText("수신자 이메일 (줄바꿈으로 여러 명)")
        self.recipients.setFixedHeight(76)
        self.subject = QLineEdit()
        self.subject.setMinimumHeight(34)

        body_box = QVBoxLayout()
        body_box.setSpacing(6)
        body_box.addWidget(self._format_toolbar())
        self.body = QTextEdit()
        self.body.setMinimumHeight(190)
        self.body.setAcceptRichText(True)
        body_box.addWidget(self.body)

        form.addRow("발신자", sender_note)
        form.addRow("수신자", self.recipients)
        form.addRow("제목", self.subject)
        form.addRow("본문", body_box)
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

    # ---------- 서식 툴바 ----------
    def _format_toolbar(self):
        bar = QFrame(objectName="Toolbar")
        h = QHBoxLayout(bar)
        h.setContentsMargins(6, 4, 6, 4)
        h.setSpacing(6)
        self.bold_btn = QPushButton("B", objectName="ToolBtn")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedSize(34, 30)
        f = self.bold_btn.font(); f.setBold(True); f.setPointSize(13); self.bold_btn.setFont(f)
        self.bold_btn.clicked.connect(self._toggle_bold)

        self.color_btn = QPushButton("글씨 색", objectName="ToolBtn")
        self.color_btn.setMinimumHeight(30)
        self.color_btn.clicked.connect(self._pick_color)

        self.size_combo = QComboBox()
        self.size_combo.addItems(FONT_SIZES)
        self.size_combo.setCurrentText("12")
        self.size_combo.setFixedWidth(64)
        self.size_combo.setMinimumHeight(30)
        self.size_combo.setToolTip("글씨 크기")
        self.size_combo.activated.connect(self._set_size)

        h.addWidget(self.bold_btn)
        h.addWidget(self.color_btn)
        h.addWidget(QLabel("크기", objectName="Conn"))
        h.addWidget(self.size_combo)
        h.addStretch(1)
        return bar

    def _merge(self, fmt):
        cursor = self.body.textCursor()
        cursor.mergeCharFormat(fmt)
        self.body.mergeCurrentCharFormat(fmt)
        self.body.setFocus()

    def _toggle_bold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold if self.bold_btn.isChecked() else QFont.Normal)
        self._merge(fmt)

    def _set_size(self):
        try:
            pt = float(self.size_combo.currentText())
        except ValueError:
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(pt)
        self._merge(fmt)

    def _pick_color(self):
        c = QColorDialog.getColor(QColor("#000000"), self, "글씨 색")
        if c.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(c)
            self._merge(fmt)

    # ---------- 프리셋 연동 ----------
    def apply_preset(self, preset):
        self.recipients.setPlainText("\n".join(preset.mail_recipients))
        self.subject.setText(preset.mail_subject)
        body = preset.mail_body or ""
        if "<html" in body.lower() or "<body" in body.lower():
            self.body.setHtml(body)
        else:
            self.body.setPlainText(body)

    def write_into(self, preset):
        # 발신자는 SSO 로그인 사용자 기준 → 서버가 채움
        preset.mail_from_name = ""
        preset.mail_from_email = ""
        preset.mail_recipients = [
            ln.strip() for ln in self.recipients.toPlainText().splitlines() if ln.strip()
        ]
        preset.mail_subject = self.subject.text()
        preset.mail_body = "" if not self.body.toPlainText().strip() else self.body.toHtml()
