import re
from collections.abc import Awaitable, Callable

from aiohttp import web

from ai.backend.common.contexts.operation import with_client_operation
from ai.backend.common.contexts.request_id import with_request_id
from ai.backend.logging.utils import with_log_context_fields

type Handler = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]

REQUEST_ID_HEADER = "X-BackendAI-RequestID"
OPERATION_HEADER = "X-BackendAI-Operation"

_MAX_CLIENT_OPERATION_LENGTH = 64
_VALID_OPERATION_RE = re.compile(r"^[a-zA-Z0-9_\-:.]+$")


def _sanitize_client_operation(raw: str) -> str:
    if not raw:
        return ""
    value = raw[:_MAX_CLIENT_OPERATION_LENGTH]
    if not _VALID_OPERATION_RE.match(value):
        return ""
    return value


@web.middleware
async def request_id_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    _handler = handler
    request_id: str | None = request.headers.get(REQUEST_ID_HEADER, None)
    operation: str = _sanitize_client_operation(request.headers.get(OPERATION_HEADER, ""))
    with (
        with_request_id(request_id),
        with_log_context_fields({"request_id": request_id}),
        with_client_operation(operation),
    ):
        return await _handler(request)
