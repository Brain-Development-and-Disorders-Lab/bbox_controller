# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None
project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))

# Only collect essential Qt plugins
qt_datas = []
qt_datas += collect_data_files('PyQt6', includes=['Qt6/plugins/platforms/*'])
qt_datas += collect_data_files('PyQt6', includes=['Qt6/plugins/imageformats/*'])

# Only collect dynamic libs for the used modules (Core/Gui/Widgets)
qt_bins = []
qt_bins += collect_dynamic_libs('PyQt6.QtCore')
qt_bins += collect_dynamic_libs('PyQt6.QtGui')
qt_bins += collect_dynamic_libs('PyQt6.QtWidgets')

a = Analysis(
    ['main.py'],
    pathex=[os.getcwd(), project_root],
    binaries=qt_bins,
    datas=[
        ('ui', 'dashboard/ui'),
        ('config', 'dashboard/config'),
        ('assets', 'dashboard/assets'),
        ('experiments', 'dashboard/experiments'),
        *qt_datas,
    ],
    hiddenimports=[
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.uic',
        'websocket-client',  # your dashboard deps
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(os.getcwd(), 'hooks', 'qt_plugin_path.py')],
    excludes=[
        # Avoid pulling unrelated Qt stacks
        'PySide6',
        'PyQt6.QtQml', 'PyQt6.QtQml.*',
        'PyQt6.QtQuick', 'PyQt6.QtQuick.*',
        'PyQt6.Qt3D', 'PyQt6.Qt3D.*',
        'PyQt6.QtQuick3D', 'PyQt6.QtQuick3D.*',
        'PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngineCore.*',
        'PyQt6.QtSql', 'PyQt6.QtSql.*',  # drops ODBC/Postgres plugins
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Behavior Box Dashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Behavior Box Dashboard',
)

app = BUNDLE(
    coll,
    name='Behavior Box Dashboard.app',
    icon='assets/icon.icns',
    bundle_identifier='com.behaviorbox.dashboard',
)
