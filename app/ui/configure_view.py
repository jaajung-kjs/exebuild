"""② 설정 뷰 — 넣을 항목·강조 규칙·필터를 쉬운 문장으로 지정 + 저장."""

import os
import subprocess
import sys
from datetime import date

from PySide6.QtWidgets import (
    QWidget, QFrame, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QComboBox,
    QLineEdit, QColorDialog, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.core.engine import process
from app.core.excel_writer import write_excel
from app.core.settings import Rule, Filter
from app.core.date_util import date_formats
from app import app_paths

PREVIEW_ROWS = 20

# 화면에 보이는 쉬운 말 ↔ 엔진이 쓰는 값
MATCH_OPTS = [("포함하면", "contains"), ("정확히 같으면", "equals")]
PRIORITY_OPTS = [("1순위", 1), ("2순위", 2), ("3순위", 3)]
FILTER_OPTS = [
    ("비어있지 않은", "not_null"),
    ("비어있는", "is_empty"),
    ("값을 포함하는", "contains"),
    ("값과 같은", "equals"),
    ("값과 다른", "not_equals"),
    ("값으로 시작하는", "starts_with"),
    ("값으로 끝나는", "ends_with"),
    ("여러 값 중 하나인", "in_list"),
]
MODE_OPTS = [("모두 만족(AND)", "and"), ("하나라도 만족(OR)", "or")]
NO_VALUE_OPS = {"not_null", "is_empty"}
_SWATCH_QSS = ("background:{c}; color:#1B2430; border:1px solid rgba(0,0,0,0.18); "
               "border-radius:6px; padding:4px 10px; font-weight:700;")


class ConfigureView(QWidget):
    def __init__(self, state, main):
        super().__init__()
        self.state = state
        self.main = main
        self.rule_rows = []      # [{frame, col, kw, match, prio, color}]
        self.filter_rows = []    # [{frame, col, op, val}]

        v = QVBoxLayout(self)
        v.setContentsMargins(32, 28, 32, 20)
        v.setSpacing(6)
        v.addWidget(QLabel("설정", objectName="H1"))
        v.addWidget(QLabel("리포트에 넣을 항목과 강조·필터 규칙을 정한 뒤 엑셀을 만듭니다.",
                           objectName="Hint"))
        v.addSpacing(14)

        # 스크롤 본문
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        b = QVBoxLayout(body)
        b.setContentsMargins(0, 0, 10, 0)
        b.setSpacing(16)
        b.addWidget(self._include_card())
        b.addWidget(self._rules_card())
        b.addWidget(self._filters_card())
        b.addWidget(self._options_card())
        b.addWidget(self._preview_card())
        b.addStretch(1)
        scroll.setWidget(body)
        v.addWidget(scroll, 1)

        # 하단 고정 액션
        v.addSpacing(10)
        bottom = QHBoxLayout()
        self.raw_btn = QPushButton("원본 그대로 저장", objectName="Ghost")
        self.raw_btn.setMinimumHeight(40)
        self.raw_btn.clicked.connect(self._save_raw)
        bottom.addWidget(self.raw_btn)
        bottom.addStretch(1)
        self.gen_btn = QPushButton("엑셀 저장", objectName="Primary")
        self.gen_btn.setMinimumHeight(40)
        self.gen_btn.clicked.connect(self._save)
        bottom.addWidget(self.gen_btn)
        v.addLayout(bottom)

    # ---------- 카드 뼈대 ----------
    def _card(self, title, hint=None):
        card = QFrame(objectName="Card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 18)
        lay.setSpacing(9)
        lay.addWidget(QLabel(title, objectName="CardTitle"))
        if hint:
            lay.addWidget(QLabel(hint, objectName="Hint"))
        lay.addWidget(QFrame(objectName="CardDivider"))
        return card, lay

    def _conn(self, text):
        return QLabel(text, objectName="Conn")

    def _include_card(self):
        card, lay = self._card(
            "① 리포트에 넣을 항목 고르기",
            "체크한 항목만 엑셀에 들어갑니다. (기본: 전체 포함)")
        bar = QHBoxLayout()
        bar.setSpacing(8)
        all_btn = QPushButton("전체 선택", objectName="Ghost")
        none_btn = QPushButton("전체 해제", objectName="Ghost")
        all_btn.clicked.connect(lambda: self._check_all(True))
        none_btn.clicked.connect(lambda: self._check_all(False))
        bar.addWidget(all_btn); bar.addWidget(none_btn); bar.addStretch(1)
        lay.addLayout(bar)
        self.include_list = QListWidget(objectName="DropList")
        self.include_list.setFrameShape(QFrame.NoFrame)
        self.include_list.setMinimumHeight(120)
        self.include_list.setMaximumHeight(190)
        lay.addWidget(self.include_list)
        return card

    def _rules_card(self):
        card, lay = self._card(
            "② 중요한 행을 색으로 강조하기",
            "예: ‘공사명’에 ‘활선’이 포함되면 1순위로 노란색 표시")
        self.rules_box = QVBoxLayout()
        self.rules_box.setSpacing(8)
        lay.addLayout(self.rules_box)
        add = QPushButton("＋ 강조 규칙 추가", objectName="Ghost")
        add.clicked.connect(lambda: self._add_rule_row())
        lay.addWidget(add, alignment=Qt.AlignLeft)
        return card

    def _filters_card(self):
        card, lay = self._card(
            "③ 필요한 행만 추리기 (선택)",
            "예: ‘지사’가 비어있지 않은 행만 남기기. 조건이 없으면 전체 행이 그대로 유지됩니다.")
        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        mode_row.addWidget(QLabel("여러 조건일 때", objectName="Conn"))
        self.mode_combo = self._mapped_combo(MODE_OPTS, 180)
        mode_row.addWidget(self.mode_combo)
        mode_row.addWidget(QLabel("하는 행만 남깁니다.", objectName="Conn"))
        mode_row.addStretch(1)
        lay.addLayout(mode_row)
        self.filters_box = QVBoxLayout()
        self.filters_box.setSpacing(8)
        lay.addLayout(self.filters_box)
        add = QPushButton("＋ 조건 추가", objectName="Ghost")
        add.clicked.connect(lambda: self._add_filter_row())
        lay.addWidget(add, alignment=Qt.AlignLeft)
        return card

    def _options_card(self):
        card, lay = self._card("④ 정렬 & 시트 나누기")
        row = QHBoxLayout()
        row.setSpacing(20)
        left = QVBoxLayout(); left.setSpacing(5)
        left.addWidget(QLabel("행 정렬 순서", objectName="FieldLabel"))
        self.sort_combo = QComboBox(); self.sort_combo.setMinimumHeight(34)
        left.addWidget(self.sort_combo)
        right = QVBoxLayout(); right.setSpacing(5)
        right.addWidget(QLabel("이 항목별로 시트 나누기", objectName="FieldLabel"))
        self.split_combo = QComboBox(); self.split_combo.setMinimumHeight(34)
        right.addWidget(self.split_combo)
        row.addLayout(left); row.addLayout(right)
        lay.addLayout(row)
        return card

    def _preview_card(self):
        card, lay = self._card(
            "미리보기",
            f"상위 {PREVIEW_ROWS}행만 표시합니다. 실제 생성은 전체 데이터에 적용됩니다.")
        self.preview = QTableWidget(objectName="InnerTable")
        self.preview.setFrameShape(QFrame.NoFrame)
        self.preview.setAlternatingRowColors(True)
        self.preview.verticalHeader().setVisible(False)
        self.preview.setEditTriggers(QTableWidget.NoEditTriggers)
        self.preview.setSelectionMode(QTableWidget.NoSelection)
        self.preview.horizontalHeader().setStretchLastSection(True)
        self.preview.setMinimumHeight(240)
        lay.addWidget(self.preview)
        return card

    # ---------- 공통 위젯 ----------
    def _col_combo(self):
        c = QComboBox()
        c.setMinimumHeight(32)
        c.setMinimumWidth(130)
        c.addItems(self.state.columns())
        return c

    def _mapped_combo(self, opts, width=130):
        c = QComboBox()
        c.setMinimumHeight(32)
        c.setMinimumWidth(width)
        for label, val in opts:
            c.addItem(label, val)
        return c

    @staticmethod
    def _set_data(combo, value):
        i = combo.findData(value)
        combo.setCurrentIndex(i if i >= 0 else 0)

    @staticmethod
    def _set_text(combo, text):
        i = combo.findText(text)
        if i >= 0:
            combo.setCurrentIndex(i)

    def _del_btn(self):
        b = QPushButton("✕", objectName="IconBtn")
        b.setFixedSize(30, 30)
        b.setToolTip("삭제")
        return b

    # ---------- 강조 규칙 행 ----------
    def _add_rule_row(self, rule: Rule = None):
        frame = QFrame(objectName="SentenceRow")
        h = QHBoxLayout(frame)
        h.setContentsMargins(12, 8, 10, 8)
        h.setSpacing(8)
        col = self._col_combo()
        kw = QLineEdit(); kw.setPlaceholderText("찾을 단어"); kw.setMinimumHeight(32)
        match = self._mapped_combo(MATCH_OPTS, 120)
        prio = self._mapped_combo(PRIORITY_OPTS, 84)
        color_btn = QPushButton("색"); color_btn.setFixedWidth(52); color_btn.setMinimumHeight(32)
        color_btn.setProperty("hex", "#FFE14D")
        color_btn.setStyleSheet(_SWATCH_QSS.format(c="#FFE14D"))
        color_btn.clicked.connect(lambda _, bt=color_btn: self._pick_color(bt))
        rm = self._del_btn()

        if rule:
            self._set_text(col, rule.column)
            kw.setText(rule.keyword)
            self._set_data(match, rule.match)
            self._set_data(prio, rule.priority)
            color_btn.setProperty("hex", rule.color)
            color_btn.setStyleSheet(_SWATCH_QSS.format(c=rule.color))

        h.addWidget(col)
        h.addWidget(self._conn("에"))
        h.addWidget(kw, 1)
        h.addWidget(self._conn("이(가)"))
        h.addWidget(match)
        h.addWidget(self._conn("→"))
        h.addWidget(prio)
        h.addWidget(self._conn("· 행 색"))
        h.addWidget(color_btn)
        h.addWidget(rm)

        entry = {"frame": frame, "col": col, "kw": kw, "match": match,
                 "prio": prio, "color": color_btn}
        rm.clicked.connect(lambda: self._remove_row(entry, self.rule_rows))
        self.rule_rows.append(entry)
        self.rules_box.addWidget(frame)

    # ---------- 필터 행 ----------
    def _add_filter_row(self, flt: Filter = None):
        frame = QFrame(objectName="SentenceRow")
        h = QHBoxLayout(frame)
        h.setContentsMargins(12, 8, 10, 8)
        h.setSpacing(8)
        col = self._col_combo()
        op = self._mapped_combo(FILTER_OPTS, 150)
        val = QLineEdit(); val.setPlaceholderText("값"); val.setMinimumHeight(32)
        rm = self._del_btn()

        if flt:
            self._set_text(col, flt.column)
            self._set_data(op, flt.op)
            val.setText(flt.value)

        entry = {"frame": frame, "col": col, "op": op, "val": val}
        op.currentIndexChanged.connect(lambda _=0, e=entry: self._sync_filter_value(e))

        h.addWidget(col)
        h.addWidget(self._conn("이(가)"))
        h.addWidget(op)
        h.addWidget(val, 1)
        h.addWidget(self._conn("행만 표시"))
        h.addWidget(rm)

        rm.clicked.connect(lambda: self._remove_row(entry, self.filter_rows))
        self.filter_rows.append(entry)
        self.filters_box.addWidget(frame)
        self._sync_filter_value(entry)

    def _sync_filter_value(self, entry):
        """조건에 따라 값 칸을 켜고 끄고, 안내 문구를 바꾼다."""
        op = entry["op"].currentData()
        needs_value = op not in NO_VALUE_OPS
        entry["val"].setEnabled(needs_value)
        if not needs_value:
            entry["val"].clear()
            entry["val"].setPlaceholderText("값 필요 없음")
        elif op == "in_list":
            entry["val"].setPlaceholderText("여러 값 · 쉼표로 구분 (예: 강릉,원주)")
        else:
            entry["val"].setPlaceholderText("값")

    def _remove_row(self, entry, rows):
        entry["frame"].setParent(None)
        if entry in rows:
            rows.remove(entry)

    def _clear_rows(self, rows):
        for e in list(rows):
            e["frame"].setParent(None)
        rows.clear()

    def _check_all(self, checked: bool):
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.include_list.count()):
            self.include_list.item(i).setCheckState(state)

    def _pick_color(self, btn):
        cur = QColor(btn.property("hex"))
        c = QColorDialog.getColor(cur, self, "행 색 선택")
        if c.isValid():
            btn.setProperty("hex", c.name().upper())
            btn.setStyleSheet(_SWATCH_QSS.format(c=c.name()))

    # ---------- 데이터 로드 / 프리셋 ----------
    def load_dataframe(self):
        cols = self.state.columns()
        self.include_list.clear()
        for c in cols:
            it = QListWidgetItem(c)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked)   # 기본: 전체 포함
            self.include_list.addItem(it)

        self.sort_combo.clear()
        self.sort_combo.addItem("정렬 안 함", "none")
        self.sort_combo.addItem("중요도(우선순위)순", "priority")
        for c in cols:
            self.sort_combo.addItem(f"{c} 순", c)

        self.split_combo.clear()
        self.split_combo.addItem("나누지 않음", "")
        for c in cols:
            self.split_combo.addItem(f"{c} 별로", c)

        self._clear_rows(self.rule_rows)
        self._clear_rows(self.filter_rows)
        self._fill_preview()
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
        # 포함 체크: 제외 목록(drop_columns)에 없으면 체크
        for i in range(self.include_list.count()):
            it = self.include_list.item(i)
            it.setCheckState(Qt.Unchecked if it.text() in preset.drop_columns else Qt.Checked)
        # 규칙·필터 재구성
        self._clear_rows(self.rule_rows)
        for rule in preset.rules:
            self._add_rule_row(rule)
        self._clear_rows(self.filter_rows)
        for flt in preset.filters:
            self._add_filter_row(flt)
        self._set_data(self.mode_combo, preset.filter_mode or "and")
        # 정렬·시트 분리
        self._set_data(self.sort_combo, preset.sort or "none")
        self._set_data(self.split_combo, preset.sheet_split_column or "")

    def write_into(self, preset):
        # 데이터 미로드 상태에서는 설정 위젯이 비어 있으므로,
        # 기존 프리셋 값을 덮어쓰지 않도록 아무것도 기록하지 않는다.
        if self.state.df is None:
            return
        # 체크 안 된 항목 = 리포트에서 제외
        preset.drop_columns = [
            self.include_list.item(i).text()
            for i in range(self.include_list.count())
            if self.include_list.item(i).checkState() != Qt.Checked
        ]
        preset.rules = [
            Rule(column=e["col"].currentText(), keyword=e["kw"].text(),
                 match=e["match"].currentData(), priority=e["prio"].currentData(),
                 color=e["color"].property("hex"))
            for e in self.rule_rows
        ]
        preset.filters = [
            Filter(column=e["col"].currentText(), op=e["op"].currentData(),
                   value=e["val"].text())
            for e in self.filter_rows
        ]
        preset.filter_mode = self.mode_combo.currentData() or "and"
        preset.sort = self.sort_combo.currentData() or "none"
        preset.sheet_split_column = self.split_combo.currentData() or ""

    # ---------- 저장 ----------
    def _out_path(self, suffix):
        fmts = date_formats(self.state.target_date or date.today())
        return str(app_paths.output_dir() / f"{fmts['yymmdd']} 공사현장 점검 {suffix}.xlsx")

    def save_processed(self) -> str | None:
        """설정을 적용해 저장. 성공 시 경로, 실패 시 None. (안내창 없음 — 실행 흐름에서 재사용)"""
        if self.state.df is None:
            return None
        self.write_into(self.state.preset)
        try:
            processed = process(self.state.df, self.state.preset)
        except ValueError as e:
            QMessageBox.critical(self, "저장 실패", str(e))
            return None
        out = self._out_path("우선순위 리스트")
        if self._write(processed, out, self.state.preset.sheet_split_column):
            self.state.output_path = out
            return out
        return None

    def save_raw(self) -> str | None:
        """가공 없이 원본 저장. 성공 시 경로, 실패 시 None."""
        if self.state.df is None:
            return None
        out = self._out_path("원본")
        if self._write(self.state.df, out, ""):
            self.state.output_path = out
            return out
        return None

    def _save(self):
        if self.state.df is None:
            QMessageBox.warning(self, "저장", "먼저 데이터를 불러오세요.")
            return
        out = self.save_processed()
        if out:
            self._after_save(out)

    def _save_raw(self):
        if self.state.df is None:
            QMessageBox.warning(self, "원본 저장", "먼저 데이터를 불러오세요.")
            return
        out = self.save_raw()
        if out:
            self._after_save(out)

    def _write(self, df, out, split) -> bool:
        try:
            write_excel(df, out, split)
            return True
        except (PermissionError, OSError) as e:
            QMessageBox.critical(self, "저장 실패",
                                 f"파일 저장에 실패했습니다.\n파일이 열려 있으면 닫고 다시 시도하세요.\n{e}")
            return False

    def _after_save(self, path):
        box = QMessageBox(self)
        box.setWindowTitle("저장 완료")
        box.setText(f"엑셀을 저장했습니다.\n{path}")
        open_btn = box.addButton("폴더 열기", QMessageBox.ActionRole)
        mail_btn = box.addButton("메일로 보내기 (베타)", QMessageBox.ActionRole)
        box.addButton("닫기", QMessageBox.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked == open_btn:
            self._open_folder(path)
        elif clicked == mail_btn:
            self.main.goto(2)

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
