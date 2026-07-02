"""앱 런타임 경로 — 엑셀 출력 폴더"""

from pathlib import Path
from app.adapters import config


def output_dir() -> Path:
    return Path(config.get_base_dir())
