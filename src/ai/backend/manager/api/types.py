from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Mapping
from contextlib import AbstractAsyncContextManager
from typing import (
    TYPE_CHECKING,
    TypeAlias,
)

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import Middleware

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
    tuple[web.Application, Iterable[WebMiddleware]],
]

CleanupContext: TypeAlias = Callable[["RootContext"], AbstractAsyncContextManager[None]]
