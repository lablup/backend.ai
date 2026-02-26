from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Mapping

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import Middleware

from ai.backend.common.api_handlers import APIResponse

type WebRequestHandler = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
type WebMiddleware = Middleware

type CORSOptions = Mapping[str, aiohttp_cors.ResourceOptions]
type AppCreator = Callable[
    [CORSOptions],
    tuple[web.Application, Iterable[WebMiddleware]],
]

type RouteMiddleware = Callable[
    [WebRequestHandler],
    WebRequestHandler,
]

type ApiHandler = Callable[..., Awaitable[APIResponse]]
