"""KEPCO 점검 리스트 생성기 — 진입점."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def load_theme() -> str:
    """QSS를 읽고 @CHECKICON@ 자리표시자를 체크 아이콘 실제 경로로 치환."""
    ui = Path(__file__).resolve().parent / "ui"
    qss = ui / "theme.qss"
    if not qss.exists():
        return ""
    css = qss.read_text(encoding="utf-8")
    return css.replace("@CHECKICON@", (ui / "check.svg").as_posix())


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(load_theme())
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
