from __future__ import annotations

from typing import Awaitable, Callable, Mapping, TypeAlias

import aiohttp_cors
from aiohttp import web

WebRequestHandler: TypeAlias = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
WebMiddleware: TypeAlias = Callable[
    [web.Request, WebRequestHandler],
    Awaitable[web.StreamResponse],
]

CORSOptions: TypeAlias = Mapping[str, aiohttp_cors.ResourceOptions]
