"""① 실행 뷰 — 날짜·본부 선택 후 원하는 단계만 골라 한 번에 실행.

프로그램의 유일한 실행 진입점. 다운로드·저장·메일 발송이 모두 여기서 일어난다.
(②설정·③메일 탭은 설정 편집·저장만 담당)"""

import os
import subprocess
import sys
from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox,
    QDateEdit, QPushButton, QLabel, QPlainTextEdit, QCheckBox, QMessageBox,
)

from app.core import departments
from app.core.engine import process
from app.core.excel_writer import write_excel
from app.core.mail_config import preset_to_mail_config
from app.core.date_util import resolve_default_date, date_formats
from app import app_paths
from app.ui.workers import DownloadWorker, MailWorker


class ExtractView(QWidget):
    def __init__(self, state, main):
        super().__init__()
        self.state = state
        self.main = main
        self._worker = None
        self._mail_worker = None
        self._offset = 1
        self._do_process = True
        self._do_mail = False

        v = QVBoxLayout(self)
        v.setContentsMargins(32, 28, 32, 28)
        v.setSpacing(6)
        v.addWidget(QLabel("실행", objectName="H1"))
        v.addWidget(QLabel("날짜·본부를 고르고, 원하는 작업만 체크해 한 번에 실행합니다.",
                           objectName="Hint"))
        v.addSpacing(16)

        # 대상 카드
        card = QFrame(objectName="Card")
        card.setMaximumWidth(640)
        form = QFormLayout(card)
        form.setContentsMargins(22, 20, 22, 20)
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

        # 실행할 작업 카드
        steps = QFrame(objectName="Card")
        steps.setMaximumWidth(640)
        sv = QVBoxLayout(steps)
        sv.setContentsMargins(22, 18, 22, 18)
        sv.setSpacing(10)
        sv.addWidget(QLabel("실행할 작업", objectName="CardTitle"))
        sv.addWidget(QFrame(objectName="CardDivider"))
        c1 = QCheckBox("1. 데이터 불러오기  (필수)")
        c1.setChecked(True)
        c1.setEnabled(False)
        self.chk_process = QCheckBox("2. 설정(정렬·강조·필터) 적용해서 저장")
        self.chk_process.setChecked(True)
        self.chk_mail = QCheckBox("3. 메일 발송 (베타)")
        for c in (c1, self.chk_process, self.chk_mail):
            sv.addWidget(c)
        sv.addWidget(QLabel(
            "· 2번을 끄면 원본 그대로 저장합니다.\n"
            "· 설정은 ②·③ 탭에서 정하고 [설정 저장]하면 자동 저장·복원됩니다. "
            "(설정이 없으면 실행 후 설정 화면으로 안내합니다.)",
            objectName="Hint"))
        v.addWidget(steps)

        # 실행 버튼
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.btn = QPushButton("▶ 실행", objectName="Primary")
        self.btn.setMinimumHeight(40)
        self.btn.setMinimumWidth(160)
        self.btn.clicked.connect(self._run)
        btn_row.addWidget(self.btn)
        v.addSpacing(6)
        v.addLayout(btn_row)

        v.addSpacing(14)
        v.addWidget(QLabel("진행 상태", objectName="SectionLabel"))
        v.addSpacing(4)
        self.log = QPlainTextEdit(objectName="StatusLog", readOnly=True)
        self.log.setPlaceholderText("대기 중 — [실행]을 누르면 진행 상태가 표시됩니다.")
        self.log.setFixedHeight(170)
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

    # ---- 실행 ----
    def _run(self):
        code = self.dept_combo.currentData()
        if not code:
            self._append("본부를 선택하세요.")
            return
        qd = self.date_edit.date()
        date_from = f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"
        self.state.target_date = date(qd.year(), qd.month(), qd.day())
        self.state.preset.department_code = code
        self._do_process = self.chk_process.isChecked()
        self._do_mail = self.chk_mail.isChecked()
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
        self.btn.setEnabled(True)
        self._append(f"✅ 불러오기 완료: {len(df)}행 × {len(df.columns)}열")
        self.main.configure.load_dataframe()   # ②탭 미리보기·설정 위젯 채움

        if not self._do_process:
            self._append("원본 그대로 저장합니다…")
            self._finish(self._save_raw())
            return
        if self._has_config():
            self.main.configure.write_into(self.state.preset)   # 최신 설정 반영
            self._append("설정을 적용해 저장합니다…")
            self._finish(self._save_processed())
        else:
            self._append("적용할 설정이 없습니다 → ②설정 탭에서 규칙을 만들고 "
                         "[설정 저장] 후 다시 실행하세요.")
            self.main.goto(1)

    def _has_config(self):
        p = self.state.preset
        return bool(p.rules or p.filters or p.drop_columns or p.sheet_split_column
                    or (p.sort and p.sort != "none"))

    # ---- 저장 실행 ----
    def _out_path(self, suffix):
        fmts = date_formats(self.state.target_date or date.today())
        return str(app_paths.output_dir() / f"{fmts['yymmdd']} 공사현장 점검 {suffix}.xlsx")

    def _write(self, df, out, split):
        try:
            write_excel(df, out, split)
            return True
        except (PermissionError, OSError) as e:
            self._append(f"❌ 저장 실패: {e}")
            QMessageBox.critical(self, "저장 실패",
                                 f"파일 저장에 실패했습니다.\n파일이 열려 있으면 닫고 다시 시도하세요.\n{e}")
            return False

    def _save_processed(self):
        try:
            processed = process(self.state.df, self.state.preset)
        except ValueError as e:
            self._append("❌ " + str(e))
            QMessageBox.critical(self, "저장 실패", str(e))
            return None
        out = self._out_path("우선순위 리스트")
        if self._write(processed, out, self.state.preset.sheet_split_column):
            self.state.output_path = out
            return out
        return None

    def _save_raw(self):
        out = self._out_path("원본")
        if self._write(self.state.df, out, ""):
            self.state.output_path = out
            return out
        return None

    def _finish(self, out):
        if not out:
            return
        self._append(f"✅ 저장 완료: {out}")
        if self._do_mail:
            self._send_mail(out)
        else:
            self._after_save(out)

    # ---- 메일 실행 (③ 체크 시) ----
    def _send_mail(self, attachment):
        self.main.mail.write_into(self.state.preset)   # ③탭 입력값 반영
        mc = preset_to_mail_config(self.state.preset)
        if not mc.get("recipients"):
            self._append("⚠️ 메일 수신자가 없어 발송을 건너뜁니다. (③메일 탭에서 설정 후 저장)")
            self._after_save(attachment)
            return
        self._append("메일 발송 중…")
        fmts = date_formats(self.state.target_date or date.today())
        self._mail_worker = MailWorker(self.state.session, mc, attachment,
                                       fmts["yymmdd"], fmts["yy_mm_dd"])
        self._mail_worker.status.connect(self._append)
        self._mail_worker.done.connect(self._on_mail_done)
        self._mail_worker.failed.connect(lambda m: self._append("❌ " + m))
        self._mail_worker.start()

    def _on_mail_done(self, result):
        if result.get("success"):
            self._append("✅ 메일 발송 완료")
            QMessageBox.information(self, "완료", "저장 및 메일 발송이 완료되었습니다.")
        else:
            msg = result.get("message", "")
            self._append("❌ 메일 발송 실패: " + msg)
            QMessageBox.warning(self, "메일 실패",
                                f"메일 발송 실패: {msg}\n엑셀은 저장되어 있습니다.")

    def _after_save(self, path):
        box = QMessageBox(self)
        box.setWindowTitle("저장 완료")
        box.setText(f"엑셀을 저장했습니다.\n{path}")
        open_btn = box.addButton("폴더 열기", QMessageBox.ActionRole)
        box.addButton("닫기", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() == open_btn:
            self._open_folder(path)

    @staticmethod
    def _open_folder(path):
        folder = os.path.dirname(path)
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass

    def _on_failed(self, msg):
        self._append("❌ " + msg)
        self.btn.setEnabled(True)

    def _append(self, text):
        self.log.appendPlainText(text)
