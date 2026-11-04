"""``/v2/conf`` checks the App Proxy API secret before it reads the session."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from http import HTTPStatus
from typing import Any
from unittest.mock import MagicMock

import pytest
from aiohttp import web

from ai.backend.appproxy.common.types import SessionConfig
from ai.backend.appproxy.coordinator.api.conf import conf_v2
from ai.backend.appproxy.coordinator.api.types import ConfRequestModel
from ai.backend.appproxy.coordinator.server import exception_middleware

_SECRET = "appproxy-api-secret"


class TestConfToken:
    @pytest.fixture
    def make_client(self, aiohttp_client: Any) -> Callable[[str], Awaitable[Any]]:
        async def _make(secret: str) -> Any:
            app = web.Application(middlewares=[exception_middleware])
            root_ctx = MagicMock()
            root_ctx.local_config.proxy_coordinator.allow_unauthorized_configure_request = False
            root_ctx.local_config.secrets.api_secret = secret
            app["_root.context"] = root_ctx
            app.router.add_post("/v2/conf", conf_v2)
            return await aiohttp_client(app)

        return _make

    @pytest.fixture
    def body(self) -> str:
        # No session id: past the token check the request is refused with 400.
        return ConfRequestModel(
            login_session_token=None,
            kernel_host="127.0.0.1",
            kernel_port=8080,
            session=SessionConfig(
                id=None,
                user_uuid=uuid.uuid4(),
                project_id=uuid.uuid4(),
                access_key=None,
                domain_name="default",
            ),
        ).model_dump_json()

    async def test_the_shared_secret_passes_the_check(
        self, make_client: Callable[[str], Awaitable[Any]], body: str
    ) -> None:
        client = await make_client(_SECRET)

        resp = await client.post("/v2/conf", data=body, headers={"X-BackendAI-Token": _SECRET})

        assert resp.status == HTTPStatus.BAD_REQUEST

    @pytest.mark.parametrize(
        "token",
        [f"{_SECRET}x", _SECRET[:-1], "시크릿"],
        ids=["longer", "prefix", "non-ascii"],
    )
    async def test_any_other_token_is_refused(
        self, make_client: Callable[[str], Awaitable[Any]], body: str, token: str
    ) -> None:
        client = await make_client(_SECRET)

        resp = await client.post("/v2/conf", data=body, headers={"X-BackendAI-Token": token})

        assert resp.status == HTTPStatus.UNAUTHORIZED

    async def test_a_missing_token_is_refused_even_under_an_empty_secret(
        self, make_client: Callable[[str], Awaitable[Any]], body: str
    ) -> None:
        client = await make_client("")

        resp = await client.post("/v2/conf", data=body)

        assert resp.status == HTTPStatus.UNAUTHORIZED
