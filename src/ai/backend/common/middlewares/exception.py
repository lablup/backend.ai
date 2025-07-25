import asyncio
import logging

from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@web.middleware
async def general_exception_middleware(
    request: web.Request, handler: Handler
) -> web.StreamResponse:
    method = request.method
    endpoint = getattr(request.match_info.route.resource, "canonical", request.path)
    log.trace("Handling request: ({}) {}", method, endpoint)
    try:
        resp = await handler(request)
    except web.HTTPException as ex:
        if ex.status_code // 100 == 4:
            log.warning("client error raised inside handlers: ({} {}): {}", method, endpoint, ex)
        elif ex.status_code // 100 == 5:
            log.exception(
                "Internal server error raised inside handlers: ({} {}): {}", method, endpoint, ex
            )
        raise
    except asyncio.CancelledError:
        # The server is closing or the client has disconnected in the middle of
        # request.  Atomic requests are still executed to their ends.
        log.debug("Request cancelled ({0} {1})", request.method, request.rel_url)
        raise
    except Exception as e:
        log.exception(
            "Uncaught exception in HTTP request handlers ({} {}): {}", method, endpoint, e
        )
        raise
    else:
        return resp
