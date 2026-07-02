"""뷰 간 공유되는 런타임 상태."""

from app.core.settings import Preset
from app.core.columns import WORK_MONITOR_COLUMNS


class AppState:
    def __init__(self):
        self.df = None            # 다운로드 원본 DataFrame
        self.session = None       # 인증 세션 (메일 발송에 재사용)
        self.preset = Preset(name="새 프리셋", department_code="",
                             sheet_split_column="2차사업소")
        self.output_path = None   # 생성된 엑셀 경로
        self.target_date = None   # 추출에서 선택한 대상 날짜 (date)

    def columns(self) -> list:
        # 컬럼은 고정. 다운로드된 df와 무관하게 항상 같은 목록으로 설정을 구성한다.
        return list(WORK_MONITOR_COLUMNS)
