from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    AsyncContextManager,
    Awaitable,
    Callable,
    Iterable,
    Mapping,
    Tuple,
)

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import Middleware
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from .context import RootContext


WebRequestHandler: TypeAlias = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
WebMiddleware: TypeAlias = Middleware

CORSOptions: TypeAlias = Mapping[str, aiohttp_cors.ResourceOptions]
AppCreator: TypeAlias = Callable[
    [CORSOptions],
    Tuple[web.Application, Iterable[WebMiddleware]],
]

CleanupContext: TypeAlias = Callable[["RootContext"], AsyncContextManager[None]]
