from collections.abc import Awaitable, Callable

from aiohttp import web

from ai.backend.common.contexts.client_operation import with_client_operation

type Handler = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]

CLIENT_OPERATION_HEADER = "X-BackendAI-Client-Operation"


@web.middleware
async def client_operation_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    client_operation: str = request.headers.get(CLIENT_OPERATION_HEADER, "")
    with with_client_operation(client_operation):
        return await handler(request)
