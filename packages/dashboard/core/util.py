import sys
import os

def get_app_data_dir():
    """Get the application data directory for storing config, experiments, etc.

    When running from PyInstaller bundle, stores data next to the .app bundle.
    When running in development, uses the apps/dashboard directory.
    """
    if hasattr(sys, '_MEIPASS'):
        # Running from PyInstaller bundle
        # Get the directory containing the .app bundle
        if sys.platform == 'darwin':
            # On macOS, if we're in a .app bundle, go up to find the .app directory
            bundle_path = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            if bundle_path.endswith('.app'):
                # Data directory next to the .app bundle
                app_data_dir = os.path.dirname(bundle_path)
            else:
                # Fallback: use executable directory
                app_data_dir = os.path.dirname(sys.executable)
        else:
            # On other platforms, use executable directory
            app_data_dir = os.path.dirname(sys.executable)
    else:
        # Running in development mode
        app_data_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            '..',
            'apps',
            'dashboard'
        )

    return os.path.abspath(app_data_dir)
