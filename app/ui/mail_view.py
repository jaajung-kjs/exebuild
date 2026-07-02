"""③ 메일 설정 뷰 (베타) — 발신·수신·제목·본문(서식) 편집·저장.

설정 편집 전용. 실제 발송은 ①실행 화면에서 '3. 메일 발송'을 체크해 실행한다.
본문은 굵기·글씨색·크기 서식을 지원하는 리치텍스트(HTML)로 저장된다."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCharFormat, QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPlainTextEdit, QTextEdit, QComboBox, QPushButton, QLabel,
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
        self.from_name = QLineEdit(); self.from_name.setMinimumHeight(34)
        self.from_email = QLineEdit(); self.from_email.setMinimumHeight(34)
        self.recipients = QPlainTextEdit()
        self.recipients.setPlaceholderText("수신자 이메일 (줄바꿈으로 여러 명)")
        self.recipients.setFixedHeight(76)
        self.subject = QLineEdit(); self.subject.setMinimumHeight(34)

        # 본문 — 서식 툴바 + 리치텍스트
        body_box = QVBoxLayout()
        body_box.setSpacing(6)
        body_box.addLayout(self._format_toolbar())
        self.body = QTextEdit()
        self.body.setMinimumHeight(180)
        self.body.setAcceptRichText(True)
        body_box.addWidget(self.body)

        form.addRow("발신자 이름", self.from_name)
        form.addRow("발신자 이메일", self.from_email)
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
        bar = QHBoxLayout()
        bar.setSpacing(6)
        self.bold_btn = QPushButton("B", objectName="Ghost")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedWidth(38)
        f = self.bold_btn.font(); f.setBold(True); self.bold_btn.setFont(f)
        self.bold_btn.clicked.connect(self._toggle_bold)

        self.size_combo = QComboBox()
        self.size_combo.addItems(FONT_SIZES)
        self.size_combo.setCurrentText("12")
        self.size_combo.setFixedWidth(64)
        self.size_combo.activated.connect(self._set_size)

        self.color_btn = QPushButton("글씨 색", objectName="Ghost")
        self.color_btn.clicked.connect(self._pick_color)

        bar.addWidget(QLabel("서식:", objectName="Conn"))
        bar.addWidget(self.bold_btn)
        bar.addWidget(QLabel("크기", objectName="Conn"))
        bar.addWidget(self.size_combo)
        bar.addWidget(self.color_btn)
        bar.addStretch(1)
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
        from PySide6.QtWidgets import QColorDialog
        c = QColorDialog.getColor(QColor("#000000"), self, "글씨 색")
        if c.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(c)
            self._merge(fmt)

    # ---------- 프리셋 연동 ----------
    def apply_preset(self, preset):
        self.from_name.setText(preset.mail_from_name)
        self.from_email.setText(preset.mail_from_email)
        self.recipients.setPlainText("\n".join(preset.mail_recipients))
        self.subject.setText(preset.mail_subject)
        body = preset.mail_body or ""
        if "<html" in body.lower() or "<body" in body.lower():
            self.body.setHtml(body)
        else:
            self.body.setPlainText(body)

    def write_into(self, preset):
        preset.mail_from_name = self.from_name.text().strip()
        preset.mail_from_email = self.from_email.text().strip()
        preset.mail_recipients = [
            ln.strip() for ln in self.recipients.toPlainText().splitlines() if ln.strip()
        ]
        preset.mail_subject = self.subject.text()
        # 본문이 비어 있으면 빈 문자열, 아니면 서식 포함 HTML로 저장
        preset.mail_body = "" if not self.body.toPlainText().strip() else self.body.toHtml()
