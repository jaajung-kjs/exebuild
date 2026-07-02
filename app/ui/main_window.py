"""메인 윈도우 — 사이드바 네비게이션 + 설정 자동 저장·복원.

설정은 QSettings(윈도우 레지스트리)에 저장되어 파일을 만들지 않는다(사내 DRM 회피).
프로그램 시작 시 자동 복원, [설정 저장]으로 갱신."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
    QStackedWidget, QLabel, QMessageBox,
)

from app.ui.state import AppState
from app.ui.extract_view import ExtractView
from app.ui.configure_view import ConfigureView
from app.ui.mail_view import MailView
from app.ui import config_store


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KEPCO 점검 리스트 생성기")
        self.resize(1080, 720)
        self.state = AppState()
        self.state.preset = config_store.load_config()   # 저장된 설정 자동 복원

        # 사이드바
        sidebar = QWidget(objectName="Sidebar")
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(0)
        sb.addWidget(self._brand_header())
        sb.addWidget(QLabel("점검 리스트 생성기", objectName="BrandSub"))
        self.nav = QListWidget()
        self.nav.addItems(["①   실행", "②   설정", "③   메일"])
        self.nav.currentRowChanged.connect(self._nav_changed)
        sb.addWidget(self.nav)
        sb.addStretch(1)

        # 본문 스택
        self.stack = QStackedWidget()
        self.extract = ExtractView(self.state, self)
        self.configure = ConfigureView(self.state, self)
        self.mail = MailView(self.state, self)
        for w in (self.extract, self.configure, self.mail):
            self.stack.addWidget(w)

        # 복원된 설정을 각 화면에 반영(날짜·본부·메일 등)
        self.apply_preset(self.state.preset)

        root = QWidget()
        row = QHBoxLayout(root)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(sidebar)
        row.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.nav.setCurrentRow(0)

    @staticmethod
    def _ui_dir() -> Path:
        if getattr(sys, "frozen", False):
            return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "app" / "ui"
        return Path(__file__).resolve().parent

    def _brand_header(self) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(22, 22, 22, 2)
        h.setSpacing(9)
        logo = QLabel()
        ui = self._ui_dir()
        # 공식 로고가 있으면(app/ui/logo.png) 우선 사용, 없으면 기본 엠블럼(logo.svg)
        path = ui / "logo.png"
        if not path.exists():
            path = ui / "logo.svg"
        pix = QPixmap(str(path))
        if not pix.isNull():
            logo.setPixmap(pix.scaledToHeight(26, Qt.SmoothTransformation))
        h.addWidget(logo)
        h.addWidget(QLabel("KEPCO", objectName="Brand"))
        h.addStretch(1)
        return row

    # ---- 네비게이션 ----
    def _nav_changed(self, row: int):
        if row >= 0:
            self.stack.setCurrentIndex(row)

    def goto(self, index: int):
        self.nav.setCurrentRow(index)

    # ---- 설정 저장/복원 ----
    def _save_config(self):
        self.collect_preset()                       # 모든 탭 → state.preset
        config_store.save_config(self.state.preset)  # 레지스트리에 영구 저장
        QMessageBox.information(self, "설정 저장",
                                "설정을 저장했습니다.\n다음 실행부터 자동으로 적용됩니다.")

    def persist_config(self):
        """현재 state.preset을 조용히(안내창 없이) 저장. ①실행의 본부·날짜 자동 저장용."""
        config_store.save_config(self.state.preset)

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
