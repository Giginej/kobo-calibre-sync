"""Tests for CalibreManager library resolution"""

import subprocess
from unittest.mock import patch

import pytest

from src.core.calibre import CalibreManager


@pytest.fixture
def manager():
    return CalibreManager(calibredb_path="/usr/bin/calibredb")


def _ok(*args, **kwargs):
    return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")


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
