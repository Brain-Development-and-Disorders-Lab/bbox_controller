# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

try:
    _spec_dir = Path(__file__).parent
except NameError:
    _spec_dir = Path(os.getcwd())
_repo_root = _spec_dir.parent.parent.resolve()
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from version import __version__

block_cipher = None

a = Analysis(
    ['../../packages/dashboard/main.py'],
    pathex=['../../packages'],
    binaries=[],
    datas=[
        ('../../packages/dashboard/ui/form.ui', 'dashboard/ui'),
        ('assets/icon.icns', 'assets'),
        ('assets/icon.png', 'assets'),
        ('config/devices.json', 'config'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'websocket',
        'websocket-client',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
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
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='Behavior Box Dashboard',
)

app = BUNDLE(
    coll,
    name='Behavior Box Dashboard.app',
    icon='assets/icon.icns',
    bundle_identifier='com.behaviorbox.dashboard',
    version=__version__,
)
