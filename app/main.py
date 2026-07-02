"""KEPCO 점검 리스트 생성기 — 진입점."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def _ui_dir() -> Path:
    """theme.qss / check.svg 가 있는 폴더. EXE(frozen)에서도 정확히 찾는다."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return base / "app" / "ui"
    return Path(__file__).resolve().parent / "ui"


def load_theme() -> str:
    """QSS를 읽고 @CHECKICON@ 자리표시자를 체크 아이콘 실제 경로로 치환."""
    ui = _ui_dir()
    qss = ui / "theme.qss"
    if not qss.exists():
        return ""
    css = qss.read_text(encoding="utf-8")
    return css.replace("@CHECKICON@", (ui / "check.svg").as_posix())


def main():
    app = QApplication(sys.argv)
    # 플랫폼(특히 윈도우 네이티브 스타일)과 무관하게 QSS가 동일하게 적용되도록 고정
    app.setStyle("Fusion")
    app.setStyleSheet(load_theme())
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
