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
from aiohttp.typedefs import Middleware

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


class EventLoopType(enum.StrEnum):
    UVLOOP = "uvloop"
    ASYNCIO = "asyncio"


class UserRole(enum.StrEnum):
    """
    User roles.
    """

    ADMIN = "admin"
    USER = "user"


class UserStatus(enum.StrEnum):
    """
    User account status.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    BEFORE_VERIFICATION = "before-verification"
