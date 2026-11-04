from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import jwt
import pytest
import pytest_mock
from aiohttp import hdrs, web
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.common.config import PermitHashConfig
from ai.backend.appproxy.common.defs import PERMIT_COOKIE_NAME
from ai.backend.appproxy.common.errors import InvalidCredentials
from ai.backend.appproxy.common.types import FrontendMode, FrontendServerMode, ProxyProtocol
from ai.backend.appproxy.worker.api.setup import setup
from ai.backend.appproxy.worker.config import PortProxyConfig
from ai.backend.appproxy.worker.types import InteractiveAppInfo

_JWT_SECRET = "a" * 32
_ANOTHER_JWT_SECRET = "b" * 32
_CIRCUIT_ID = "d0e6f60c-f375-4454-b4d3-e8ee202fa372"
_USER_ID = UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")
_FAR_FUTURE = datetime(2999, 1, 1, tzinfo=UTC)
_LONG_AGO = datetime(2000, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class _RejectedSetupTokenCase:
    claims: Mapping[str, Any]
    signing_secret: str


@pytest.fixture
def worker_app(mocker: pytest_mock.MockerFixture) -> web.Application:
    root_ctx = Mock()
    root_ctx.local_config.secrets.jwt_secret = _JWT_SECRET
    root_ctx.local_config.permit_hash = PermitHashConfig(secret=b"permit-secret")
    worker_config = root_ctx.local_config.proxy_worker
    worker_config.frontend_mode = FrontendServerMode.PORT
    worker_config.port_proxy = Mock(
        spec=PortProxyConfig, advertised_host="proxy.example.com", bind_host="0.0.0.0"
    )
    worker_config.tls_advertised = False
    worker_config.tls_listen = False
    mocker.patch(
        "ai.backend.appproxy.worker.api.setup.get_circuit_info",
        AsyncMock(
            return_value=Mock(
                app_info=InteractiveAppInfo(user_id=_USER_ID),
                protocol=ProxyProtocol.HTTP,
                frontend_mode=FrontendMode.PORT,
                port=10200,
            )
        ),
    )
    app = web.Application()
    app["_root.context"] = root_ctx
    return app


@pytest.fixture
def setup_request_with_a_valid_token(worker_app: web.Application) -> web.Request:
    token = jwt.encode(
        {"circuit": _CIRCUIT_ID, "redirect": "/lab", "jti": "unique-id", "exp": _FAR_FUTURE},
        _JWT_SECRET,
        algorithm="HS256",
    )
    request = make_mocked_request("GET", f"/setup?token={token}", app=worker_app)
    request["request_id"] = "request-id"
    return request


@pytest.fixture
def setup_request_with_a_rejected_token(
    case: _RejectedSetupTokenCase, worker_app: web.Application
) -> web.Request:
    token = jwt.encode(dict(case.claims), case.signing_secret, algorithm="HS256")
    request = make_mocked_request("GET", f"/setup?token={token}", app=worker_app)
    request["request_id"] = "request-id"
    return request


class TestSetupToken:
    async def test_valid_token_redirects_with_a_permit_cookie(
        self, setup_request_with_a_valid_token: web.Request
    ) -> None:
        response = await setup(setup_request_with_a_valid_token)

        assert response.status == HTTPStatus.FOUND
        assert response.headers[hdrs.LOCATION] == "http://proxy.example.com:10200/lab"
        assert PERMIT_COOKIE_NAME in response.cookies

    async def test_token_stays_usable_until_it_expires(
        self, setup_request_with_a_valid_token: web.Request
    ) -> None:
        first_response = await setup(setup_request_with_a_valid_token)
        second_response = await setup(setup_request_with_a_valid_token)

        assert first_response.status == HTTPStatus.FOUND
        assert second_response.status == HTTPStatus.FOUND

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _RejectedSetupTokenCase(
                    claims={"circuit": _CIRCUIT_ID, "jti": "unique-id", "exp": _LONG_AGO},
                    signing_secret=_JWT_SECRET,
                ),
                id="expired",
            ),
            pytest.param(
                _RejectedSetupTokenCase(
                    claims={"circuit": _CIRCUIT_ID, "jti": "unique-id", "exp": _FAR_FUTURE},
                    signing_secret=_ANOTHER_JWT_SECRET,
                ),
                id="signed_with_another_secret",
            ),
            pytest.param(
                _RejectedSetupTokenCase(
                    claims={"circuit": _CIRCUIT_ID, "jti": "unique-id"},
                    signing_secret=_JWT_SECRET,
                ),
                id="without_exp",
            ),
            pytest.param(
                _RejectedSetupTokenCase(
                    claims={"circuit": _CIRCUIT_ID, "exp": _FAR_FUTURE},
                    signing_secret=_JWT_SECRET,
                ),
                id="without_jti",
            ),
            pytest.param(
                _RejectedSetupTokenCase(
                    claims={"jti": "unique-id", "exp": _FAR_FUTURE},
                    signing_secret=_JWT_SECRET,
                ),
                id="without_circuit",
            ),
        ],
    )
    async def test_invalid_token_is_rejected(
        self, setup_request_with_a_rejected_token: web.Request
    ) -> None:
        with pytest.raises(InvalidCredentials):
            await setup(setup_request_with_a_rejected_token)
