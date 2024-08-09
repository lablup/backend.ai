import enum
from collections.abc import Mapping
from typing import (
    Awaitable,
    Callable,
    Iterable,
    TypeAlias,
)

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
AppCreator: TypeAlias = Callable[
    [CORSOptions],
    tuple[web.Application, Iterable[WebMiddleware]],
]


class EventLoopType(enum.StrEnum):
    UVLOOP = "uvloop"
    ASYNCIO = "asyncio"


class UserStatus(enum.StrEnum):
    """
    User account status.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    BEFORE_VERIFICATION = "before-verification"
