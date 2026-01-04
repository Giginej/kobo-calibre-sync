"""Metadata extraction from ebook files"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ebooklib import epub


@dataclass
class BookMetadata:
    title: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None


class MetadataExtractor:
    def extract(self, path: Path) -> BookMetadata:
        """Extract metadata from an ebook file"""
        suffix = path.suffix.lower()

        if suffix == ".epub":
            return self._extract_epub(path)

        # For other formats, return empty metadata (filename will be used as title)
        return BookMetadata()

    def _extract_epub(self, path: Path) -> BookMetadata:
        """Extract metadata from EPUB file"""
        try:
            book = epub.read_epub(str(path), options={"ignore_ncx": True})

            title = self._get_metadata(book, "title")
            author = self._get_metadata(book, "creator")
            language = self._get_metadata(book, "language")
            publisher = self._get_metadata(book, "publisher")
            description = self._get_metadata(book, "description")

            # Try to get ISBN from identifiers
            isbn = None
            identifiers = book.get_metadata("DC", "identifier")
            for identifier in identifiers:
                id_value = identifier[0] if isinstance(identifier, tuple) else identifier
                if id_value and "isbn" in str(id_value).lower():
                    isbn = id_value
                    break

            return BookMetadata(
                title=title,
                author=author,
                language=language,
                publisher=publisher,
                description=description,
                isbn=isbn,
            )
        except Exception:
            return BookMetadata()

    def _get_metadata(self, book, field: str) -> Optional[str]:
        """Get a single metadata field from epub"""
        try:
            data = book.get_metadata("DC", field)
            if data:
                value = data[0]
                if isinstance(value, tuple):
                    return value[0]
                return value
        except Exception:
            pass
        return None
