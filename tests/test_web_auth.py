"""Tests for web app auth and the Kobo IP allowlist"""

import pytest

from src.web import app as web

KOBO_IP = "192.168.10.130"
OTHER_IP = "192.168.10.125"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(web, "KOBO_DEVICE_IPS", {KOBO_IP})
    monkeypatch.setattr(web, "AUTH_PASSWORD", "secret")
    monkeypatch.setattr(web, "current_ebooks", [])
    return web.app.test_client()


def _get(client, path, ip, auth=None):
    return client.get(path, environ_base={"REMOTE_ADDR": ip}, auth=auth)


class TestKoboAllowlist:
    def test_kobo_page_open_from_kobo_ip(self, client):
        assert _get(client, "/kobo", KOBO_IP).status_code == 200

    def test_kobo_page_requires_auth_from_other_ip(self, client):
        assert _get(client, "/kobo", OTHER_IP).status_code == 401

    def test_download_reachable_from_kobo_ip(self, client):
        # No books scanned: past the auth check, the route answers 404
        assert _get(client, "/download/0", KOBO_IP).status_code == 404

    def test_main_page_still_requires_auth_from_kobo_ip(self, client):
        assert _get(client, "/", KOBO_IP).status_code == 401

    def test_api_still_requires_auth_from_kobo_ip(self, client):
        assert _get(client, "/api/scan?path=downloads", KOBO_IP).status_code == 401

    def test_valid_credentials_work_from_any_ip(self, client):
        auth = (web.AUTH_USERNAME, "secret")
        assert _get(client, "/kobo", OTHER_IP, auth=auth).status_code == 200

    def test_empty_allowlist_requires_auth(self, client, monkeypatch):
        monkeypatch.setattr(web, "KOBO_DEVICE_IPS", set())
        assert _get(client, "/kobo", KOBO_IP).status_code == 401
