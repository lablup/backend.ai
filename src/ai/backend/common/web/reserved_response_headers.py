"""Response headers reserved before the response exists, applied when it is prepared.

A middleware or handler calls ``reserve_response_headers()``;
``setup_reserved_response_headers()`` installs the ``on_response_prepare`` hook
that copies them onto whatever response the request ends with, an error raised
later included.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from aiohttp import web
from multidict import CIMultiDict

_RESERVED_RESPONSE_HEADERS_KEY: Final = "reserved_response_headers"


def reserve_response_headers(request: web.Request, headers: Mapping[str, str]) -> None:
    """Use this instead of writing to the response a middleware gets back: a raised
    HTTPException never passes through the middleware, so headers set there are lost."""
    reserved: CIMultiDict[str] | None = request.get(_RESERVED_RESPONSE_HEADERS_KEY)
    if reserved is None:
        reserved = CIMultiDict()
        request[_RESERVED_RESPONSE_HEADERS_KEY] = reserved
    reserved.update(headers)


async def apply_reserved_response_headers(
    request: web.Request, response: web.StreamResponse
) -> None:
    reserved: CIMultiDict[str] | None = request.get(_RESERVED_RESPONSE_HEADERS_KEY)
    if reserved:
        response.headers.update(reserved)


def setup_reserved_response_headers(app: web.Application) -> None:
    app.on_response_prepare.append(apply_reserved_response_headers)
