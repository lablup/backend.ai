from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any
from uuid import UUID

from aiohttp import web

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.middlewares.request_id import REQUEST_ID_HEADER, request_id_middleware

if TYPE_CHECKING:
    pass


async def test_request_id_middleware_with_custom_request_id(aiohttp_client: Any) -> None:
    async def test_handler(request: web.Request) -> web.Response:
        assert current_request_id() == request.headers.get(REQUEST_ID_HEADER)
        return web.Response(text="ok")

    app = web.Application()
    app.middlewares.append(request_id_middleware)
    app.router.add_get("/", test_handler)

    client = await aiohttp_client(app)

    # Test with custom request ID
    test_id = str(uuid.uuid4())
    resp = await client.get("/", headers={REQUEST_ID_HEADER: test_id})
    assert resp.status == 200
    # Verify request_id is included in response headers
    assert resp.headers.get(REQUEST_ID_HEADER) == test_id


async def test_request_id_middleware_without_request_id(aiohttp_client: Any) -> None:
    async def test_handler(request: web.Request) -> web.Response:
        # When no request_id header is provided, with_request_id generates a UUID
        req_id = current_request_id()
        assert req_id is not None
        # Verify it's a valid UUID
        UUID(req_id)
        return web.Response(text="ok")

    app = web.Application()
    app.middlewares.append(request_id_middleware)
    app.router.add_get("/", test_handler)

    client = await aiohttp_client(app)

    # Test without request ID header
    resp = await client.get("/")
    assert resp.status == 200
    # Response should not have request_id header when none was provided in request
    assert REQUEST_ID_HEADER not in resp.headers
