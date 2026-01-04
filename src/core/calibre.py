"""Calibre integration via calibredb and calibre CLI tools"""

from __future__ import annotations

import subprocess
import shutil
import os
import re
import socket
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass


def get_local_ip() -> str:
    """Get the local IP address of this machine on the network"""
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

from src.core.scanner import Ebook


class CalibreError(Exception):
    """Raised when Calibre operations fail"""
    pass


@dataclass
class DeviceInfo:
    """Information about a connected device"""
    name: str
    path: str
    connected: bool = False


class CalibreManager:
    def __init__(self, calibredb_path: Optional[str] = None):
        self.calibre_base = "/Applications/calibre.app/Contents/MacOS"
        self.calibredb = calibredb_path or self._find_calibredb()
        self.calibre_debug = self._find_tool("calibre-debug")
        self.calibre_server = self._find_tool("calibre-server")
        self._server_process = None

    def _find_calibredb(self) -> str:
        """Find calibredb executable"""
        macos_path = f"{self.calibre_base}/calibredb"
        if Path(macos_path).exists():
            return macos_path

        path = shutil.which("calibredb")
        if path:
            return path

        raise CalibreError(
            "calibredb not found. Please install Calibre or specify the path."
        )

    def _find_tool(self, name: str) -> Optional[str]:
        """Find a calibre tool"""
        macos_path = f"{self.calibre_base}/{name}"
        if Path(macos_path).exists():
            return macos_path
        return shutil.which(name)

    def _run(self, *args, tool: str = None) -> subprocess.CompletedProcess:
        """Run a calibre command"""
        executable = tool or self.calibredb
        cmd = [executable, *args]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 and "already exist" not in result.stderr.lower():
            raise CalibreError(f"calibre error: {result.stderr}")
        return result

    def get_library_path(self) -> Optional[Path]:
        """Get the path to the Calibre library"""
        # Try common locations
        home = Path.home()
        common_paths = [
            home / "Calibre Library",
            home / "Documents" / "Calibre Library",
            home / "Library" / "Calibre Library",
        ]
        for path in common_paths:
            if path.exists():
                return path

        # Try to get from calibredb
        try:
            result = self._run("list", "--limit", "0")
            # Parse library path from output if available
            return common_paths[0] if common_paths[0].exists() else None
        except:
            return None

    def import_books(self, ebooks: List[Ebook]) -> List[int]:
        """Import ebooks into Calibre library. Returns list of book IDs."""
        imported_ids = []

        for ebook in ebooks:
            try:
                result = self._run("add", str(ebook.path))
                # Parse the output to get the book ID
                for line in result.stdout.splitlines():
                    if "Added book ids:" in line:
                        ids_str = line.split(":")[-1].strip()
                        for id_str in ids_str.split(","):
                            try:
                                imported_ids.append(int(id_str.strip()))
                            except ValueError:
                                pass
            except CalibreError:
                # Book might already exist, continue
                pass

        return imported_ids

    def check_kobo_usb(self) -> Optional[DeviceInfo]:
        """Check if a Kobo is connected via USB"""
        # Look for Kobo mount points on macOS
        volumes = Path("/Volumes")
        if not volumes.exists():
            return None

        for vol in volumes.iterdir():
            if vol.is_dir():
                # Check for Kobo-specific files
                kobo_dir = vol / ".kobo"
                if kobo_dir.exists():
                    return DeviceInfo(
                        name=vol.name,
                        path=str(vol),
                        connected=True
                    )
        return None

    def send_to_kobo_usb(self, ebooks: List[Ebook], device: DeviceInfo) -> int:
        """Send ebooks directly to USB-connected Kobo"""
        sent_count = 0
        kobo_books_dir = Path(device.path)

        for ebook in ebooks:
            try:
                # Determine destination based on format
                dest_dir = kobo_books_dir
                dest_file = dest_dir / ebook.path.name

                # Copy file
                shutil.copy2(ebook.path, dest_file)
                sent_count += 1
            except Exception as e:
                print(f"Error copying {ebook.path}: {e}")

        return sent_count

    def import_and_send_usb(self, ebooks: List[Ebook]) -> Tuple[int, int]:
        """Import books to Calibre and send to USB-connected Kobo"""
        # First import to Calibre
        imported_ids = self.import_books(ebooks)

        # Check for USB Kobo
        device = self.check_kobo_usb()
        if device:
            sent = self.send_to_kobo_usb(ebooks, device)
            return len(imported_ids), sent

        return len(imported_ids), 0

    def get_content_server_url(self, for_remote: bool = False) -> Optional[str]:
        """Get URL for Calibre content server if running

        Args:
            for_remote: If True, return URL with local network IP (for Kobo access)
                       If False, return localhost URL
        """
        # Default port for Calibre content server
        ports = [8080, 8180, 8081]

        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                if result == 0:
                    if for_remote:
                        return f"http://{get_local_ip()}:{port}"
                    return f"http://127.0.0.1:{port}"
            except:
                pass

        return None

    def start_content_server(self, port: int = 8080) -> Tuple[str, str]:
        """Start Calibre content server for OPDS access

        Returns:
            Tuple of (local_url, network_url)
        """
        if not self.calibre_server:
            raise CalibreError("calibre-server not found")

        # Check if already running
        existing_url = self.get_content_server_url()
        if existing_url:
            network_url = self.get_content_server_url(for_remote=True)
            return existing_url, network_url

        library_path = self.get_library_path()
        if not library_path:
            raise CalibreError("Calibre library not found")

        # Start server in background, listen on all interfaces
        try:
            self._server_process = subprocess.Popen(
                [self.calibre_server, str(library_path), "--port", str(port), "--listen-on", "0.0.0.0"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            local_ip = get_local_ip()
            return f"http://127.0.0.1:{port}", f"http://{local_ip}:{port}"
        except Exception as e:
            raise CalibreError(f"Failed to start content server: {e}")

    def get_opds_url(self, for_remote: bool = True) -> str:
        """Get OPDS feed URL for Kobo browser access

        Args:
            for_remote: If True, return URL with network IP (for Kobo)
        """
        server_url = self.get_content_server_url(for_remote=for_remote)
        if server_url:
            return f"{server_url}/opds"
        return ""

    def send_to_device(self, ebooks: List[Ebook]) -> dict:
        """
        Send ebooks to Kobo - tries USB first, then provides OPDS info
        Returns dict with status info
        """
        result = {
            "imported": 0,
            "sent_usb": 0,
            "kobo_connected": False,
            "opds_url": "",
            "local_ip": get_local_ip(),
            "message": ""
        }

        # Import books first
        imported_ids = self.import_books(ebooks)
        result["imported"] = len(imported_ids)

        # Check for USB Kobo
        device = self.check_kobo_usb()
        if device:
            result["kobo_connected"] = True
            result["sent_usb"] = self.send_to_kobo_usb(ebooks, device)
            result["message"] = f"Inviati {result['sent_usb']} ebook al Kobo ({device.name}) via USB"
            return result

        # No USB, check/start content server for OPDS
        opds_url = self.get_opds_url(for_remote=True)
        if opds_url:
            result["opds_url"] = opds_url
            result["message"] = f"Libri importati in Calibre. Accedi da Kobo browser: {opds_url}"
        else:
            # Try to start server
            try:
                local_url, network_url = self.start_content_server()
                result["opds_url"] = f"{network_url}/opds"
                result["message"] = f"Server avviato. Accedi da Kobo browser: {result['opds_url']}"
            except:
                result["message"] = (
                    "Libri importati in Calibre. "
                    "Per sincronizzare: Calibre > Connetti/Condividi > Avvia connessione wireless"
                )

        return result

    def list_books(self, search: str = "") -> str:
        """List books in library, optionally filtered by search"""
        if search:
            result = self._run("list", "--search", search)
        else:
            result = self._run("list")
        return result.stdout
