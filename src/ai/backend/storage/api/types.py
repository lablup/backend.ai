from __future__ import annotations

from typing import Awaitable, Callable, Mapping, TypeAlias

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import Middleware

WebRequestHandler: TypeAlias = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
WebMiddleware: TypeAlias = Middleware

CORSOptions: TypeAlias = Mapping[str, aiohttp_cors.ResourceOptions]
