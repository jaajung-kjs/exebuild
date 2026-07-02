"""② 설정 뷰 — drop·규칙·필터·색·정렬 + 샘플 미리보기."""

from datetime import date

from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
    QSpinBox, QColorDialog, QMessageBox, QGroupBox, QFormLayout, QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

_SWATCH_QSS = "background:{c}; color:#1B2430; border:1px solid rgba(0,0,0,0.18); border-radius:6px; padding:3px 8px; font-weight:700;"

from app.core.engine import process
from app.core.excel_writer import write_excel
from app.core.settings import Rule, Filter
from app.core.date_util import date_formats
from app import app_paths

PREVIEW_ROWS = 20
FILTER_OPS = ["not_null", "equals", "contains", "not_equals"]


class ConfigureView(QWidget):
    def __init__(self, state, main):
        super().__init__()
        self.state = state
        self.main = main

        v = QVBoxLayout(self)
        v.setContentsMargins(32, 28, 32, 28)
        v.setSpacing(6)
        v.addWidget(QLabel("설정", objectName="H1"))
        v.addWidget(QLabel("컬럼 제외·우선순위 규칙·필터를 지정하고 엑셀을 생성합니다.", objectName="Hint"))
        v.addSpacing(16)

        top = QHBoxLayout()
        top.setSpacing(16)
        top.addWidget(self._drop_box(), 2)
        top.addWidget(self._rules_box(), 6)
        top.addWidget(self._filters_box(), 3)
        v.addLayout(top)

        v.addSpacing(14)
        opt_card = QFrame(objectName="Card")
        opt = QFormLayout(opt_card)
        opt.setContentsMargins(18, 16, 18, 16)
        opt.setSpacing(12)
        opt.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.sort_combo = QComboBox()
        self.sort_combo.setMinimumHeight(32)
        self.split_combo = QComboBox()
        self.split_combo.setMinimumHeight(32)
        opt.addRow("정렬", self.sort_combo)
        opt.addRow("시트 분리 열", self.split_combo)
        v.addWidget(opt_card)

        v.addSpacing(14)
        v.addWidget(QLabel(f"샘플 미리보기 · 상위 {PREVIEW_ROWS}행", objectName="SectionLabel"))
        v.addSpacing(4)
        self.preview = QTableWidget()
        self.preview.setAlternatingRowColors(True)
        self.preview.verticalHeader().setVisible(False)
        self.preview.setEditTriggers(QTableWidget.NoEditTriggers)
        self.preview.setSelectionMode(QTableWidget.NoSelection)
        self.preview.horizontalHeader().setStretchLastSection(True)
        v.addWidget(self.preview, 1)

        v.addSpacing(12)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.gen_btn = QPushButton("엑셀 생성", objectName="Primary")
        self.gen_btn.setMinimumHeight(38)
        self.gen_btn.clicked.connect(self._generate)
        btn_row.addWidget(self.gen_btn)
        v.addLayout(btn_row)

    # ---- 섹션 위젯 ----
    def _drop_box(self):
        box = QGroupBox("컬럼 Drop  ·  체크 시 제외")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(10, 6, 10, 10)
        self.drop_list = QListWidget(objectName="DropList")
        lay.addWidget(self.drop_list)
        return box

    def _rules_box(self):
        box = QGroupBox("우선순위 규칙")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(10, 6, 10, 10)
        lay.setSpacing(8)
        self.rules_table = QTableWidget(0, 5)
        self.rules_table.setHorizontalHeaderLabels(["열", "키워드", "매칭", "순위", "색"])
        self.rules_table.verticalHeader().setVisible(False)
        self.rules_table.setSelectionMode(QTableWidget.NoSelection)
        rh = self.rules_table.horizontalHeader()
        rh.setSectionResizeMode(0, QHeaderView.Fixed)
        rh.setSectionResizeMode(1, QHeaderView.Stretch)
        rh.setSectionResizeMode(2, QHeaderView.Fixed)
        rh.setSectionResizeMode(3, QHeaderView.Fixed)
        rh.setSectionResizeMode(4, QHeaderView.Fixed)
        for _c, _w in ((0, 92), (2, 98), (3, 58), (4, 44)):
            self.rules_table.setColumnWidth(_c, _w)
        lay.addWidget(self.rules_table)
        row = QHBoxLayout()
        row.setSpacing(8)
        add = QPushButton("＋ 규칙 추가", objectName="Ghost")
        rm = QPushButton("－ 선택 삭제", objectName="Ghost")
        add.clicked.connect(lambda: self._add_rule_row())
        rm.clicked.connect(lambda: self._remove_row(self.rules_table))
        row.addWidget(add); row.addWidget(rm); row.addStretch(1)
        lay.addLayout(row)
        return box

    def _filters_box(self):
        box = QGroupBox("필터  ·  모두 만족(AND)")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(10, 6, 10, 10)
        lay.setSpacing(8)
        self.filters_table = QTableWidget(0, 3)
        self.filters_table.setHorizontalHeaderLabels(["열", "연산", "값"])
        self.filters_table.verticalHeader().setVisible(False)
        self.filters_table.setSelectionMode(QTableWidget.NoSelection)
        fh = self.filters_table.horizontalHeader()
        fh.setSectionResizeMode(0, QHeaderView.Stretch)
        fh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        fh.setSectionResizeMode(2, QHeaderView.Stretch)
        lay.addWidget(self.filters_table)
        row = QHBoxLayout()
        row.setSpacing(8)
        add = QPushButton("＋ 필터 추가", objectName="Ghost")
        rm = QPushButton("－ 선택 삭제", objectName="Ghost")
        add.clicked.connect(lambda: self._add_filter_row())
        rm.clicked.connect(lambda: self._remove_row(self.filters_table))
        row.addWidget(add); row.addWidget(rm); row.addStretch(1)
        lay.addLayout(row)
        return box

    def _col_combo(self):
        c = QComboBox()
        c.addItems(self.state.columns())
        return c

    def _add_rule_row(self, rule: Rule = None):
        t = self.rules_table
        r = t.rowCount()
        t.insertRow(r)
        col = self._col_combo()
        kw = QLineEdit()
        kw.setPlaceholderText("키워드")
        match = QComboBox(); match.addItems(["contains", "equals"])
        pr = QSpinBox(); pr.setRange(1, 3); pr.setAlignment(Qt.AlignCenter)
        for wdg in (col, kw, match, pr):
            wdg.setMinimumHeight(30)
        color_btn = QPushButton("색")
        color_btn.setFixedWidth(46); color_btn.setMinimumHeight(30)
        color_btn.setProperty("hex", "#FFE14D")
        color_btn.setStyleSheet(_SWATCH_QSS.format(c="#FFE14D"))
        color_btn.clicked.connect(lambda _, b=color_btn: self._pick_color(b))
        if rule:
            col.setCurrentText(rule.column); kw.setText(rule.keyword)
            match.setCurrentText(rule.match); pr.setValue(rule.priority)
            color_btn.setProperty("hex", rule.color)
            color_btn.setStyleSheet(_SWATCH_QSS.format(c=rule.color))
        for i, w in enumerate([col, kw, match, pr, color_btn]):
            t.setCellWidget(r, i, w)

    def _add_filter_row(self, flt: Filter = None):
        t = self.filters_table
        r = t.rowCount()
        t.insertRow(r)
        col = self._col_combo()
        col.setMinimumWidth(88)
        op = QComboBox(); op.addItems(FILTER_OPS)
        val = QLineEdit()
        val.setPlaceholderText("값")
        for wdg in (col, op, val):
            wdg.setMinimumHeight(30)
        if flt:
            col.setCurrentText(flt.column); op.setCurrentText(flt.op); val.setText(flt.value)
        for i, w in enumerate([col, op, val]):
            t.setCellWidget(r, i, w)

    def _remove_row(self, table):
        r = table.currentRow()
        if r >= 0:
            table.removeRow(r)

    def _pick_color(self, btn):
        cur = QColor(btn.property("hex"))
        c = QColorDialog.getColor(cur, self, "행 색 선택")
        if c.isValid():
            btn.setProperty("hex", c.name().upper())
            btn.setStyleSheet(_SWATCH_QSS.format(c=c.name()))

    # ---- 데이터 로드 / 프리셋 ----
    def load_dataframe(self):
        cols = self.state.columns()
        self.drop_list.clear()
        for c in cols:
            it = QListWidgetItem(c)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Unchecked)
            self.drop_list.addItem(it)
        self.sort_combo.clear()
        self.sort_combo.addItems(["none", "priority"] + cols)
        self.split_combo.clear()
        self.split_combo.addItems([""] + cols)
        self._fill_preview()
        # 프리셋 값이 있으면 반영
        self.apply_preset(self.state.preset)

    def _fill_preview(self):
        df = self.state.df
        if df is None:
            return
        sample = df.head(PREVIEW_ROWS)
        self.preview.setColumnCount(len(sample.columns))
        self.preview.setHorizontalHeaderLabels([str(c) for c in sample.columns])
        self.preview.setRowCount(len(sample))
        for r in range(len(sample)):
            for c in range(len(sample.columns)):
                self.preview.setItem(r, c, QTableWidgetItem(str(sample.iat[r, c])))

    def apply_preset(self, preset):
        cols = self.state.columns()
        if not cols:
            return
        for i in range(self.drop_list.count()):
            it = self.drop_list.item(i)
            it.setCheckState(Qt.Checked if it.text() in preset.drop_columns else Qt.Unchecked)
        self.rules_table.setRowCount(0)
        for rule in preset.rules:
            self._add_rule_row(rule)
        self.filters_table.setRowCount(0)
        for flt in preset.filters:
            self._add_filter_row(flt)
        if preset.sort:
            self.sort_combo.setCurrentText(preset.sort)
        self.split_combo.setCurrentText(preset.sheet_split_column)

    def write_into(self, preset):
        # 데이터 미로드 상태에서는 설정 위젯이 비어 있으므로,
        # 기존 프리셋 값을 덮어쓰지 않도록 아무것도 기록하지 않는다.
        if self.state.df is None:
            return
        preset.drop_columns = [
            self.drop_list.item(i).text()
            for i in range(self.drop_list.count())
            if self.drop_list.item(i).checkState() == Qt.Checked
        ]
        preset.rules = []
        for r in range(self.rules_table.rowCount()):
            col = self.rules_table.cellWidget(r, 0).currentText()
            kw = self.rules_table.cellWidget(r, 1).text()
            match = self.rules_table.cellWidget(r, 2).currentText()
            pr = self.rules_table.cellWidget(r, 3).value()
            color = self.rules_table.cellWidget(r, 4).property("hex")
            preset.rules.append(Rule(column=col, keyword=kw, match=match, priority=pr, color=color))
        preset.filters = []
        for r in range(self.filters_table.rowCount()):
            col = self.filters_table.cellWidget(r, 0).currentText()
            op = self.filters_table.cellWidget(r, 1).currentText()
            val = self.filters_table.cellWidget(r, 2).text()
            preset.filters.append(Filter(column=col, op=op, value=val))
        preset.sort = self.sort_combo.currentText()
        preset.sheet_split_column = self.split_combo.currentText()

    # ---- 생성 ----
    def _generate(self):
        if self.state.df is None:
            QMessageBox.warning(self, "설정", "먼저 데이터를 불러오세요.")
            return
        self.write_into(self.state.preset)
        try:
            processed = process(self.state.df, self.state.preset)
        except ValueError as e:
            QMessageBox.critical(self, "생성 실패", str(e))
            return
        fmts = date_formats(self.state.target_date or date.today())
        out = str(app_paths.output_dir() / f"{fmts['yymmdd']} 공사현장 점검 우선순위 리스트.xlsx")
        try:
            write_excel(processed, out, self.state.preset.sheet_split_column)
        except (PermissionError, OSError) as e:
            QMessageBox.critical(self, "저장 실패", f"파일 저장에 실패했습니다.\n파일이 열려 있으면 닫고 다시 시도하세요.\n{e}")
            return
        self.state.output_path = out
        QMessageBox.information(self, "생성 완료", f"저장됨:\n{out}")
        self.main.goto(2)
