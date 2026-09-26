"""Tests for CalibreManager"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.calibre import CalibreError, CalibreManager, DeviceInfo
from src.core.scanner import Ebook


@pytest.fixture
def manager():
    return CalibreManager(calibredb_path="/usr/bin/calibredb")


def _ok(*args, **kwargs):
    return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")


def _result(returncode=0, stdout="", stderr=""):
    def run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)
    return run


class TestLibraryPath:
    def test_uses_calibre_library_env(self, manager, tmp_path, monkeypatch):
        monkeypatch.setenv("CALIBRE_LIBRARY", str(tmp_path))
        assert manager.get_library_path() == tmp_path

    def test_env_pointing_to_missing_dir_returns_none(self, manager, tmp_path, monkeypatch):
        monkeypatch.setenv("CALIBRE_LIBRARY", str(tmp_path / "missing"))
        assert manager.get_library_path() is None

    def test_falls_back_to_home_without_env(self, manager, tmp_path, monkeypatch):
        monkeypatch.delenv("CALIBRE_LIBRARY", raising=False)
        (tmp_path / "Calibre Library").mkdir()
        with patch("pathlib.Path.home", return_value=tmp_path):
            assert manager.get_library_path() == tmp_path / "Calibre Library"


class TestRunWithLibrary:
    def test_calibredb_gets_with_library(self, manager, monkeypatch):
        monkeypatch.setenv("CALIBRE_LIBRARY", "/data/lib")
        with patch("subprocess.run", side_effect=_ok) as run:
            manager._run("list")
        assert run.call_args[0][0] == ["/usr/bin/calibredb", "list", "--with-library", "/data/lib"]

    def test_no_with_library_without_env(self, manager, monkeypatch):
        monkeypatch.delenv("CALIBRE_LIBRARY", raising=False)
        with patch("subprocess.run", side_effect=_ok) as run:
            manager._run("list")
        assert run.call_args[0][0] == ["/usr/bin/calibredb", "list"]

    def test_other_tools_do_not_get_with_library(self, manager, monkeypatch):
        monkeypatch.setenv("CALIBRE_LIBRARY", "/data/lib")
        with patch("subprocess.run", side_effect=_ok) as run:
            manager._run("--version", tool="/usr/bin/calibre-server")
        assert run.call_args[0][0] == ["/usr/bin/calibre-server", "--version"]


class TestRunErrors:
    def test_nonzero_exit_raises(self, manager):
        with patch("subprocess.run", side_effect=_result(1, stderr="library locked")):
            with pytest.raises(CalibreError, match="library locked"):
                manager._run("list")

    def test_already_exists_is_not_an_error(self, manager):
        with patch("subprocess.run", side_effect=_result(1, stderr="Book Already Exists in library")):
            result = manager._run("add", "/books/a.epub")
        assert result.returncode == 1


class TestImportBooks:
    def test_parses_added_ids(self, manager, monkeypatch):
        monkeypatch.delenv("CALIBRE_LIBRARY", raising=False)
        ebooks = [Ebook(path=Path("/books/a.epub"))]
        with patch("subprocess.run", side_effect=_result(stdout="Added book ids: 12, 13\n")) as run:
            ids = manager.import_books(ebooks)
        assert ids == [12, 13]
        assert run.call_args[0][0] == ["/usr/bin/calibredb", "add", "/books/a.epub"]

    def test_one_call_per_book(self, manager):
        ebooks = [Ebook(path=Path("/books/a.epub")), Ebook(path=Path("/books/b.epub"))]
        outputs = iter(["Added book ids: 1\n", "Added book ids: 2\n"])

        def run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, stdout=next(outputs), stderr="")

        with patch("subprocess.run", side_effect=run):
            assert manager.import_books(ebooks) == [1, 2]

    def test_duplicate_yields_no_id(self, manager):
        ebooks = [Ebook(path=Path("/books/a.epub"))]
        with patch("subprocess.run", side_effect=_result(1, stderr="already exist")):
            assert manager.import_books(ebooks) == []

    def test_ignores_non_numeric_ids(self, manager):
        ebooks = [Ebook(path=Path("/books/a.epub"))]
        with patch("subprocess.run", side_effect=_result(stdout="Added book ids: 5, x\n")):
            assert manager.import_books(ebooks) == [5]

    def test_failure_on_one_book_does_not_stop_the_others(self, manager):
        ebooks = [Ebook(path=Path("/books/bad.epub")), Ebook(path=Path("/books/ok.epub"))]
        results = iter([
            (1, "", "corrupt file"),
            (0, "Added book ids: 7\n", ""),
        ])

        def run(cmd, **kwargs):
            code, out, err = next(results)
            return subprocess.CompletedProcess(cmd, code, stdout=out, stderr=err)

        with patch("subprocess.run", side_effect=run):
            assert manager.import_books(ebooks) == [7]


class TestListBooks:
    def test_without_search(self, manager, monkeypatch):
        monkeypatch.delenv("CALIBRE_LIBRARY", raising=False)
        with patch("subprocess.run", side_effect=_result(stdout="1 Title\n")) as run:
            assert manager.list_books() == "1 Title\n"
        assert run.call_args[0][0] == ["/usr/bin/calibredb", "list"]

    def test_with_search(self, manager, monkeypatch):
        monkeypatch.delenv("CALIBRE_LIBRARY", raising=False)
        with patch("subprocess.run", side_effect=_ok) as run:
            manager.list_books("author:Eco")
        assert run.call_args[0][0] == ["/usr/bin/calibredb", "list", "--search", "author:Eco"]


class TestSendToKoboUsb:
    def test_copies_files_to_device(self, manager, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.epub").write_bytes(b"epub")
        device_dir = tmp_path / "KOBOeReader"
        device_dir.mkdir()
        device = DeviceInfo(name="KOBOeReader", path=str(device_dir), connected=True)

        sent = manager.send_to_kobo_usb([Ebook(path=src / "a.epub")], device)

        assert sent == 1
        assert (device_dir / "a.epub").read_bytes() == b"epub"

    def test_missing_source_is_not_counted(self, manager, tmp_path):
        device = DeviceInfo(name="KOBOeReader", path=str(tmp_path), connected=True)
        sent = manager.send_to_kobo_usb([Ebook(path=tmp_path / "missing.epub")], device)
        assert sent == 0


class TestSendToDevice:
    @pytest.fixture(autouse=True)
    def _no_network(self):
        with patch("src.core.calibre.get_local_ip", return_value="192.168.10.50"):
            yield

    def test_usb_path(self, manager, tmp_path):
        device = DeviceInfo(name="KOBOeReader", path=str(tmp_path), connected=True)
        with patch.object(manager, "import_books", return_value=[1]), \
             patch.object(manager, "check_kobo_usb", return_value=device), \
             patch.object(manager, "send_to_kobo_usb", return_value=1):
            result = manager.send_to_device([Ebook(path=Path("/books/a.epub"))])

        assert result["imported"] == 1
        assert result["kobo_connected"] is True
        assert result["sent_usb"] == 1
        assert "via USB" in result["message"]

    def test_uses_running_content_server(self, manager):
        with patch.object(manager, "import_books", return_value=[1]), \
             patch.object(manager, "check_kobo_usb", return_value=None), \
             patch.object(manager, "get_opds_url", return_value="http://192.168.10.50:8080/opds"):
            result = manager.send_to_device([])

        assert result["kobo_connected"] is False
        assert result["opds_url"] == "http://192.168.10.50:8080/opds"

    def test_starts_content_server_when_none_running(self, manager):
        with patch.object(manager, "import_books", return_value=[]), \
             patch.object(manager, "check_kobo_usb", return_value=None), \
             patch.object(manager, "get_opds_url", return_value=""), \
             patch.object(manager, "start_content_server",
                          return_value=("http://127.0.0.1:8080", "http://192.168.10.50:8080")):
            result = manager.send_to_device([])

        assert result["opds_url"] == "http://192.168.10.50:8080/opds"
        assert result["message"].startswith("Server avviato")

    def test_falls_back_to_wireless_hint_when_server_fails(self, manager):
        with patch.object(manager, "import_books", return_value=[]), \
             patch.object(manager, "check_kobo_usb", return_value=None), \
             patch.object(manager, "get_opds_url", return_value=""), \
             patch.object(manager, "start_content_server", side_effect=CalibreError("no server")):
            result = manager.send_to_device([])

        assert result["opds_url"] == ""
        assert "connessione wireless" in result["message"]
