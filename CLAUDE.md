# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kobo Calibre Sync is a Flask web app that imports ebooks into Calibre and syncs them to a Kobo e-reader, either via USB (through Calibre's `calibredb`) or wirelessly (the app serves ebook files directly to the Kobo's built-in browser). It can run locally on macOS for personal use, or be deployed as an LXC container on Proxmox to run continuously on the home network (see `PROXMOX_SETUP.md` and `scripts/`).

## Commands

```bash
# Install dependencies
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Run application (starts the Flask server on port 5050)
python -m src.main

# Run all tests
pytest

# Run single test
pytest tests/test_scanner.py::TestEbookScanner::test_scan_finds_epub -v
```

## Architecture

```
src/
├── main.py              # Entry point, starts the Flask app
├── web/
│   └── app.py            # Flask app: routes, HTML/JS templates, auth
└── core/
    ├── scanner.py        # Scans folders for ebook files (Ebook dataclass)
    ├── metadata.py        # Extracts metadata from ebooks (BookMetadata dataclass)
    └── calibre.py         # Calibre integration via calibredb CLI (CalibreManager)
```

**Data flow**: Browser calls `/api/scan` -> Scanner finds ebook files in the requested folder -> MetadataExtractor reads embedded metadata -> results shown in the web table -> `/api/import` calls CalibreManager to run `calibredb add` -> `/api/send` either copies to a USB-connected Kobo or exposes the books for wireless download via `/kobo` and `/download/<index>`.

There used to be two desktop GUIs (PySide6 and Tkinter) before the app pivoted to the Flask web interface; both were removed since neither was reachable from any entry point.

## Key Implementation Details

- Uses `calibredb` CLI tool located at `/Applications/calibre.app/Contents/MacOS/calibredb` on macOS (on Linux/LXC deployments, whatever `calibredb` is on `PATH`).
- Metadata extraction works fully for EPUB files via ebooklib; other formats return empty metadata (filename used as fallback).
- Wireless sync requires Kobo to be connected via Calibre's wireless device feature (Calibre: Connect/share > Start wireless device connection), or the app's own `/kobo` download page.
- Supported formats: `.epub`, `.mobi`, `.azw`, `.azw3`, `.fb2`, `.cbz`, `.cbr` (PDF escluso). `scanner.py` only scans one folder level (non-recursive).
- **Authentication**: every route requires HTTP Basic Auth (`src/web/app.py`). Credentials come from `KOBO_SYNC_USER` (default `kobo`) and `KOBO_SYNC_PASSWORD`. If `KOBO_SYNC_PASSWORD` is not set, a random password is generated at startup and printed to stdout/journalctl — it changes on every restart, so set it explicitly for any non-ephemeral deployment.
- **Path validation**: `/api/scan` only allows scanning inside the user's home directory or `EBOOK_SOURCE_DIR` (if set) — anything else is rejected with a 400, to prevent path traversal / arbitrary file read via `/download/<index>`.
- Environment variables: `EBOOK_SOURCE_DIR` (default scan folder, falls back to `~/Downloads`), `CALIBRE_LIBRARY` (used by deploy scripts; `CalibreManager.get_library_path()` currently only probes macOS-style paths, so this may need attention if the Linux/LXC deployment doesn't find the library automatically).

## Known gaps

- No automated tests for `core/calibre.py` (the `calibredb` subprocess wrapper), `core/metadata.py`, or `web/app.py` — only `core/scanner.py` is covered by `tests/`.
- `calibre.py` swallows several subprocess failures silently (bare `except`/`pass`) — a failed import or sync may show no error.
