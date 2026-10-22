from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.common.dto.manager.auth.response import UpdatePasswordNoAuthResponse
from ai.backend.web.server import update_password_no_auth

MANAGER_ENDPOINT = "http://manager:8081"
PASSWORD_UPDATE_BODY = {
    "username": "user@example.com",
    "current_password": "old-password",
    "new_password": "new-password",
}


def _build_app(update_password: AsyncMock) -> web.Application:
    acquired = MagicMock()
    acquired.endpoint = MANAGER_ENDPOINT

    @asynccontextmanager
    async def acquire() -> AsyncIterator[MagicMock]:
        yield acquired

    manager_pool = MagicMock()
    manager_pool.acquire = acquire
    registry = MagicMock()
    registry.auth.update_password_no_auth = update_password

    app = web.Application()
    config = MagicMock()
    config.api.domain = "default"
    app["config"] = config
    app["manager_pool"] = manager_pool
    app["no_auth_client_registries"] = {MANAGER_ENDPOINT: registry}
    app.router.add_route("POST", "/server/update-password-no-auth", update_password_no_auth)
    return app


@pytest.mark.parametrize("status", [400, 401])
async def test_update_password_no_auth_returns_manager_status_on_rejection(
    aiohttp_client: Any, status: int
) -> None:
    update_password = AsyncMock(
        side_effect=BackendAPIError(
            status,
            "Rejected",
            {
                "type": "https://api.backend.ai/probs/rejected",
                "title": "Rejected",
                "msg": "password rejected",
            },
        )
    )
    client = await aiohttp_client(_build_app(update_password))

    resp = await client.post("/server/update-password-no-auth", json=PASSWORD_UPDATE_BODY)

    assert resp.status == status
    assert await resp.json() == {
        "data": {
            "type": "https://api.backend.ai/probs/rejected",
            "title": "Rejected",
            "details": "password rejected",
        },
        "password_changed_at": None,
    }


async def test_update_password_no_auth_returns_200_on_success(aiohttp_client: Any) -> None:
    update_password = AsyncMock(
        return_value=UpdatePasswordNoAuthResponse(password_changed_at="2026-09-29T00:00:00+00:00")
    )
    client = await aiohttp_client(_build_app(update_password))

    resp = await client.post("/server/update-password-no-auth", json=PASSWORD_UPDATE_BODY)

    assert resp.status == 200
    assert await resp.json() == {
        "data": None,
        "password_changed_at": "2026-09-29T00:00:00+00:00",
    }
