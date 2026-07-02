"""단일 설정을 QSettings에 자동 저장·복원.

QSettings는 Windows에서 레지스트리(HKEY_CURRENT_USER\\Software\\...), macOS에서
사용자 환경설정(plist)에 저장한다 — 문서 파일을 새로 만들지 않으므로 사내 DRM의
영향을 받지 않고, 읽어올 파일도 없다. 한 번 저장하면 계속 남아 프로그램 시작 시
자동 복원된다."""

import json

from PySide6.QtCore import QSettings

from app.core.settings import Preset

_ORG = "KEPCO"
_APP = "점검리스트생성기"
_KEY = "preset_json"


def _settings() -> QSettings:
    return QSettings(_ORG, _APP)


def load_config() -> Preset:
    """저장된 설정을 복원. 없거나 손상됐으면 기본 설정."""
    raw = _settings().value(_KEY, "")
    if raw:
        try:
            return Preset.from_dict(json.loads(raw))
        except (ValueError, TypeError):
            pass
    # 기본값: 2차사업소별로 시트 나누기
    return Preset(name="기본 설정", department_code="", sheet_split_column="2차사업소")


def save_config(preset: Preset) -> None:
    """현재 설정을 저장(레지스트리 등). 즉시 반영·영구 보존."""
    s = _settings()
    s.setValue(_KEY, json.dumps(preset.to_dict(), ensure_ascii=False))
    s.sync()
