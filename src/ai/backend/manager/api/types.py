from __future__ import annotations

from typing import (
    Awaitable,
    Callable,
    Iterable,
    AsyncContextManager,
    Mapping,
    Tuple,
    TYPE_CHECKING,
)
from typing_extensions import TypeAlias

from aiohttp import web
import aiohttp_cors

if TYPE_CHECKING:
    from .context import RootContext


WebRequestHandler: TypeAlias = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
WebMiddleware: TypeAlias = Callable[
    [web.Request, WebRequestHandler],
    Awaitable[web.StreamResponse],
]

CORSOptions: TypeAlias = Mapping[str, aiohttp_cors.ResourceOptions]
AppCreator: TypeAlias = Callable[
    [CORSOptions],
    Tuple[web.Application, Iterable[WebMiddleware]],
]

CleanupContext: TypeAlias = Callable[['RootContext'], AsyncContextManager[None]]
