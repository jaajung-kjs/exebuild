"""① 추출 뷰 — 날짜·본부 선택 후 다운로드."""

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QDateEdit, QPushButton,
    QLabel, QPlainTextEdit,
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
        v.setContentsMargins(28, 24, 28, 24)
        v.addWidget(QLabel("① 데이터 추출", objectName="H1"))
        v.addWidget(QLabel("날짜와 본부를 선택하고 불러오세요.", objectName="Hint"))

        form = QFormLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self._reset_date()

        self.dept_combo = QComboBox()
        for group, deps in departments.grouped().items():
            self.dept_combo.addItem(f"── {group} ──")
            idx = self.dept_combo.count() - 1
            self.dept_combo.model().item(idx).setEnabled(False)
            for d in deps:
                self.dept_combo.addItem(d.name, d.code)

        form.addRow("대상 날짜", self.date_edit)
        form.addRow("본부", self.dept_combo)
        v.addLayout(form)

        self.btn = QPushButton("불러오기")
        self.btn.clicked.connect(self._start)
        v.addWidget(self.btn)

        self.log = QPlainTextEdit(objectName="StatusLog", readOnly=True)
        v.addWidget(self.log, 1)

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
