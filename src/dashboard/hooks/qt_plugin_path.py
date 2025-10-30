import os
import sys

def _set_qt_paths():
    base = getattr(sys, '_MEIPASS', None)
    if not base:
        return
    candidates = [
        os.path.join(base, 'PyQt6', 'Qt6', 'plugins'),
        os.path.join(base, 'Qt', 'plugins'),
        os.path.join(base, 'plugins'),
        os.path.join(base, 'PlugIns'),
    ]
    for p in candidates:
        platforms = os.path.join(p, 'platforms')
        if os.path.isdir(platforms):
            os.environ['QT_PLUGIN_PATH'] = p
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = platforms
            break

_set_qt_paths()
