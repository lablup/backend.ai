from collections.abc import Awaitable, Callable
from typing import Optional

from aiohttp import web

from ai.backend.common.contexts.request_id import with_request_id
from ai.backend.logging.utils import with_log_context_fields

type Handler = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]

REQUEST_ID_HEADER = "X-BackendAI-RequestID"


@web.middleware
async def request_id_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    _handler = handler
    request_id: Optional[str] = request.headers.get(REQUEST_ID_HEADER, None)
    with (
        with_request_id(request_id),
        with_log_context_fields({"request_id": request_id}),
    ):
        return await _handler(request)
