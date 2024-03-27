import functools
import logging
from typing import Any, Awaitable, Callable, Final

from aiohttp import web

from ai.backend.common.logging import BraceStyleAdapter

from .exception import AuthorizationFailed

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


WATCHER_HEADER_TOKEN_KEY: Final = "X-BackendAI-Watcher-Token"
HANDLER_ATTR_MAP_NAME: Final = "_backend_attrs"
AUTH_REQUIRE_ATTR: Final = "auth_required"
AUTH_PASS: Final = "is_authorized"


def set_handler_attr(func: Callable, key: str, value: Any) -> None:
    attrs = getattr(func, HANDLER_ATTR_MAP_NAME, None)
    if attrs is None:
        attrs = {}
    attrs[key] = value
    setattr(func, HANDLER_ATTR_MAP_NAME, attrs)


def get_handler_attr(request: web.Request, key: str, default: Any = None) -> Any:
    # When used in the aiohttp server-side codes, we should use
    # request.match_info.hanlder instead of handler passed to the middleware
    # functions because aiohttp wraps this original handler with functools.partial
    # multiple times to implement its internal middleware processing.
    attrs = getattr(request.match_info.handler, HANDLER_ATTR_MAP_NAME, None)
    if attrs is not None:
        return attrs.get(key, default)
    return default


def auth_required(handler: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
    @functools.wraps(handler)
    async def wrapped(request: web.Request, *args, **kwargs) -> Any:
        if request.get(AUTH_PASS, False):
            return await handler(request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, AUTH_REQUIRE_ATTR, True)
    return wrapped


def is_auth_required(request: web.Request) -> bool:
    return get_handler_attr(request, AUTH_REQUIRE_ATTR, False)


@web.middleware
async def auth_middleware(request: web.Request, handler) -> web.StreamResponse:
    # This is a global middleware: request.app is the root app.
    if not is_auth_required(request):
        return await handler(request)
    token = request.headers.get(WATCHER_HEADER_TOKEN_KEY, None)
    if token != request.app["token"]:
        log.info("invalid requested token")
        return web.HTTPForbidden()
    request.update({AUTH_PASS: True})
    return await handler(request)
