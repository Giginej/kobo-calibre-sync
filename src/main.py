"""
Kobo Calibre Sync - Main entry point
Web-based GUI to import ebooks into Calibre and sync to Kobo via wireless
"""

from src.web.app import run


def main():
    run()


if __name__ == "__main__":
    main()
