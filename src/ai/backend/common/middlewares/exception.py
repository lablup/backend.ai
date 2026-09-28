import asyncio
import logging

from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


@web.middleware
async def general_exception_middleware(
    request: web.Request, handler: Handler
) -> web.StreamResponse:
    method = request.method
    endpoint = getattr(request.match_info.route.resource, "canonical", request.path)
    log.trace("handling request", http_method=method, endpoint=endpoint)
    try:
        resp = await handler(request)
    except web.HTTPException as ex:
        if ex.status_code // 100 == 4:
            log.trace(
                "client error raised inside handlers",
                http_method=method,
                endpoint=endpoint,
                response_status=ex.status_code,
                error=str(ex),
            )
        elif ex.status_code // 100 == 5:
            log.exception(
                "internal server error raised inside handlers",
                http_method=method,
                endpoint=endpoint,
                response_status=ex.status_code,
            )
        raise
    except ConnectionError as e:
        log.warning(
            "connection error inside handlers",
            exc_info=e,
            http_method=method,
            endpoint=endpoint,
        )
        raise
    except asyncio.CancelledError:
        # The server is closing or the client has disconnected in the middle of
        # request.  Atomic requests are still executed to their ends.
        log.debug("request cancelled", http_method=method, request_url=str(request.rel_url))
        raise
    except Exception:
        log.exception(
            "uncaught exception in http request handlers", http_method=method, endpoint=endpoint
        )
        raise
    else:
        return resp
