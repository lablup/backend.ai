from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import UUID

import pytest
from aiohttp import web

from ai.backend.appproxy.common.errors import AuthorizationFailed
from ai.backend.appproxy.coordinator.api.conf import conf_v2
from ai.backend.appproxy.coordinator.api.types import ConfRequestModel
from ai.backend.appproxy.coordinator.models import Token
from ai.backend.common.exception import BackendAISchemaValidationFailed

_API_SECRET = "coordinator-api-secret"


@pytest.fixture
def conf_request_body() -> dict[str, Any]:
    return {
        "login_session_token": None,
        "kernel_host": "10.0.0.5",
        "kernel_port": 30000,
        "session": {
            "id": str(UUID(int=1)),
            "user_uuid": str(UUID(int=2)),
            "group_id": str(UUID(int=3)),
            "access_key": "AKIATEST",
            "domain_name": "default",
        },
    }


@dataclass(frozen=True)
class _ConfRequestHeadersCase:
    description: str
    headers: dict[str, str]


@dataclass(frozen=True)
class _ConfRequestSituation:
    request: Mock
    coordinator_db_session: Mock


class TestConfV2Authentication:
    @pytest.fixture
    def conf_request_situation(
        self, case: _ConfRequestHeadersCase, conf_request_body: dict[str, Any]
    ) -> _ConfRequestSituation:
        coordinator_db_session = Mock(spec_set=["add"])
        begin_session_context = MagicMock()
        begin_session_context.__aenter__.return_value = coordinator_db_session
        begin_session_context.__aexit__.return_value = False
        root_ctx = Mock()
        root_ctx.local_config.secrets.api_secret = _API_SECRET
        root_ctx.db.begin_session.return_value = begin_session_context

        request = Mock(spec=web.Request)
        request.app = {"_root.context": root_ctx}
        request.headers = case.headers
        request.can_read_body = True
        request.content_type = "application/json"
        request.text = AsyncMock(return_value=json.dumps(conf_request_body))
        return _ConfRequestSituation(
            request=request,
            coordinator_db_session=coordinator_db_session,
        )

    @pytest.mark.parametrize(
        "case",
        [
            _ConfRequestHeadersCase(description="no_token", headers={}),
            _ConfRequestHeadersCase(
                description="wrong_token",
                headers={"X-BackendAI-Token": "not-the-api-secret"},
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_request_without_api_secret_is_rejected_and_stores_nothing(
        self, conf_request_situation: _ConfRequestSituation
    ) -> None:
        with pytest.raises(AuthorizationFailed):
            await conf_v2(conf_request_situation.request)

        conf_request_situation.coordinator_db_session.add.assert_not_called()

    @pytest.mark.parametrize(
        "case",
        [
            _ConfRequestHeadersCase(
                description="api_secret",
                headers={"X-BackendAI-Token": _API_SECRET},
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_request_with_api_secret_stores_and_returns_a_token(
        self, conf_request_situation: _ConfRequestSituation
    ) -> None:
        response = await conf_v2(conf_request_situation.request)

        assert isinstance(response, web.Response)
        assert response.status == HTTPStatus.OK
        assert response.text is not None
        stored_token = conf_request_situation.coordinator_db_session.add.call_args.args[0]
        assert isinstance(stored_token, Token)
        assert json.loads(response.text) == {"token": str(stored_token.id)}
        assert stored_token.kernel_host == "10.0.0.5"
        assert stored_token.kernel_port == 30000


@dataclass(frozen=True)
class _AcceptedKernelHostCase:
    kernel_host: str
    stored_kernel_host: str


class TestConfRequestModelKernelAddress:
    @pytest.mark.parametrize(
        "case",
        [
            _AcceptedKernelHostCase(kernel_host="10.0.0.5", stored_kernel_host="10.0.0.5"),
            _AcceptedKernelHostCase(kernel_host="127.0.0.1", stored_kernel_host="127.0.0.1"),
            _AcceptedKernelHostCase(kernel_host="2001:DB8:0::1", stored_kernel_host="2001:db8::1"),
            _AcceptedKernelHostCase(kernel_host="agent-1", stored_kernel_host="agent-1"),
            _AcceptedKernelHostCase(kernel_host="agent_1", stored_kernel_host="agent_1"),
            _AcceptedKernelHostCase(
                kernel_host="host.docker.internal",
                stored_kernel_host="host.docker.internal",
            ),
        ],
        ids=lambda case: case.kernel_host,
    )
    def test_accepts_ip_address_or_host_name(
        self, conf_request_body: dict[str, Any], case: _AcceptedKernelHostCase
    ) -> None:
        params = ConfRequestModel.model_validate({
            **conf_request_body,
            "kernel_host": case.kernel_host,
        })

        assert params.kernel_host == case.stored_kernel_host

    @pytest.mark.parametrize(
        "kernel_host",
        [
            "",
            "http://10.0.0.5",
            "10.0.0.5:30000",
            "10.0.0.5/path",
            "user@10.0.0.5",
            "10.0.0.5?a=1",
            "10.0.0.5#fragment",
            "10.0.0.5 ",
            "agent-1\n",
            "[::1]",
            "-agent",
            "a" * 256,
        ],
    )
    def test_rejects_anything_else_as_kernel_host(
        self, conf_request_body: dict[str, Any], kernel_host: str
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ConfRequestModel.model_validate({**conf_request_body, "kernel_host": kernel_host})

    @pytest.mark.parametrize("kernel_port", [1, 65535])
    def test_accepts_kernel_port_in_range(
        self, conf_request_body: dict[str, Any], kernel_port: int
    ) -> None:
        params = ConfRequestModel.model_validate({**conf_request_body, "kernel_port": kernel_port})

        assert params.kernel_port == kernel_port

    @pytest.mark.parametrize("kernel_port", [-1, 0, 65536])
    def test_rejects_kernel_port_out_of_range(
        self, conf_request_body: dict[str, Any], kernel_port: int
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ConfRequestModel.model_validate({**conf_request_body, "kernel_port": kernel_port})
