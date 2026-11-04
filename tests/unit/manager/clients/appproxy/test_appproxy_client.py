from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any
from uuid import UUID

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.clients.appproxy.client import AppProxyClient
from ai.backend.manager.clients.appproxy.types import (
    AppTokenSessionIdentity,
    CreateSessionAppTokenRequestBody,
)
from ai.backend.manager.errors.appproxy import AppProxyConnectionError, AppProxyResponseError

_API_TOKEN = "coordinator-api-token"
_SESSION_ID = UUID(int=1)
_USER_ID = UUID(int=2)
_PROJECT_ID = UUID(int=3)


@pytest.fixture
def session_app_token_request_body() -> CreateSessionAppTokenRequestBody:
    return CreateSessionAppTokenRequestBody(
        login_session_token=None,
        kernel_host="10.0.0.5",
        kernel_port=30000,
        session=AppTokenSessionIdentity(
            id=SessionID(_SESSION_ID),
            user_uuid=UserID(_USER_ID),
            group_id=ProjectID(_PROJECT_ID),
            access_key=AccessKey("AKIATEST"),
            domain_name="default",
        ),
    )


@dataclass(frozen=True)
class _CoordinatorAnswerCase:
    description: str
    status: int
    body: str
    content_type: str = "application/json"


@dataclass(frozen=True)
class _ReceivedConfRequest:
    api_token: str | None
    body: dict[str, Any]


@dataclass(frozen=True)
class _ClientOfAnsweringCoordinator:
    client: AppProxyClient
    received_conf_requests: list[_ReceivedConfRequest]


class TestCreateSessionAppToken:
    @pytest.fixture
    async def client_of_answering_coordinator(
        self, case: _CoordinatorAnswerCase, aiohttp_server: Any
    ) -> AsyncIterator[_ClientOfAnsweringCoordinator]:
        received_conf_requests: list[_ReceivedConfRequest] = []

        async def answer_conf_request(request: web.Request) -> web.Response:
            received_conf_requests.append(
                _ReceivedConfRequest(
                    api_token=request.headers.get("X-BackendAI-Token"),
                    body=await request.json(),
                )
            )
            return web.Response(
                status=case.status,
                text=case.body,
                content_type=case.content_type,
            )

        app = web.Application()
        app.router.add_post("/v2/conf", answer_conf_request)
        server: TestServer = await aiohttp_server(app)
        address = str(server.make_url("/"))
        async with ClientSession(base_url=address) as client_session:
            yield _ClientOfAnsweringCoordinator(
                client=AppProxyClient(client_session, address, _API_TOKEN),
                received_conf_requests=received_conf_requests,
            )

    @pytest.fixture
    async def client_of_unreachable_coordinator(self) -> AsyncIterator[AppProxyClient]:
        address = "http://127.0.0.1:1"
        async with ClientSession(base_url=address) as client_session:
            yield AppProxyClient(client_session, address, _API_TOKEN)

    @pytest.mark.parametrize(
        "case",
        [
            _CoordinatorAnswerCase(
                description="issued_token",
                status=HTTPStatus.OK,
                body='{"token": "issued-token"}',
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_sends_api_token_and_returns_issued_token(
        self,
        client_of_answering_coordinator: _ClientOfAnsweringCoordinator,
        session_app_token_request_body: CreateSessionAppTokenRequestBody,
    ) -> None:
        token = await client_of_answering_coordinator.client.create_session_app_token(
            session_app_token_request_body
        )

        assert token == "issued-token"
        assert client_of_answering_coordinator.received_conf_requests == [
            _ReceivedConfRequest(
                api_token=_API_TOKEN,
                body={
                    "login_session_token": None,
                    "kernel_host": "10.0.0.5",
                    "kernel_port": 30000,
                    "session": {
                        "id": str(_SESSION_ID),
                        "user_uuid": str(_USER_ID),
                        "group_id": str(_PROJECT_ID),
                        "access_key": "AKIATEST",
                        "domain_name": "default",
                    },
                },
            )
        ]

    @pytest.mark.parametrize(
        "case",
        [
            _CoordinatorAnswerCase(
                description="unauthorized",
                status=HTTPStatus.UNAUTHORIZED,
                body='{"title": "Credential/signature mismatch."}',
            ),
            _CoordinatorAnswerCase(
                description="invalid_kernel_address",
                status=HTTPStatus.BAD_REQUEST,
                body='{"title": "Input validation error"}',
            ),
            _CoordinatorAnswerCase(
                description="no_token_in_body",
                status=HTTPStatus.OK,
                body="{}",
            ),
            _CoordinatorAnswerCase(
                description="body_is_not_json",
                status=HTTPStatus.OK,
                body="<html></html>",
                content_type="text/html",
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_raises_response_error_without_retrying_when_no_token_is_issued(
        self,
        client_of_answering_coordinator: _ClientOfAnsweringCoordinator,
        session_app_token_request_body: CreateSessionAppTokenRequestBody,
    ) -> None:
        with pytest.raises(AppProxyResponseError):
            await client_of_answering_coordinator.client.create_session_app_token(
                session_app_token_request_body
            )

        assert len(client_of_answering_coordinator.received_conf_requests) == 1

    async def test_raises_connection_error_when_coordinator_is_unreachable(
        self,
        client_of_unreachable_coordinator: AppProxyClient,
        session_app_token_request_body: CreateSessionAppTokenRequestBody,
    ) -> None:
        with pytest.raises(AppProxyConnectionError):
            await client_of_unreachable_coordinator.create_session_app_token(
                session_app_token_request_body
            )
