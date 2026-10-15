from __future__ import annotations

import json
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.common.errors.http import AuthorizationFailed
from ai.backend.appproxy.worker.api.ingress import (
    TOKEN_HEADER,
    IngressHandler,
    coordinator_auth_middleware,
)
from ai.backend.appproxy.worker.errors.ingress import (
    IngressStateUnavailableError,
    IngressWriteNotSupportedError,
)
from ai.backend.appproxy.worker.ingress.factory import IngressState
from ai.backend.appproxy.worker.ingress.layered import LayeredIngressState
from ai.backend.appproxy.worker.ingress.validating import ValidatingIngressWriter
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress

API_SECRET = "api-secret"


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


class TestCoordinatorAuthMiddleware:
    async def test_matching_token_passes(
        self, app: web.Application, next_handler: AsyncMock
    ) -> None:
        request = make_mocked_request(
            "PUT", "/v2/ingress", headers={TOKEN_HEADER: API_SECRET}, app=app
        )
        await coordinator_auth_middleware(request, next_handler)
        next_handler.assert_awaited_once_with(request)

    async def test_missing_token_is_rejected(
        self, app: web.Application, next_handler: AsyncMock
    ) -> None:
        request = make_mocked_request("PUT", "/v2/ingress", app=app)
        with pytest.raises(AuthorizationFailed):
            await coordinator_auth_middleware(request, next_handler)
        next_handler.assert_not_awaited()

    async def test_wrong_token_is_rejected(
        self, app: web.Application, next_handler: AsyncMock
    ) -> None:
        request = make_mocked_request(
            "PUT", "/v2/ingress", headers={TOKEN_HEADER: "wrong"}, app=app
        )
        with pytest.raises(AuthorizationFailed):
            await coordinator_auth_middleware(request, next_handler)
        next_handler.assert_not_awaited()


INGRESS_PAYLOAD: dict[str, Any] = {
    "id": "ingress-1",
    "authority": "worker-1",
    "revision": 3,
    "frontend": {"kind": "port", "protocol": "http", "port": {"number": 10205}},
    "access": {"mode": "public", "allowed_client_ips": []},
    "backend": {
        "id": "backend-1",
        "target_groups": [{"id": "group-1", "weight": 1, "targets": []}],
    },
}


def _request(body: dict[str, Any] | None = None) -> Mock:
    request = Mock(spec=web.Request)
    request.can_read_body = body is not None
    request.json = AsyncMock(return_value=body)
    return request


@pytest.fixture
def writer() -> AsyncMock:
    return AsyncMock(spec=ValidatingIngressWriter)


@pytest.fixture
def reader() -> AsyncMock:
    reader = AsyncMock(spec=LayeredIngressState)
    reader.get_all.return_value = [Ingress.model_validate(INGRESS_PAYLOAD)]
    return reader


class TestIngressHandler:
    async def test_upsert_reports_the_applied_revisions(
        self, reader: AsyncMock, writer: AsyncMock
    ) -> None:
        handler = IngressHandler(IngressState(reader=reader, writer=writer))
        response = await handler.upsert(_request({"ingresses": [INGRESS_PAYLOAD]}))
        assert isinstance(response, web.Response)
        assert response.status == HTTPStatus.OK
        assert json.loads(response.text or "") == {"revisions": {"10205": 3}}
        writer.apply.assert_awaited_once()

    async def test_remove_removes_through_the_writer(
        self, reader: AsyncMock, writer: AsyncMock
    ) -> None:
        handler = IngressHandler(IngressState(reader=reader, writer=writer))
        body = {"keys": [{"authority": "worker-1", "frontend_key": "10205"}]}
        response = await handler.remove(_request(body))
        assert response.status == HTTPStatus.NO_CONTENT
        writer.remove.assert_awaited_once()

    async def test_replace_reports_the_applied_revisions(
        self, reader: AsyncMock, writer: AsyncMock
    ) -> None:
        handler = IngressHandler(IngressState(reader=reader, writer=writer))
        response = await handler.replace(_request({"ingresses": [INGRESS_PAYLOAD]}))
        assert isinstance(response, web.Response)
        assert response.status == HTTPStatus.OK
        assert json.loads(response.text or "") == {"revisions": {"10205": 3}}
        writer.replace_all.assert_awaited_once()

    async def test_write_without_writer_is_not_supported(self, reader: AsyncMock) -> None:
        handler = IngressHandler(IngressState(reader=reader, writer=None))
        with pytest.raises(IngressWriteNotSupportedError):
            await handler.upsert(_request({"ingresses": [INGRESS_PAYLOAD]}))

    async def test_without_state_is_unavailable(self) -> None:
        handler = IngressHandler(state=None)
        with pytest.raises(IngressStateUnavailableError):
            await handler.revisions(_request())

    async def test_revisions_map_frontend_keys(self, reader: AsyncMock, writer: AsyncMock) -> None:
        handler = IngressHandler(IngressState(reader=reader, writer=writer))
        response = await handler.revisions(_request())
        assert isinstance(response, web.Response)
        assert response.status == HTTPStatus.OK
        assert json.loads(response.text or "") == {"revisions": {"10205": 3}}
