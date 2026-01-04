"""Calibre integration via calibredb command-line tool"""

from __future__ import annotations

import subprocess
import shutil
from pathlib import Path
from typing import Optional, List

from src.core.scanner import Ebook


class CalibreError(Exception):
    """Raised when Calibre operations fail"""

    pass


class CalibreManager:
    def __init__(self, calibredb_path: Optional[str] = None):
        self.calibredb = calibredb_path or self._find_calibredb()

    def _find_calibredb(self) -> str:
        """Find calibredb executable"""
        # macOS Calibre installation path
        macos_path = "/Applications/calibre.app/Contents/MacOS/calibredb"
        if Path(macos_path).exists():
            return macos_path

        # Try to find in PATH
        path = shutil.which("calibredb")
        if path:
            return path

        raise CalibreError(
            "calibredb not found. Please install Calibre or specify the path."
        )

    def _run(self, *args) -> subprocess.CompletedProcess:
        """Run calibredb command"""
        cmd = [self.calibredb, *args]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise CalibreError(f"calibredb error: {result.stderr}")
        return result

    def import_books(self, ebooks: List[Ebook]) -> List[int]:
        """Import ebooks into Calibre library. Returns list of book IDs."""
        imported_ids = []

        for ebook in ebooks:
            result = self._run("add", str(ebook.path))
            # Parse the output to get the book ID
            # Output format: "Added book ids: X"
            for line in result.stdout.splitlines():
                if "Added book ids:" in line:
                    ids_str = line.split(":")[-1].strip()
                    for id_str in ids_str.split(","):
                        try:
                            imported_ids.append(int(id_str.strip()))
                        except ValueError:
                            pass

        return imported_ids

    def send_to_device(self, ebooks: List[Ebook]) -> None:
        """
        Send ebooks to connected device via Calibre's wireless device connection.

        Note: The Kobo must be connected via Calibre's wireless device feature.
        In Calibre: Connect/share > Start wireless device connection
        On Kobo: Settings > Calibre device connection > Connect
        """
        # First import to get book IDs, then send
        for ebook in ebooks:
            # Add book if not already in library
            result = self._run("add", "--duplicates", str(ebook.path))

            # The book is now in the library and will be synced to the device
            # when using Calibre's wireless connection

        # Note: Direct device sending requires calibre-server or GUI
        # For wireless sync, books need to be in the library and
        # the device needs to sync via Calibre's wireless feature

    def list_books(self, search: str = "") -> str:
        """List books in library, optionally filtered by search"""
        if search:
            result = self._run("list", "--search", search)
        else:
            result = self._run("list")
        return result.stdout
