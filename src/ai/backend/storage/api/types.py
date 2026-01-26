from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import Middleware

type WebRequestHandler = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
type WebMiddleware = Middleware

type CORSOptions = Mapping[str, aiohttp_cors.ResourceOptions]
