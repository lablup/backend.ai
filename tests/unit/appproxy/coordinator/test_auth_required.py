"""``auth_required`` checks the App Proxy API secret in the ``X-BackendAI-Token`` header."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from aiohttp.typedefs import Handler

from ai.backend.appproxy.common.errors import AuthorizationFailed
from ai.backend.appproxy.coordinator.api.utils import auth_required

_SECRET = "appproxy-api-secret"


class TestAuthRequiredToken:
    @pytest.fixture
    def app(self) -> web.Application:
        app = web.Application()
        app["_root.context"] = MagicMock()
        app["_root.context"].local_config.secrets.api_secret = _SECRET
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

    @pytest.mark.parametrize(
        "token",
        [_SECRET, f"Bearer {_SECRET}", f"BackendAI {_SECRET}"],
        ids=["bare", "bearer", "backendai"],
    )
    async def test_the_secret_in_each_accepted_form_passes(
        self, app: web.Application, handler: Handler, handled: list[web.Request], token: str
    ) -> None:
        request = make_mocked_request("GET", "/", headers={"X-BackendAI-Token": token}, app=app)

        await auth_required("manager")(handler)(request)

        assert handled == [request]

    @pytest.mark.parametrize(
        "token",
        [f"{_SECRET}x", _SECRET[:-1], "시크릿"],
        ids=["longer", "prefix", "non-ascii"],
    )
    async def test_any_other_token_is_refused(
        self, app: web.Application, handler: Handler, handled: list[web.Request], token: str
    ) -> None:
        request = make_mocked_request("GET", "/", headers={"X-BackendAI-Token": token}, app=app)

        with pytest.raises(AuthorizationFailed):
            await auth_required("manager")(handler)(request)

        assert handled == []
