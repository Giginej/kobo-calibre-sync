"""
Kobo Calibre Sync - Main entry point
GUI application to import ebooks into Calibre and sync to Kobo via wireless
"""

import sys
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Kobo Calibre Sync")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
