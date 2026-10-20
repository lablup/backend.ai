from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock

import jwt
import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.common.errors import AuthorizationFailed
from ai.backend.appproxy.coordinator.api.utils import auth_required_middleware

API_SECRET = "api-secret"


@dataclass(frozen=True)
class _HeaderCase:
    name: str
    headers: dict[str, str]


@pytest.fixture
def app() -> web.Application:
    app = web.Application()
    root_ctx = Mock()
    root_ctx.local_config.secrets.api_secret = API_SECRET
    app["_root.context"] = root_ctx
    return app


@pytest.fixture
def next_handler() -> AsyncMock:
    return AsyncMock(return_value=web.Response())


class TestAuthRequiredMiddleware:
    @pytest.mark.parametrize(
        "case",
        [
            _HeaderCase(name="token", headers={"X-BackendAI-Token": API_SECRET}),
            _HeaderCase(name="token-bearer", headers={"X-BackendAI-Token": f"Bearer {API_SECRET}"}),
            _HeaderCase(
                name="token-backendai", headers={"X-BackendAI-Token": f"BackendAI {API_SECRET}"}
            ),
            _HeaderCase(
                name="jwt",
                headers={
                    "Authorization": f"Bearer {jwt.encode({}, API_SECRET, algorithm='HS256')}"
                },
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_secret_passes(
        self, app: web.Application, next_handler: AsyncMock, case: _HeaderCase
    ) -> None:
        request = make_mocked_request("POST", "/", headers=case.headers, app=app)
        await auth_required_middleware(request, next_handler)
        next_handler.assert_awaited_once_with(request)

    @pytest.mark.parametrize(
        "case",
        [
            _HeaderCase(name="missing", headers={}),
            _HeaderCase(name="wrong-token", headers={"X-BackendAI-Token": "wrong"}),
            _HeaderCase(
                name="wrong-jwt",
                headers={"Authorization": f"Bearer {jwt.encode({}, 'wrong', algorithm='HS256')}"},
            ),
            _HeaderCase(name="unsupported-method", headers={"Authorization": "Basic abc"}),
        ],
        ids=lambda case: case.name,
    )
    async def test_missing_or_wrong_secret_is_rejected(
        self, app: web.Application, next_handler: AsyncMock, case: _HeaderCase
    ) -> None:
        request = make_mocked_request("POST", "/", headers=case.headers, app=app)
        with pytest.raises(AuthorizationFailed):
            await auth_required_middleware(request, next_handler)
        next_handler.assert_not_awaited()
