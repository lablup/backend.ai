"""Response headers set before the response exists, applied when it is prepared.

A middleware or handler calls ``defer_response_headers()``;
``setup_deferred_response_headers()`` installs the ``on_response_prepare`` hook
that copies them onto whatever response the request ends with, an error raised
later included.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from aiohttp import web
from multidict import CIMultiDict

_DEFERRED_RESPONSE_HEADERS_KEY: Final = "deferred_response_headers"


def defer_response_headers(request: web.Request, headers: Mapping[str, str]) -> None:
    """Use this instead of writing to the response a middleware gets back: a raised
    HTTPException never passes through the middleware, so headers set there are lost."""
    deferred: CIMultiDict[str] | None = request.get(_DEFERRED_RESPONSE_HEADERS_KEY)
    if deferred is None:
        deferred = CIMultiDict()
        request[_DEFERRED_RESPONSE_HEADERS_KEY] = deferred
    deferred.update(headers)


async def apply_deferred_response_headers(
    request: web.Request, response: web.StreamResponse
) -> None:
    deferred: CIMultiDict[str] | None = request.get(_DEFERRED_RESPONSE_HEADERS_KEY)
    if deferred:
        response.headers.update(deferred)


def setup_deferred_response_headers(app: web.Application) -> None:
    app.on_response_prepare.append(apply_deferred_response_headers)
