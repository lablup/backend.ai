from __future__ import annotations

import inspect
import logging
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.common.utils import mask_sensitive_keys
from ai.backend.appproxy.coordinator.api.conf import conf_v2
from ai.backend.appproxy.coordinator.api.types import ConfRequestModel
from ai.backend.appproxy.coordinator.api.worker_v2 import TokenResponseModel
from ai.backend.appproxy.coordinator.models import Token

_LOGIN_SESSION_TOKEN = "login-session-token-value"
_SESSION_ID = UUID("f5cd34ba-ae53-4537-a813-09f38496443d")
_CONF_REQUEST_BODY_OF_AN_OLDER_MANAGER: dict[str, Any] = {
    "login_session_token": _LOGIN_SESSION_TOKEN,
    "kernel_host": "10.0.0.1",
    "kernel_port": 8000,
    "session": {
        "id": str(_SESSION_ID),
        "user_uuid": "f38dea23-50fa-42a0-b5ae-338f5f4693f4",
        "group_id": "2de2b969-1d04-48a6-af16-0bc8adb3c831",
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "domain_name": "default",
    },
}


class TestConfLoginSessionToken:
    @pytest.fixture
    def db_session(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def conf_request(self, db_session: MagicMock) -> web.Request:
        root_ctx = MagicMock()
        root_ctx.local_config.proxy_coordinator.allow_unauthorized_configure_request = True
        root_ctx.db.begin_session.return_value.__aenter__.return_value = db_session
        app = web.Application()
        app["_root.context"] = root_ctx
        return make_mocked_request("POST", "/", app=app)

    async def test_token_is_stored_without_the_login_session_token(
        self, conf_request: web.Request, db_session: MagicMock
    ) -> None:
        params = ConfRequestModel.model_validate(_CONF_REQUEST_BODY_OF_AN_OLDER_MANAGER)

        await inspect.unwrap(conf_v2)(conf_request, params)

        stored_token: Token = db_session.add.call_args.args[0]
        assert stored_token.login_session_token is None
        assert stored_token.kernel_host == "10.0.0.1"
        assert stored_token.session_id == _SESSION_ID

    async def test_login_session_token_is_not_logged(
        self, conf_request: web.Request, caplog: pytest.LogCaptureFixture
    ) -> None:
        params = ConfRequestModel.model_validate(_CONF_REQUEST_BODY_OF_AN_OLDER_MANAGER)

        with caplog.at_level(logging.DEBUG, logger="ai.backend.appproxy.coordinator"):
            await inspect.unwrap(conf_v2)(conf_request, params)

        assert _LOGIN_SESSION_TOKEN not in caplog.text


class TestLoginSessionTokenExposure:
    def test_raw_request_params_are_masked_in_logs(self) -> None:
        masked_params = mask_sensitive_keys(_CONF_REQUEST_BODY_OF_AN_OLDER_MANAGER)

        assert masked_params["login_session_token"] == "***"

    def test_token_response_omits_a_value_stored_earlier(self) -> None:
        stored_row = {
            "login_session_token": _LOGIN_SESSION_TOKEN,
            "kernel_host": "10.0.0.1",
            "kernel_port": 8000,
            "session_id": _SESSION_ID,
            "user_uuid": UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
            "group_id": UUID("2de2b969-1d04-48a6-af16-0bc8adb3c831"),
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "domain_name": "default",
        }

        response = TokenResponseModel.model_validate(stored_row)

        assert _LOGIN_SESSION_TOKEN not in response.model_dump_json()
