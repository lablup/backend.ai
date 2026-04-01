import enum
from collections.abc import Awaitable, Callable, Iterable, Mapping

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import Middleware

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
