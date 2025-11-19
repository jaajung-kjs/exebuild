"""
Configuration management for KEPCO RPA system
Handles path management for both development and exe packaging
"""

import os
import sys


def get_base_dir():
    """
    Get the base directory of the application
    Works for both development and PyInstaller exe
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return os.path.dirname(sys.executable)
    else:
        # Running as Python script
        return os.path.dirname(os.path.abspath(__file__))


def get_classification_file_path():
    """Get the path to 분류표.xlsx"""
    return os.path.join(get_base_dir(), '분류표.xlsx')


def get_output_dir():
    """Get the output directory (same as exe location)"""
    output_dir = get_base_dir()
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


# Server URLs
WORK_MONITOR_URL = "http://work-monitor.kepco.co.kr"
BIZMAIL_URL = "http://bizmail.kepco.co.kr"
POWERGATE_WS_URI = "ws://127.0.0.1:21777"

# Work Monitor settings
DEPARTMENT_CODE = "4200"  # 강원본부
LIST_COUNT = 1000
PAGE = 1

# File format
FILE_FORMAT = "xls"  # Server returns HTML format regardless

# Timeouts
WEBSOCKET_TIMEOUT = 10
HTTP_TIMEOUT = 60

# Application info
APP_NAME = "KEPCO RPA"
APP_VERSION = "1.0.0"
