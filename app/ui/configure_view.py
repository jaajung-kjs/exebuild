"""② 설정 뷰 — 넣을 항목·강조 규칙·필터를 쉬운 문장으로 편집·저장.

설정(프리셋) 편집 전용. 실제 실행(다운로드·저장·메일)은 ①실행 화면에서만 한다."""

from PySide6.QtWidgets import (
    QWidget, QFrame, QScrollArea, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QCheckBox, QLineEdit, QColorDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.core.settings import Rule, Filter
from app.ui.widgets import NoScrollComboBox

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
DEFAULT_SPLIT = "2차사업소"   # 시트 나누기 기본 기준 열
_SWATCH_QSS = ("background:{c}; color:#1B2430; border:1px solid rgba(0,0,0,0.18); "
               "border-radius:6px; padding:4px 10px; font-weight:700;")


class ConfigureView(QWidget):
    def __init__(self, state, main):
        super().__init__()
        self.state = state
        self.main = main
        self.rule_rows = []      # [{frame, col, kw, match, prio, color}]
        self.filter_rows = []    # [{frame, col, op, val}]
        self.include_checks = [] # 컬럼 포함 체크박스 리스트

        v = QVBoxLayout(self)
        v.setContentsMargins(32, 28, 32, 20)
        v.setSpacing(6)
        v.addWidget(QLabel("설정", objectName="H1"))
        v.addWidget(QLabel("안전 우선순위에 포함할 항목과 강조·필터 규칙을 정한 뒤 엑셀을 만듭니다.",
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
        b.addStretch(1)
        scroll.setWidget(body)
        v.addWidget(scroll, 1)

        # 하단 고정 액션 — 설정(프리셋) 저장만. 실행은 ①실행 화면에서.
        v.addSpacing(10)
        bottom = QHBoxLayout()
        bottom.addWidget(QLabel("다운로드·저장·메일 실행은 ①실행 화면에서 합니다.",
                                objectName="Hint"))
        bottom.addStretch(1)
        self.save_btn = QPushButton("설정 저장", objectName="Primary")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(lambda: self.main._save_config())
        bottom.addWidget(self.save_btn)
        v.addLayout(bottom)

        # 다운로드 전에도 고정 컬럼으로 설정 가능하게 초기 채움
        self.populate_columns()

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
            "① 안전 우선순위에 포함할 항목 고르기",
            "체크한 항목만 엑셀에 들어갑니다. (기본: 전체 포함)")
        bar = QHBoxLayout()
        bar.setSpacing(8)
        all_btn = QPushButton("전체 선택", objectName="Ghost")
        none_btn = QPushButton("전체 해제", objectName="Ghost")
        all_btn.clicked.connect(lambda: self._check_all(True))
        none_btn.clicked.connect(lambda: self._check_all(False))
        bar.addWidget(all_btn); bar.addWidget(none_btn); bar.addStretch(1)
        lay.addLayout(bar)
        # 컬럼 체크박스 3열 그리드 (스크롤 줄이기)
        self.include_grid = QGridLayout()
        self.include_grid.setHorizontalSpacing(18)
        self.include_grid.setVerticalSpacing(7)
        lay.addLayout(self.include_grid)
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
            "③ 필요한 행만 추리기",
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
        self.sort_combo = NoScrollComboBox(); self.sort_combo.setMinimumHeight(34)
        left.addWidget(self.sort_combo)
        right = QVBoxLayout(); right.setSpacing(5)
        right.addWidget(QLabel("이 항목별로 시트 나누기", objectName="FieldLabel"))
        self.split_combo = NoScrollComboBox(); self.split_combo.setMinimumHeight(34)
        right.addWidget(self.split_combo)
        row.addLayout(left); row.addLayout(right)
        lay.addLayout(row)

        lay.addWidget(QLabel("저장 파일명", objectName="FieldLabel"))
        self.filename_edit = QLineEdit(); self.filename_edit.setMinimumHeight(34)
        self.filename_edit.setPlaceholderText("{DATE} 공사현장 점검 우선순위 리스트")
        lay.addWidget(self.filename_edit)
        lay.addWidget(QLabel(
            "{DATE}는 ①실행에서 선택한 대상 날짜로 바뀝니다(예: 260709). "
            "확장자(.xlsx)는 자동으로 붙습니다. 비워두면 기본값을 씁니다.",
            objectName="Hint"))
        return card

    # ---------- 공통 위젯 ----------
    def _col_combo(self):
        c = NoScrollComboBox()
        c.setMinimumHeight(32)
        c.setMinimumWidth(130)
        c.addItems(self.state.columns())
        return c

    def _mapped_combo(self, opts, width=130):
        c = NoScrollComboBox()
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
        for cb in self.include_checks:
            cb.setChecked(checked)

    def _pick_color(self, btn):
        cur = QColor(btn.property("hex"))
        c = QColorDialog.getColor(cur, self, "행 색 선택")
        if c.isValid():
            btn.setProperty("hex", c.name().upper())
            btn.setStyleSheet(_SWATCH_QSS.format(c=c.name()))

    # ---------- 데이터 로드 / 프리셋 ----------
    def populate_columns(self):
        """고정 컬럼(또는 다운로드된 컬럼)으로 설정 위젯을 채운다. 다운로드 전에도 동작."""
        cols = self.state.columns()
        # 3열 체크박스 그리드 재구성
        while self.include_grid.count():
            item = self.include_grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        self.include_checks = []
        ncols = 3
        for i, c in enumerate(cols):
            cb = QCheckBox(c)
            cb.setChecked(True)   # 기본: 전체 포함
            self.include_grid.addWidget(cb, i // ncols, i % ncols)
            self.include_checks.append(cb)
        for col in range(ncols):
            self.include_grid.setColumnStretch(col, 1)

        self.sort_combo.clear()
        self.sort_combo.addItem("정렬 안 함", "none")
        self.sort_combo.addItem("점검순위 순 (1 → 2 → 3순위)", "priority")
        for c in cols:
            self.sort_combo.addItem(f"{c} 순", c)

        self.split_combo.clear()
        self.split_combo.addItem("나누지 않음", "")
        for c in cols:
            label = f"{c} 별로" + ("  (기본값)" if c == DEFAULT_SPLIT else "")
            self.split_combo.addItem(label, c)

    def apply_preset(self, preset):
        cols = self.state.columns()
        if not cols:
            return
        # 포함 체크: 제외 목록(drop_columns)에 없으면 체크
        for cb in self.include_checks:
            cb.setChecked(cb.text() not in preset.drop_columns)
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
        # 저장된 값이 없으면 기본으로 '2차사업소별로' 선택
        self._set_data(self.split_combo, preset.sheet_split_column or DEFAULT_SPLIT)
        self.filename_edit.setText(preset.filename_template)

    def write_into(self, preset):
        # 열은 하드코딩(고정)이라 다운로드 없이도 위젯이 항상 채워져 있으므로
        # 언제든 현재 설정을 프리셋에 기록한다.
        # 체크 안 된 항목 = 안전 우선순위에서 제외
        preset.drop_columns = [cb.text() for cb in self.include_checks if not cb.isChecked()]
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
        preset.filename_template = self.filename_edit.text().strip()

