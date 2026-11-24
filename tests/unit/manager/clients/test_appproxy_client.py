from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestClient

from ai.backend.common.contexts.request_id import with_request_context
from ai.backend.common.middlewares.request_id import REQUEST_ID_HEADER
from ai.backend.manager.clients.appproxy.client import AppProxyClient


@pytest.fixture
def received_request_ids() -> list[str | None]:
    return []


@pytest.fixture
async def appproxy_client(
    aiohttp_client: Any,  # pytest-aiohttp plugin fixture
    received_request_ids: list[str | None],
) -> AsyncIterator[AppProxyClient]:
    async def handler(request: web.Request) -> web.Response:
        received_request_ids.append(request.headers.get(REQUEST_ID_HEADER))
        return web.Response(status=204)

    app = web.Application()
    app.router.add_delete("/v2/endpoints/{endpoint_id}", handler)
    client: TestClient[Any] = await aiohttp_client(app)  # type: ignore[type-arg]
    address = str(client.make_url("/"))
    async with ClientSession(base_url=address) as session:
        yield AppProxyClient(session, address, "test-token")


class TestAppProxyClient:
    async def test_request_id_header_follows_the_request_context(
        self, appproxy_client: AppProxyClient, received_request_ids: list[str | None]
    ) -> None:
        with with_request_context("req-from-manager"):
            await appproxy_client.delete_endpoint(uuid.uuid4())

        assert received_request_ids == ["req-from-manager"]

    async def test_no_request_id_header_without_request_context(
        self, appproxy_client: AppProxyClient, received_request_ids: list[str | None]
    ) -> None:
        await appproxy_client.delete_endpoint(uuid.uuid4())

        assert received_request_ids == [None]
