"""뷰 간 공유되는 런타임 상태."""

from app.core.settings import Preset


class AppState:
    def __init__(self):
        self.df = None            # 다운로드 원본 DataFrame
        self.session = None       # 인증 세션 (메일 발송에 재사용)
        self.preset = Preset(name="새 프리셋", department_code="")
        self.output_path = None   # 생성된 엑셀 경로

    def columns(self) -> list:
        if self.df is None:
            return []
        return list(self.df.columns)
