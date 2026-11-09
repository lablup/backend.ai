import asyncio
import logging

from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

# 499 "Client Closed Request" is an nginx convention, not an RFC status, so neither
# http.HTTPStatus nor aiohttp defines it. The stub carrying it never reaches the wire.
HTTP_CLIENT_CLOSED_REQUEST = 499


def is_client_disconnect(request: web.BaseRequest, exc: BaseException) -> bool:
    """True when ``exc`` is the ConnectionResetError aiohttp raises for a write to a transport
    the client has already closed. The same error on a live transport is an upstream fault."""
    if not isinstance(exc, ConnectionResetError):
        return False
    transport = request.transport
    return transport is None or transport.is_closing()


def client_closed_response() -> web.StreamResponse:
    """Stands in for the abandoned response so aiohttp finishes the request through its own
    ConnectionError path instead of logging a 500 with a traceback."""
    return web.Response(status=HTTP_CLIENT_CLOSED_REQUEST, reason="Client Closed Request")


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
        if is_client_disconnect(request, e):
            log.trace(
                "client disconnected while writing the response",
                http_method=method,
                endpoint=endpoint,
            )
            return client_closed_response()
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
