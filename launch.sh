#!/bin/bash
# Launch script for Kobo Calibre Sync

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"
PYSIDE6_PATH="$VENV/lib/python3.9/site-packages/PySide6"

export QT_PLUGIN_PATH="$PYSIDE6_PATH/Qt/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="$PYSIDE6_PATH/Qt/plugins/platforms"
export DYLD_LIBRARY_PATH="$PYSIDE6_PATH/Qt/lib:$DYLD_LIBRARY_PATH"
export DYLD_FRAMEWORK_PATH="$PYSIDE6_PATH/Qt/lib:$DYLD_FRAMEWORK_PATH"

source "$VENV/bin/activate"
exec python -m src.main "$@"
