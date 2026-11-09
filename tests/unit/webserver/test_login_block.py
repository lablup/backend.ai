from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from pytest_mock import MockerFixture

from ai.backend.web import server


class TestLoginBlock:
    @pytest.fixture
    def blocked_request(self, mocker: MockerFixture) -> web.Request:
        request = make_mocked_request("POST", "/server/login")
        config = MagicMock()
        config.session.login_block_time = 60
        config.session.login_allowed_fail_count = 10
        request.app["config"] = config
        client = MagicMock()
        client.get_login_history = AsyncMock(
            return_value=json.dumps({
                "last_login_attempt": time.time() - 30,
                "login_fail_count": 10,
            }).encode()
        )
        client.set_login_block = AsyncMock()
        client.record_login_failure = AsyncMock()
        request.app["redis"] = client
        session = MagicMock()
        session.get.return_value = False
        mocker.patch.object(server, "get_session", AsyncMock(return_value=session))
        mocker.patch.object(server, "get_client_ip", return_value="127.0.0.1")
        mocker.patch.object(
            request,
            "text",
            AsyncMock(
                return_value=json.dumps({
                    "username": "user@example.com",
                    "password": "wrong",
                })
            ),
        )
        return request

    async def test_repeated_blocked_requests_do_not_update_history(
        self, blocked_request: web.Request
    ) -> None:
        for _ in range(3):
            with pytest.raises(web.HTTPTooManyRequests):
                await server.login_handler(blocked_request)
        blocked_request.app["redis"].record_login_failure.assert_not_awaited()
