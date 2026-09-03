from __future__ import annotations

from typing import Any

from aiohttp import web

from ai.backend.common.web.deferred_response_headers import (
    deferred_response_headers,
    setup_deferred_response_headers,
)


async def _ok(request: web.Request) -> web.Response:
    deferred_response_headers(request)["X-Pending"] = "ok"
    return web.Response(text="ok")


async def _rejected(request: web.Request) -> web.Response:
    deferred_response_headers(request)["X-Pending"] = "rejected"
    raise web.HTTPTooManyRequests()


async def _silent(request: web.Request) -> web.Response:
    return web.Response(text="silent")


async def test_deferred_headers_reach_the_response(aiohttp_client: Any) -> None:
    app = web.Application()
    setup_deferred_response_headers(app)
    app.router.add_get("/ok", _ok)
    client = await aiohttp_client(app)

    response = await client.get("/ok")

    assert response.status == 200
    assert response.headers["X-Pending"] == "ok"


async def test_deferred_headers_reach_an_error_raised_later(aiohttp_client: Any) -> None:
    app = web.Application()
    setup_deferred_response_headers(app)
    app.router.add_get("/rejected", _rejected)
    client = await aiohttp_client(app)

    response = await client.get("/rejected")

    assert response.status == 429
    assert response.headers["X-Pending"] == "rejected"


async def test_response_without_deferred_headers_is_untouched(aiohttp_client: Any) -> None:
    app = web.Application()
    setup_deferred_response_headers(app)
    app.router.add_get("/silent", _silent)
    client = await aiohttp_client(app)

    response = await client.get("/silent")

    assert "X-Pending" not in response.headers
