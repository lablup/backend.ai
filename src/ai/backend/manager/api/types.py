from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Mapping
from contextlib import AbstractAsyncContextManager
from typing import (
    TYPE_CHECKING,
)

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import Middleware

if TYPE_CHECKING:
    from .context import RootContext


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

type CleanupContext = Callable[["RootContext"], AbstractAsyncContextManager[None]]
