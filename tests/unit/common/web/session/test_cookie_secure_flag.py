from __future__ import annotations

import pytest
from aiohttp import web

from ai.backend.common.web.session import SimpleCookieStorage


class TestCookieSecureFlag:
    """Verify that the Secure flag on AIOHTTP_SESSION cookie
    is controlled by the `secure` parameter of the storage,
    which maps to `config.security.cookie_secure`."""

    @pytest.fixture
    def secure_storage(self) -> SimpleCookieStorage:
        """Simulates production: cookie_secure = true (default)."""
        return SimpleCookieStorage(secure=True)

    @pytest.fixture
    def insecure_storage(self) -> SimpleCookieStorage:
        """Simulates halfstack/dev: cookie_secure = false."""
        return SimpleCookieStorage(secure=False)

    @pytest.fixture
    def default_storage(self) -> SimpleCookieStorage:
        """Storage with secure=None (no explicit setting)."""
        return SimpleCookieStorage()

    async def test_secure_flag_present_when_cookie_secure_enabled(
        self,
        secure_storage: SimpleCookieStorage,
    ) -> None:
        response = web.Response()
        secure_storage.save_cookie(response, "test-session-id", max_age=3600)
        cookie = response.cookies["AIOHTTP_SESSION"]
        assert cookie["secure"] is True

    async def test_secure_flag_absent_when_cookie_secure_disabled(
        self,
        insecure_storage: SimpleCookieStorage,
    ) -> None:
        response = web.Response()
        insecure_storage.save_cookie(response, "test-session-id", max_age=3600)
        cookie = response.cookies["AIOHTTP_SESSION"]
        assert not cookie["secure"]

    async def test_secure_flag_absent_by_default(
        self,
        default_storage: SimpleCookieStorage,
    ) -> None:
        response = web.Response()
        default_storage.save_cookie(response, "test-session-id", max_age=3600)
        cookie = response.cookies["AIOHTTP_SESSION"]
        assert cookie["secure"] == ""

    async def test_httponly_flag_always_present(
        self,
        secure_storage: SimpleCookieStorage,
        insecure_storage: SimpleCookieStorage,
    ) -> None:
        for storage in [secure_storage, insecure_storage]:
            response = web.Response()
            storage.save_cookie(response, "test-session-id", max_age=3600)
            cookie = response.cookies["AIOHTTP_SESSION"]
            assert cookie["httponly"] is True

    async def test_cookie_value_set_correctly(
        self,
        secure_storage: SimpleCookieStorage,
    ) -> None:
        response = web.Response()
        secure_storage.save_cookie(response, "my-session-key", max_age=3600)
        cookie = response.cookies["AIOHTTP_SESSION"]
        assert cookie.value == "my-session-key"

    async def test_set_cookie_header_string(
        self,
        secure_storage: SimpleCookieStorage,
        insecure_storage: SimpleCookieStorage,
        default_storage: SimpleCookieStorage,
    ) -> None:
        cases = [
            ("cookie_secure=true (production)", secure_storage),
            ("cookie_secure=false (halfstack)", insecure_storage),
            ("default (secure=None)", default_storage),
        ]
        for label, storage in cases:
            response = web.Response()
            storage.save_cookie(response, "test-session-id", max_age=3600)
            cookie_header = response.cookies["AIOHTTP_SESSION"].output(header="Set-Cookie:")
            print(f"\n[{label}]\n  {cookie_header}")

            if storage is secure_storage:
                assert "Secure" in cookie_header
            else:
                assert "Secure" not in cookie_header

    async def test_cookie_deleted_when_empty_data(
        self,
        secure_storage: SimpleCookieStorage,
    ) -> None:
        response = web.Response()
        secure_storage.save_cookie(response, "", max_age=3600)
        cookie = response.cookies.get("AIOHTTP_SESSION")
        if cookie is not None:
            assert cookie.value == ""
            assert cookie["max-age"] == "0"
