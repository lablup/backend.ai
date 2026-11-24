from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from datetime import datetime
from pathlib import Path
from typing import override

import aiohttp
import pytest
from yarl import URL

from ai.backend.client.v2.auth import AuthStrategy
from ai.backend.client.v2.base_client import BackendAIAuthClient
from ai.backend.client.v2.config import ClientConfig

_ENDPOINT = URL("http://manager.example")


class _NoAuth(AuthStrategy):
    @override
    def sign(
        self,
        method: str,
        version: str,
        endpoint: URL,
        date: datetime,
        rel_url: str,
        content_type: str,
    ) -> Mapping[str, str]:
        return {}


@pytest.fixture
async def saved_cookie_file(tmp_path: Path) -> Path:
    jar = aiohttp.CookieJar(unsafe=True)
    jar.update_cookies({"AIOHTTP_SESSION": "stored-session"}, _ENDPOINT)
    path = tmp_path / "cookie.dat"
    jar.save(path)
    return path


@pytest.fixture
async def client_with_cookie_file(saved_cookie_file: Path) -> AsyncIterator[BackendAIAuthClient]:
    config = ClientConfig(
        endpoint=_ENDPOINT, endpoint_type="session", cookie_file=saved_cookie_file
    )
    client = await BackendAIAuthClient.create(config, _NoAuth())
    yield client
    await client.close()


class TestCookieFile:
    async def test_session_sends_the_cookies_saved_in_the_file(
        self, client_with_cookie_file: BackendAIAuthClient
    ) -> None:
        cookies = client_with_cookie_file.session.cookie_jar.filter_cookies(_ENDPOINT)

        assert cookies["AIOHTTP_SESSION"].value == "stored-session"
