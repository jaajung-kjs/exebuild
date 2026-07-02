"""프리셋 JSON 저장소 — presets/<이름>.json 로드·저장·삭제·목록"""

import json
import re
from pathlib import Path

from app.core.settings import Preset


def _safe_filename(name: str) -> str:
    """파일명에 쓸 수 없는 문자를 _로 치환"""
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


def save_preset(preset: Preset, directory: Path) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{_safe_filename(preset.name)}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(preset.to_dict(), f, ensure_ascii=False, indent=2)
    return path


def load_preset(name: str, directory: Path) -> Preset:
    path = Path(directory) / f"{_safe_filename(name)}.json"
    with open(path, "r", encoding="utf-8") as f:
        return Preset.from_dict(json.load(f))


def list_presets(directory: Path) -> list[str]:
    directory = Path(directory)
    if not directory.exists():
        return []
    names = []
    for p in directory.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                names.append(json.load(f).get("name", p.stem))
        except (json.JSONDecodeError, OSError):
            continue
    return sorted(names)


def delete_preset(name: str, directory: Path) -> None:
    path = Path(directory) / f"{_safe_filename(name)}.json"
    if path.exists():
        path.unlink()
