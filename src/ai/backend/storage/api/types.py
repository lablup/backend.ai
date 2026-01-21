from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import TypeAlias

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import Middleware

WebRequestHandler: TypeAlias = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
WebMiddleware: TypeAlias = Middleware

CORSOptions: TypeAlias = Mapping[str, aiohttp_cors.ResourceOptions]
