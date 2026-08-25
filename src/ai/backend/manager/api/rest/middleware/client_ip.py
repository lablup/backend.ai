from collections.abc import Awaitable, Callable

from aiohttp import web

from ai.backend.common.contexts.client_ip import with_client_ip

from .auth import extract_client_ip

type Handler = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]


@web.middleware
async def client_ip_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    """Push the caller's address into the context for the whole request.

    Runs ahead of authentication so that unauthenticated routes — a login attempt
    above all — record where they came from.
    """
    client_ip = extract_client_ip(request)
    if client_ip is None:
        return await handler(request)
    with with_client_ip(client_ip):
        return await handler(request)
