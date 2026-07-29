# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for KEPCO RPA
Build command: pyinstaller build_exe.spec
"""

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# holidays는 국가별 모듈을 동적 로딩 → 서브모듈을 명시적으로 수집해야 EXE에서 SouthKorea 사용 가능
_holidays_submodules = collect_submodules('holidays')

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/ui/theme.qss', 'app/ui'),   # QSS 테마 번들
        ('app/ui/check.svg', 'app/ui'),   # 체크박스 체크표시 아이콘
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtSvg',
        'websockets',
        'requests',
        'pandas',
        'openpyxl',
        'lxml',
        'xlrd',
        *_holidays_submodules,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 앱은 QtWidgets/QtCore/QtGui/QtSvg만 사용 → 나머지 무거운 Qt 모듈 제외(용량 최적화)
    excludes=[
        'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuick3D',
        'PySide6.QtQuickWidgets', 'PySide6.QtQuickControls2',
        'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.Qt3DInput',
        'PySide6.Qt3DAnimation', 'PySide6.Qt3DExtras', 'PySide6.Qt3DLogic',
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineQuick', 'PySide6.QtWebChannel', 'PySide6.QtWebView',
        'PySide6.QtWebSockets', 'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets', 'PySide6.QtSpatialAudio',
        'PySide6.QtCharts', 'PySide6.QtDataVisualization', 'PySide6.QtGraphs',
        'PySide6.QtPdf', 'PySide6.QtPdfWidgets', 'PySide6.QtSql',
        'PySide6.QtTest', 'PySide6.QtHelp', 'PySide6.QtDesigner',
        'PySide6.QtUiTools', 'PySide6.QtScxml', 'PySide6.QtStateMachine',
        'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtSerialBus',
        'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtPositioning',
        'PySide6.QtLocation', 'PySide6.QtRemoteObjects', 'PySide6.QtTextToSpeech',
        'PySide6.QtNetworkAuth', 'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets',
        'PySide6.Qt3DQuick', 'PySide6.QtDataVisualizationQml',
        # 앱이 쓰지 않는 무거운 파이썬 라이브러리
        'tkinter', 'matplotlib', 'scipy', 'PIL', 'IPython', 'notebook',
        'pytest', '_pytest', 'PySide6.scripts',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KEPCO_RPA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 앱 — 콘솔(cmd) 창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
