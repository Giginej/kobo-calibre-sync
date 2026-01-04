"""Tests for ebook scanner"""

import tempfile
from pathlib import Path

import pytest

from src.core.scanner import EbookScanner, SUPPORTED_FORMATS


class TestEbookScanner:
    def test_scan_empty_folder(self, tmp_path):
        scanner = EbookScanner()
        result = scanner.scan(tmp_path)
        assert result == []

    def test_scan_finds_epub(self, tmp_path):
        epub_file = tmp_path / "test.epub"
        epub_file.touch()

        scanner = EbookScanner()
        result = scanner.scan(tmp_path)

        assert len(result) == 1
        assert result[0].path == epub_file

    def test_scan_ignores_non_ebook_files(self, tmp_path):
        (tmp_path / "document.txt").touch()
        (tmp_path / "image.png").touch()
        (tmp_path / "book.epub").touch()

        scanner = EbookScanner()
        result = scanner.scan(tmp_path)

        assert len(result) == 1
        assert result[0].path.suffix == ".epub"

    def test_scan_nonexistent_folder(self):
        scanner = EbookScanner()
        result = scanner.scan(Path("/nonexistent/path"))
        assert result == []

    def test_supported_formats(self, tmp_path):
        for fmt in SUPPORTED_FORMATS:
            (tmp_path / f"book{fmt}").touch()

        scanner = EbookScanner()
        result = scanner.scan(tmp_path)

        assert len(result) == len(SUPPORTED_FORMATS)
