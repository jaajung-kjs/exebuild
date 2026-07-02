"""메인 윈도우 — 사이드바 네비게이션 + 프리셋 바."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QHBoxLayout, QVBoxLayout, QListWidget,
    QStackedWidget, QLabel, QPushButton, QComboBox, QInputDialog, QMessageBox,
)

from app.ui.state import AppState
from app.ui.extract_view import ExtractView
from app.ui.configure_view import ConfigureView
from app.ui.mail_view import MailView
from app.core import preset_store
from app import app_paths


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KEPCO 점검 리스트 생성기")
        self.resize(1080, 720)
        self.state = AppState()

        # 사이드바
        sidebar = QWidget(objectName="Sidebar")
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(0)
        sb.addWidget(QLabel("KEPCO", objectName="Brand"))
        sb.addWidget(QLabel("점검 리스트 생성기", objectName="BrandSub"))
        self.nav = QListWidget()
        self.nav.addItems(["①   추출", "②   설정", "③   메일"])
        self.nav.currentRowChanged.connect(self._nav_changed)
        sb.addWidget(self.nav)
        sb.addStretch(1)
        sb.addWidget(self._preset_bar())

        # 본문 스택
        self.stack = QStackedWidget()
        self.extract = ExtractView(self.state, self)
        self.configure = ConfigureView(self.state, self)
        self.mail = MailView(self.state, self)
        for w in (self.extract, self.configure, self.mail):
            self.stack.addWidget(w)

        root = QWidget()
        row = QHBoxLayout(root)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(sidebar)
        row.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.nav.setCurrentRow(0)

    def _preset_bar(self) -> QWidget:
        bar = QFrame(objectName="PresetPanel")
        v = QVBoxLayout(bar)
        v.setContentsMargins(16, 14, 16, 16)
        v.setSpacing(8)
        self.preset_combo = QComboBox()
        self._reload_presets()
        load = QPushButton("불러오기", objectName="PresetBtn")
        save = QPushButton("저장", objectName="PresetBtn")
        load.clicked.connect(self._load_preset)
        save.clicked.connect(self._save_preset)
        v.addWidget(QLabel("프리셋", objectName="PresetLabel"))
        v.addWidget(self.preset_combo)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(load)
        row.addWidget(save)
        v.addLayout(row)
        return bar

    # ---- 네비게이션 ----
    def _nav_changed(self, row: int):
        if row >= 0:
            self.stack.setCurrentIndex(row)

    def goto(self, index: int):
        self.nav.setCurrentRow(index)

    # ---- 프리셋 ----
    def _reload_presets(self):
        self.preset_combo.clear()
        self.preset_combo.addItems(preset_store.list_presets(app_paths.presets_dir()))

    def _load_preset(self):
        name = self.preset_combo.currentText()
        if not name:
            return
        preset = preset_store.load_preset(name, app_paths.presets_dir())
        self.state.preset = preset
        self.apply_preset(preset)
        QMessageBox.information(self, "프리셋", f"'{name}' 불러오기 완료")

    def _save_preset(self):
        preset = self.collect_preset()
        name, ok = QInputDialog.getText(self, "프리셋 저장", "이름:", text=preset.name)
        if not ok or not name.strip():
            return
        preset.name = name.strip()
        preset_store.save_preset(preset, app_paths.presets_dir())
        self.state.preset = preset
        self._reload_presets()
        self.preset_combo.setCurrentText(preset.name)
        QMessageBox.information(self, "프리셋", f"'{preset.name}' 저장 완료")

    def apply_preset(self, preset):
        self.extract.apply_preset(preset)
        self.configure.apply_preset(preset)
        self.mail.apply_preset(preset)

    def collect_preset(self):
        preset = self.state.preset
        self.extract.write_into(preset)
        self.configure.write_into(preset)
        self.mail.write_into(preset)
        return preset
