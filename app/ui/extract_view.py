"""① 추출 뷰 — 날짜·본부 선택 후 다운로드."""

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox,
    QDateEdit, QPushButton, QLabel, QPlainTextEdit,
)

from app.core import departments
from app.core.date_util import resolve_default_date
from app.ui.workers import DownloadWorker


class ExtractView(QWidget):
    def __init__(self, state, main):
        super().__init__()
        self.state = state
        self.main = main
        self._worker = None
        self._offset = 1

        v = QVBoxLayout(self)
        v.setContentsMargins(32, 28, 32, 28)
        v.setSpacing(6)
        v.addWidget(QLabel("데이터 추출", objectName="H1"))
        v.addWidget(QLabel("대상 날짜와 본부를 선택해 점검 데이터를 불러옵니다.", objectName="Hint"))
        v.addSpacing(16)

        # 입력 카드
        card = QFrame(objectName="Card")
        card.setMaximumWidth(580)
        form = QFormLayout(card)
        form.setContentsMargins(22, 22, 22, 22)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setMinimumHeight(34)
        self._reset_date()

        self.dept_combo = QComboBox()
        self.dept_combo.setMinimumHeight(34)
        for group, deps in departments.grouped().items():
            self.dept_combo.addItem(f"── {group} ──")
            idx = self.dept_combo.count() - 1
            self.dept_combo.model().item(idx).setEnabled(False)
            for d in deps:
                self.dept_combo.addItem(d.name, d.code)

        form.addRow("대상 날짜", self.date_edit)
        form.addRow("본부", self.dept_combo)
        v.addWidget(card)

        # 주요 액션 (우측 정렬)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.btn = QPushButton("불러오기", objectName="Primary")
        self.btn.setMinimumHeight(38)
        self.btn.clicked.connect(self._start)
        btn_row.addWidget(self.btn)
        v.addSpacing(6)
        v.addLayout(btn_row)

        v.addSpacing(14)
        v.addWidget(QLabel("진행 상태", objectName="SectionLabel"))
        v.addSpacing(4)
        self.log = QPlainTextEdit(objectName="StatusLog", readOnly=True)
        self.log.setPlaceholderText("대기 중 — [불러오기]를 누르면 인증·다운로드 진행 상태가 표시됩니다.")
        self.log.setFixedHeight(200)
        v.addWidget(self.log)
        v.addStretch(1)

    def _reset_date(self):
        d = resolve_default_date(date.today(), self._offset)
        self.date_edit.setDate(QDate(d.year, d.month, d.day))

    # ---- 프리셋 연동 ----
    def apply_preset(self, preset):
        self._offset = preset.default_date_offset
        self._reset_date()
        i = self.dept_combo.findData(preset.department_code)
        if i >= 0:
            self.dept_combo.setCurrentIndex(i)

    def write_into(self, preset):
        preset.department_code = self.dept_combo.currentData() or ""
        preset.default_date_offset = self._offset

    # ---- 다운로드 ----
    def _start(self):
        code = self.dept_combo.currentData()
        if not code:
            self._append("본부를 선택하세요.")
            return
        qd = self.date_edit.date()
        date_from = f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"
        self.state.target_date = date(qd.year(), qd.month(), qd.day())
        self.state.preset.department_code = code
        self.btn.setEnabled(False)
        self.log.clear()
        self._append(f"대상: {date_from} / {self.dept_combo.currentText()}")

        self._worker = DownloadWorker(date_from, code)
        self._worker.status.connect(self._append)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_done(self, session, df):
        self.state.session = session
        self.state.df = df
        self._append(f"✅ 완료: {len(df)}행 × {len(df.columns)}열")
        self.btn.setEnabled(True)
        self.main.configure.load_dataframe()
        self.main.goto(1)

    def _on_failed(self, msg):
        self._append("❌ " + msg)
        self.btn.setEnabled(True)

    def _append(self, text):
        self.log.appendPlainText(text)
