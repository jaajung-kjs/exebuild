"""
Configuration management for KEPCO RPA system
Handles path management for both development and exe packaging
"""

import os
import sys
from pathlib import Path


def get_base_dir():
    """
    Get the base directory of the application
    Works for both development and PyInstaller exe
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return os.path.dirname(sys.executable)
    else:
        # Running as Python script — 저장소 루트 (app/adapters/config.py 기준 2단계 상위)
        return str(Path(__file__).resolve().parents[2])


def get_output_dir():
    """Get the output directory (same as exe location)"""
    output_dir = get_base_dir()
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


# Server URLs
WORK_MONITOR_URL = "http://work-monitor.kepco.co.kr"
MAIL_URL = "http://mail.kepco.co.kr"   # 로그인된 SSO 웹메일
POWERGATE_WS_URI = "ws://127.0.0.1:21777"

# Work Monitor settings
DEPARTMENT_CODE = "4200"  # 강원본부 (fallback — 실제 값은 UI에서 선택한 본부 코드)
LIST_COUNT = 1000
PAGE = 1

# File format
FILE_FORMAT = "xls"  # Server returns HTML format regardless

# Timeouts
WEBSOCKET_TIMEOUT = 10
HTTP_TIMEOUT = 60
# 엑셀 생성이 서버에서 20~60초(때론 그 이상) 걸리므로 다운로드는 넉넉히.
DOWNLOAD_TIMEOUT = 300

# Application info
APP_NAME = "KEPCO RPA"
APP_VERSION = "1.0.0"
