from __future__ import annotations

import asyncio
import logging
import traceback
from typing import TYPE_CHECKING, Final, cast

from aiohttp import web
from aiohttp.typedefs import Middleware

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.common.json import dump_json_str
from ai.backend.common.plugin.monitor import INCREMENT
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.common import (
    GenericBadRequest,
    InternalServerError,
    MethodNotAllowed,
    URLNotFound,
)
from ai.backend.manager.exceptions import InvalidArgument

if TYPE_CHECKING:
    from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
    from ai.backend.manager.api.rest.types import WebRequestHandler
    from ai.backend.manager.config.provider import ManagerConfigProvider

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _debug_error_response(
    e: Exception,
) -> web.StreamResponse:
    error_type = ""
    error_title = ""
    error_message = "Internal server error"
    status_code = 500
    error_code = ErrorCode.default()
    if isinstance(e, BackendAIError):
        error_type = e.error_type
        error_title = e.error_title
        if e.extra_msg:
            error_message = e.extra_msg
        status_code = e.status_code
        error_code = e.error_code()

    return web.json_response(
        {
            "type": error_type,
            "title": error_title,
            "error_code": str(error_code),
            "msg": error_message,
            "traceback": traceback.format_exc(),
        },
        status=status_code,
        dumps=dump_json_str,
    )


def build_exception_middleware(
    *,
    error_monitor: ErrorPluginContext,
    stats_monitor: StatsPluginContext,
    config_provider: ManagerConfigProvider,
) -> Middleware:
    """Build an exception middleware with explicit dependencies."""

    @web.middleware
    async def _middleware(request: web.Request, handler: WebRequestHandler) -> web.StreamResponse:
        method = request.method
        endpoint = getattr(request.match_info.route.resource, "canonical", request.path)
        try:
            await stats_monitor.report_metric(INCREMENT, "ai.backend.manager.api.requests")
            resp = await handler(request)
        except InvalidArgument as ex:
            if len(ex.args) > 1:
                raise InvalidAPIParameters(
                    f"{ex.args[0]}: {', '.join(map(str, ex.args[1:]))}"
                ) from ex
            if len(ex.args) == 1:
                raise InvalidAPIParameters(ex.args[0]) from ex
            raise InvalidAPIParameters() from ex
        except BackendAIError as ex:
            if ex.status_code // 100 == 4:
                log.warning(
                    "client error raised inside handlers: ({} {}): {}",
                    method,
                    endpoint,
                    repr(ex),
                )
            elif ex.status_code // 100 == 5:
                log.exception(
                    "Internal server error raised inside handlers: ({} {}): {}",
                    method,
                    endpoint,
                    repr(ex),
                )
            await error_monitor.capture_exception()
            await stats_monitor.report_metric(INCREMENT, "ai.backend.manager.api.failures")
            await stats_monitor.report_metric(
                INCREMENT, f"ai.backend.manager.api.status.{ex.status_code}"
            )
            if config_provider.config.debug.enabled:
                return _debug_error_response(ex)
            raise
        except web.HTTPException as ex:
            await stats_monitor.report_metric(INCREMENT, "ai.backend.manager.api.failures")
            await stats_monitor.report_metric(
                INCREMENT, f"ai.backend.manager.api.status.{ex.status_code}"
            )
            if ex.status_code // 100 == 4:
                log.warning(
                    "client error raised inside handlers: ({} {}): {}", method, endpoint, ex
                )
            elif ex.status_code // 100 == 5:
                log.exception(
                    "Internal server error raised inside handlers: ({} {}): {}",
                    method,
                    endpoint,
                    ex,
                )
            if ex.status_code == 404:
                raise URLNotFound(extra_data=request.path) from ex
            if ex.status_code == 405:
                concrete_ex = cast(web.HTTPMethodNotAllowed, ex)
                raise MethodNotAllowed(
                    method=concrete_ex.method, allowed_methods=concrete_ex.allowed_methods
                ) from ex
            raise GenericBadRequest from ex
        except asyncio.CancelledError as e:
            log.debug("Request cancelled ({0} {1})", request.method, request.rel_url)
            raise e
        except Exception as e:
            await error_monitor.capture_exception()
            log.exception(
                "Uncaught exception in HTTP request handlers ({} {}): {}", method, endpoint, e
            )
            if config_provider.config.debug.enabled:
                return _debug_error_response(e)
            raise InternalServerError() from e
        else:
            await stats_monitor.report_metric(
                INCREMENT, f"ai.backend.manager.api.status.{resp.status}"
            )
            return resp

    return _middleware
