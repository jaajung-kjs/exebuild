"""KEPCO 점검 리스트 생성기 — 진입점."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    qss = Path(__file__).resolve().parent / "ui" / "theme.qss"
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
