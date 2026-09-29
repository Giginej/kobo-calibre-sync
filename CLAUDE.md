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
- **Kobo IP allowlist**: the Kobo browser handles Basic Auth poorly, so `/kobo` and `/download/<index>` skip auth when the client IP (`request.remote_addr`) is listed in `KOBO_DEVICE_IPS` (comma-separated). All other routes still require auth. This relies on Flask being exposed directly; behind a reverse proxy `remote_addr` would be the proxy's IP.
- **Path validation**: `/api/scan` only allows scanning inside the user's home directory or `EBOOK_SOURCE_DIR` (if set) — anything else is rejected with a 400, to prevent path traversal / arbitrary file read via `/download/<index>`.
- Environment variables: `EBOOK_SOURCE_DIR` (default scan folder, falls back to `~/Downloads`), `CALIBRE_LIBRARY` (when set, `get_library_path()` returns it and every `calibredb` call gets `--with-library`; otherwise macOS-style paths under the home are probed), `KOBO_DEVICE_IPS` (see above).

## Deployment

Live on Proxmox CT101 (`kobo-sync`, 192.168.10.107:5050), running as root from `/opt/kobo-sync` (plain copy, not a git checkout: deploy with `git archive HEAD` + `pct push`, keeping the existing `.venv`). Secrets and `KOBO_DEVICE_IPS` live in `/etc/kobo-sync.env` (mode 600), loaded by the systemd drop-in `/etc/systemd/system/kobo-sync.service.d/auth.conf`. Calibre-Web runs alongside on port 8083.

**Kobo Sync (primary Calibre -> Kobo path)**: Calibre-Web's native Kobo sync is enabled (`config_kobo_sync=1`, `config_kobo_proxy=0`) and the Kobo's `api_endpoint` in `.kobo/Kobo/Kobo eReader.conf` points to `http://192.168.10.107:8083/kobo/<token>`. Only books on the "Kobo" shelf sync (`kobo_only_shelves_sync=1` for admin); removing a book from the shelf removes it from the Kobo on next sync. Calibre-Web settings live in `/home/kobo/.calibre-web/app.db`. Two gotchas already hit: Kobo sync needs `jsonschema` in Calibre-Web's venv (without it `/v1/library/sync` fails with `'NoneType' object has no attribute 'SyncToken'`), and with the store proxy ON the Kobo store rejects the forwarded token ("Invalid token version") so sync aborts; hence proxy OFF, which means Kobo store purchases don't sync while the endpoint points to Calibre-Web.

**Library on CT101**: `/home/kobo/calibre-library` is a copy of the Mac library (`~/Biblioteca di calibre`, 332 books, copied 2026-09-29 via tar over ssh + `chown kobo:kobo`; CT101 has no `rsync` or `sqlite3`, use tar and python3). Calibre 9.15 on the Mac writes schema version 27, which drops `books.isbn`, `books.lccn` and `books.flags`; Calibre-Web 0.6.25 still queries them and every page returns 500 (`no such column: books.isbn`). Fix applied on the server copy: `ALTER TABLE books ADD COLUMN isbn TEXT DEFAULT ''`, same for `lccn`, and `flags INTEGER NOT NULL DEFAULT 1`. Any fresh copy from the Mac drops them again, so re-add them after each copy (or upgrade Calibre-Web).

## Known gaps

- Tests cover `core/scanner.py`, `core/calibre.py` (`subprocess.run` mocked; USB detection and content server only through patched methods), and auth/allowlist in `web/app.py`. Still no tests for `core/metadata.py` or the other web routes.
- `calibredb` calls have no timeout: a hung `calibredb` blocks the web request.
- `calibre.py` swallows several subprocess failures silently (bare `except`/`pass`) — a failed import or sync may show no error.
