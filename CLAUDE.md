# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kobo Calibre Sync is a PyQt6 desktop application that imports ebooks into Calibre and syncs them to a Kobo e-reader via Calibre's wireless device connection.

## Commands

```bash
# Install dependencies
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Run application
python -m src.main

# Run all tests
pytest

# Run single test
pytest tests/test_scanner.py::TestEbookScanner::test_scan_finds_epub -v
```

## Architecture

```
src/
├── main.py              # Entry point
├── gui/
│   └── main_window.py   # PyQt6 main window with ebook table
└── core/
    ├── scanner.py       # Scans folders for ebook files (Ebook dataclass)
    ├── metadata.py      # Extracts metadata from ebooks (BookMetadata dataclass)
    └── calibre.py       # Calibre integration via calibredb CLI (CalibreManager)
```

**Data flow**: Scanner finds ebook files -> MetadataExtractor reads embedded metadata -> CalibreManager imports via `calibredb add` command

## Key Implementation Details

- Uses `calibredb` CLI tool located at `/Applications/calibre.app/Contents/MacOS/calibredb` on macOS
- Metadata extraction works fully for EPUB files via ebooklib; other formats return empty metadata (filename used as fallback)
- Wireless sync requires Kobo to be connected via Calibre's wireless device feature (Calibre: Connect/share > Start wireless device connection)
- Supported formats: `.epub`, `.mobi`, `.azw`, `.azw3`, `.fb2`, `.cbz`, `.cbr` (PDF escluso)
