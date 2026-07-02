"""공용 위젯 — 스크롤 중 값이 바뀌지 않는 콤보박스."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox


class NoScrollComboBox(QComboBox):
    """마우스 휠로 값이 바뀌지 않게 한다.

    포커스(클릭)된 상태에서만 휠로 값 변경을 허용하고, 그렇지 않으면 휠 이벤트를
    무시해 부모 스크롤 영역이 스크롤되도록 한다."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()
