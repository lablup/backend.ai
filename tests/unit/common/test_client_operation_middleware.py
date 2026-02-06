from __future__ import annotations

from typing import Any

from aiohttp import web

from ai.backend.common.contexts.client_operation import get_client_operation
from ai.backend.common.middlewares.client_operation import (
    CLIENT_OPERATION_HEADER,
    client_operation_middleware,
)


async def test_client_operation_middleware_with_header(aiohttp_client: Any) -> None:
    async def test_handler(request: web.Request) -> web.Response:
        assert get_client_operation() == "list_sessions"
        return web.Response(text="ok")

    app = web.Application()
    app.middlewares.append(client_operation_middleware)
    app.router.add_get("/", test_handler)

    client = await aiohttp_client(app)
    resp = await client.get("/", headers={CLIENT_OPERATION_HEADER: "list_sessions"})
    assert resp.status == 200


async def test_client_operation_middleware_without_header(aiohttp_client: Any) -> None:
    async def test_handler(request: web.Request) -> web.Response:
        assert get_client_operation() == ""
        return web.Response(text="ok")

    app = web.Application()
    app.middlewares.append(client_operation_middleware)
    app.router.add_get("/", test_handler)

    client = await aiohttp_client(app)
    resp = await client.get("/")
    assert resp.status == 200
