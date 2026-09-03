from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import pytest
from aiohttp import web

from ai.backend.common.web.reserved_response_headers import (
    reserve_response_headers,
    setup_reserved_response_headers,
)

_HEADER = "X-Reserved"


async def _returns_with_header(request: web.Request) -> web.Response:
    reserve_response_headers(request, {_HEADER: "set"})
    return web.Response(text="ok")


async def _raises_with_header(request: web.Request) -> web.Response:
    reserve_response_headers(request, {_HEADER: "set"})
    raise web.HTTPTooManyRequests()


async def _returns_without_header(request: web.Request) -> web.Response:
    return web.Response(text="ok")


@dataclass(frozen=True)
class _Case:
    id: str
    handler: Callable[[web.Request], Awaitable[web.Response]]
    expected_status: int
    expected_header: str | None


@pytest.mark.parametrize(
    "case",
    [
        # Header set by the handler lands on its normal response.
        _Case(
            id="returned-response",
            handler=_returns_with_header,
            expected_status=200,
            expected_header="set",
        ),
        # Header set before an error is raised lands on the error response too.
        _Case(
            id="raised-error",
            handler=_raises_with_header,
            expected_status=429,
            expected_header="set",
        ),
        # Nothing set: the hook adds nothing.
        _Case(
            id="no-reserved-header",
            handler=_returns_without_header,
            expected_status=200,
            expected_header=None,
        ),
    ],
    ids=lambda case: case.id,
)
async def test_reserved_headers_land_on_the_prepared_response(
    case: _Case, aiohttp_client: Any
) -> None:
    app = web.Application()
    setup_reserved_response_headers(app)
    app.router.add_get("/", case.handler)
    client = await aiohttp_client(app)

    response = await client.get("/")

    assert response.status == case.expected_status
    assert response.headers.get(_HEADER) == case.expected_header
