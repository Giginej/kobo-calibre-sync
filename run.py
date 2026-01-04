#!/usr/bin/env python3
"""
Launcher script that sets up Qt plugin paths correctly for macOS
"""
import os
import sys

# Get the path to PySide6's Qt plugins
try:
    import PySide6
    pyside6_path = os.path.dirname(PySide6.__file__)
    plugin_path = os.path.join(pyside6_path, "Qt", "plugins")

    if os.path.exists(plugin_path):
        os.environ["QT_PLUGIN_PATH"] = plugin_path
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(plugin_path, "platforms")
except ImportError:
    pass

# Now import and run the app
from src.main import main

if __name__ == "__main__":
    main()
