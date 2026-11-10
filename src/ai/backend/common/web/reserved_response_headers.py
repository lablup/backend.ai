"""Response headers reserved before the response exists, applied when it is prepared.

A middleware or handler calls ``reserve_response_headers()`` with an object that
writes its headers; ``setup_reserved_response_headers()`` installs the
``on_response_prepare`` hook that applies every reservation to whatever response
the request ends with, an error raised later included.
"""

from __future__ import annotations

from typing import Final, Protocol

from aiohttp import web
from multidict import CIMultiDict

_RESERVED_RESPONSE_HEADERS_KEY: Final = "reserved_response_headers"


class ReservedResponseHeaders(Protocol):
    def apply_to(self, headers: CIMultiDict[str]) -> None: ...


def reserve_response_headers(request: web.Request, reserved: ReservedResponseHeaders) -> None:
    """Use this instead of writing to the response a middleware gets back: a raised
    HTTPException never passes through the middleware, so headers set there are lost."""
    reservations: list[ReservedResponseHeaders] | None = request.get(_RESERVED_RESPONSE_HEADERS_KEY)
    if reservations is None:
        reservations = []
        request[_RESERVED_RESPONSE_HEADERS_KEY] = reservations
    reservations.append(reserved)


async def apply_reserved_response_headers(
    request: web.Request, response: web.StreamResponse
) -> None:
    reservations: list[ReservedResponseHeaders] = request.get(_RESERVED_RESPONSE_HEADERS_KEY, [])
    for reserved in reservations:
        reserved.apply_to(response.headers)


def setup_reserved_response_headers(app: web.Application) -> None:
    app.on_response_prepare.append(apply_reserved_response_headers)
