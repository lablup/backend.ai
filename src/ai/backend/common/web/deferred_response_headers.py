"""Response headers set before the response exists, applied when it is prepared.

A middleware or handler adds headers to ``deferred_response_headers(request)``;
``setup_deferred_response_headers()`` installs the ``on_response_prepare`` hook that copies them onto
whatever response the request ends with, an error raised later included.
"""

from __future__ import annotations

from typing import Final

from aiohttp import web
from multidict import CIMultiDict

_DEFERRED_RESPONSE_HEADERS_KEY: Final = "deferred_response_headers"


def deferred_response_headers(request: web.Request) -> CIMultiDict[str]:
    """Use this instead of writing to the response a middleware gets back: a raised
    HTTPException never passes through the middleware, so headers set there are lost."""
    headers: CIMultiDict[str] | None = request.get(_DEFERRED_RESPONSE_HEADERS_KEY)
    if headers is None:
        headers = CIMultiDict()
        request[_DEFERRED_RESPONSE_HEADERS_KEY] = headers
    return headers


async def apply_deferred_response_headers(
    request: web.Request, response: web.StreamResponse
) -> None:
    headers: CIMultiDict[str] | None = request.get(_DEFERRED_RESPONSE_HEADERS_KEY)
    if headers:
        response.headers.update(headers)


def setup_deferred_response_headers(app: web.Application) -> None:
    app.on_response_prepare.append(apply_deferred_response_headers)
