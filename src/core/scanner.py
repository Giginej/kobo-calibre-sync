"""Ebook file scanner"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set, List


SUPPORTED_FORMATS = {".epub", ".mobi", ".azw", ".azw3", ".fb2", ".cbz", ".cbr"}


@dataclass
class Ebook:
    path: Path


class EbookScanner:
    def __init__(self, formats: Optional[Set[str]] = None):
        self.formats = formats or SUPPORTED_FORMATS

    def scan(self, folder: Path) -> List[Ebook]:
        """Scan a folder for ebook files (non-recursive)"""
        if not folder.exists():
            return []

        ebooks = []
        for file in folder.iterdir():
            if file.is_file() and file.suffix.lower() in self.formats:
                ebooks.append(Ebook(path=file))

        return sorted(ebooks, key=lambda e: e.path.name.lower())
