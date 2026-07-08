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
    if "--diag-send-external" in sys.argv:
        # 사외메일 실제 발송 테스트 (GUI 없음)
        from app.diag_external import run_send_external_test
        sys.exit(run_send_external_test(sys.argv))
    if "--diag-external" in sys.argv:
        # 사외메일 발송 가능 여부 진단 (GUI 없음)
        from app.diag_external import run_external_diag
        sys.exit(run_external_diag(sys.argv))

    from app.auto_run import is_auto_mode
    if is_auto_mode():
        # 무인 자동 실행 (GUI 없음) — QSettings 등을 위해 코어 앱만 생성
        from PySide6.QtCore import QCoreApplication
        from app.auto_run import run_auto
        QCoreApplication(sys.argv)
        sys.exit(run_auto())

    app = QApplication(sys.argv)
    # 플랫폼(특히 윈도우 네이티브 스타일)과 무관하게 QSS가 동일하게 적용되도록 고정
    app.setStyle("Fusion")
    app.setStyleSheet(load_theme())
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
