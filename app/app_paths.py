"""앱 런타임 경로 — 프리셋 폴더와 엑셀 출력 폴더"""

from pathlib import Path
from app.adapters import config


def presets_dir() -> Path:
    d = Path(config.get_base_dir()) / "presets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def output_dir() -> Path:
    return Path(config.get_base_dir())
