"""Regression tests for the appproxy worker setup endpoint.

The `/setup?token=X` endpoint sets the permit cookie alongside an HTTP
redirect. The redirect must remain non-cacheable — otherwise browsers will
skip the server on later visits and have no chance to reissue an expired
cookie, producing an infinite 401 loop. These tests pin the response shape
(status code + headers + cookie presence) so the cacheable-redirect failure
mode cannot return silently.
"""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import jwt
import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.common.config import PermitHashConfig
from ai.backend.appproxy.common.defs import PERMIT_COOKIE_NAME
from ai.backend.appproxy.common.types import (
    DigestModType,
    FrontendMode,
    FrontendServerMode,
    ProxyProtocol,
)
from ai.backend.appproxy.worker.api.setup import ProxySetupRequestModel, setup
from ai.backend.appproxy.worker.config import PortProxyConfig
from ai.backend.appproxy.worker.types import InteractiveAppInfo

JWT_SECRET = "test-jwt-secret"


def _build_circuit() -> MagicMock:
    circuit = MagicMock()
    circuit.id = uuid4()
    circuit.protocol = ProxyProtocol.HTTP
    circuit.frontend_mode = FrontendMode.PORT
    circuit.port = 30001
    circuit.subdomain = None
    circuit.app_info = InteractiveAppInfo(user_id=uuid4())
    return circuit


def _build_root_ctx() -> MagicMock:
    root_ctx = MagicMock()
    root_ctx.local_config.secrets.jwt_secret = JWT_SECRET
    root_ctx.local_config.permit_hash = PermitHashConfig(
        secret=b"test-permit-hash",
        digest_mod=DigestModType.SHA256,
    )

    config = root_ctx.local_config.proxy_worker
    config.frontend_mode = FrontendServerMode.PORT
    config.tls_advertised = False
    config.tls_listen = False
    # generate_proxy_url() uses isinstance / structural match against
    # PortProxyConfig, so this must be a real instance, not a MagicMock.
    config.port_proxy = PortProxyConfig(
        bind_host="0.0.0.0",
        advertised_host="proxy.test.example",
        bind_port_range=(30000, 31000),
        advertised_port_range=None,
    )
    return root_ctx


def _build_request(token: str, root_ctx: MagicMock) -> web.Request:
    app = web.Application()
    app["_root.context"] = root_ctx
    request = make_mocked_request("GET", f"/setup?token={token}", app=app)
    request["request_id"] = "test-req"
    return request


def _make_token(circuit_id: str) -> str:
    return jwt.encode(
        {"circuit": circuit_id, "redirect": ""},
        JWT_SECRET,
        algorithm="HS256",
    )


class TestSetupRedirectIsNotCacheable:
    """The Set-Cookie-bearing redirect must not be cacheable."""

    @pytest.fixture
    async def response(self) -> web.Response:
        circuit = _build_circuit()
        root_ctx = _build_root_ctx()
        token = _make_token(str(circuit.id))
        request = _build_request(token, root_ctx)
        params = ProxySetupRequestModel(token=token)

        # The decorator wraps `setup`; call the original via __wrapped__
        # to skip request-body parsing.
        inner: Any = cast(Any, setup).__wrapped__
        with patch(
            "ai.backend.appproxy.worker.api.setup.get_circuit_info",
            AsyncMock(return_value=circuit),
        ):
            result = await inner(request, params)
        return cast(web.Response, result)

    async def test_status_is_302_not_308(self, response: web.Response) -> None:
        # 308 is cacheable by default per RFC 7538 §3; using HTTPFound (302)
        # downgrades from "cacheable by default" to "heuristically cacheable".
        # The Cache-Control header below is what actually guarantees no caching,
        # but pinning the status code prevents accidental reverts.
        assert response.status == 302

    async def test_cache_control_is_no_store(self, response: web.Response) -> None:
        assert response.headers.get("Cache-Control") == "no-store"

    async def test_permit_cookie_is_still_issued(self, response: web.Response) -> None:
        cookie = response.cookies.get(PERMIT_COOKIE_NAME)
        assert cookie is not None
        assert cookie["max-age"] == "604800"
