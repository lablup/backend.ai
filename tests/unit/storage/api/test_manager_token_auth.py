"""``token_auth_middleware`` checks the manager's storage-proxy secret."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from aiohttp.typedefs import Handler

from ai.backend.storage.api.manager import token_auth_middleware

_SECRET = "storage-proxy-secret"
_TOKEN_HEADER = "X-BackendAI-Storage-Auth-Token"


class TestTokenAuthMiddleware:
    @pytest.fixture
    def app(self) -> web.Application:
        app = web.Application()
        app["ctx"] = MagicMock()
        app["ctx"].local_config.api.manager.secret = _SECRET
        return app

    @pytest.fixture
    def handled(self) -> list[web.Request]:
        return []

    @pytest.fixture
    def handler(self, handled: list[web.Request]) -> Handler:
        async def _handler(request: web.Request) -> web.StreamResponse:
            handled.append(request)
            return web.Response()

        return _handler

    async def test_the_shared_secret_passes(
        self, app: web.Application, handler: Handler, handled: list[web.Request]
    ) -> None:
        request = make_mocked_request("GET", "/", headers={_TOKEN_HEADER: _SECRET}, app=app)

        await token_auth_middleware(request, handler)

        assert handled == [request]

    @pytest.mark.parametrize(
        "token",
        [f"{_SECRET}x", _SECRET[:-1], "시크릿"],
        ids=["longer", "prefix", "non-ascii"],
    )
    async def test_any_other_token_is_forbidden(
        self, app: web.Application, handler: Handler, handled: list[web.Request], token: str
    ) -> None:
        request = make_mocked_request("GET", "/", headers={_TOKEN_HEADER: token}, app=app)

        with pytest.raises(web.HTTPForbidden):
            await token_auth_middleware(request, handler)

        assert handled == []
