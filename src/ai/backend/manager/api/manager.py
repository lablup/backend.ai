"""Backward-compatibility shim for the manager module.

Handler logic has been migrated to ``api.rest.manager.handler.ManagerHandler``.
This module keeps ``create_app()`` functional so that ``server.py`` can still
load it as a legacy subapp.

Exported symbols used by other modules are preserved:
- ``server_status_required``, ``READ_ALLOWED``, ``ALL_ALLOWED``
- ``GQLMutationUnfrozenRequiredMiddleware``
- ``SchedulerOps``
- ``PrivateContext``, ``init``, ``shutdown``
- ``detect_status_update``, ``report_status_bgtask``
"""

from __future__ import annotations

import asyncio
import enum
import functools
import logging
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any

import aiohttp_cors
import attrs
import graphene
from aiohttp import web
from aiohttp.typedefs import Handler
from aiotools import aclosing

from ai.backend.common.types import QueueSentinel
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api.rest.server_status import (
    ALL_ALLOWED,
    READ_ALLOWED,
)
from ai.backend.manager.errors.common import ServerFrozen, ServiceUnavailable
from ai.backend.manager.models.health import report_manager_status

from .auth import superadmin_required
from .types import CORSOptions, WebMiddleware, WebRequestHandler
from .utils import set_handler_attr

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = (
    "server_status_required",
    "READ_ALLOWED",
    "ALL_ALLOWED",
    "GQLMutationUnfrozenRequiredMiddleware",
    "SchedulerOps",
)


# ------------------------------------------------------------------
# SchedulerOps (re-exported from DTO for backward compat)
# ------------------------------------------------------------------


class SchedulerOps(enum.Enum):
    INCLUDE_AGENTS = "include-agents"
    EXCLUDE_AGENTS = "exclude-agents"


# ------------------------------------------------------------------
# server_status_required — backward-compat wrapper for legacy shims
# ------------------------------------------------------------------


def server_status_required(
    allowed_status: frozenset[ManagerStatus],
) -> Callable[[Handler], Handler]:
    """Legacy wrapper that reads ``config_provider`` from ``root_ctx``.

    New code should use :func:`ai.backend.manager.api.rest.server_status.server_status_required`
    which receives ``config_provider`` via constructor DI.
    """

    def decorator(handler: Handler) -> Handler:
        @functools.wraps(handler)
        async def wrapped(request: web.Request, *args: Any, **kwargs: Any) -> web.StreamResponse:
            root_ctx: RootContext = request.app["_root.context"]
            status = await root_ctx.config_provider.legacy_etcd_config_loader.get_manager_status()
            if status not in allowed_status:
                if status == ManagerStatus.FROZEN:
                    raise ServerFrozen
                msg = f"Server is not in the required status: {allowed_status}"
                raise ServiceUnavailable(msg)
            return await handler(request, *args, **kwargs)

        set_handler_attr(wrapped, "server_status_required", True)
        set_handler_attr(wrapped, "required_server_statuses", allowed_status)

        return wrapped

    return decorator


# ------------------------------------------------------------------
# GQL middleware — used by admin handler
# ------------------------------------------------------------------


class GQLMutationUnfrozenRequiredMiddleware:
    """GraphQL middleware that blocks mutations when the manager is frozen.

    Receives ``manager_status`` via constructor DI instead of reading
    from the GraphQL context.
    """

    def __init__(self, manager_status: ManagerStatus) -> None:
        self._manager_status = manager_status

    def resolve(
        self, next: Callable[..., Any], root: Any, info: graphene.ResolveInfo, **args: Any
    ) -> Any:
        if info.operation.operation == "mutation" and self._manager_status == ManagerStatus.FROZEN:
            raise ServerFrozen
        return next(root, info, **args)


# ------------------------------------------------------------------
# Background tasks — lifecycle management
# ------------------------------------------------------------------


async def detect_status_update(root_ctx: RootContext) -> None:
    try:
        async with aclosing(
            root_ctx.config_provider.legacy_etcd_config_loader.watch_manager_status()
        ) as agen:
            async for ev in agen:
                if isinstance(ev, QueueSentinel):
                    continue
                if ev.event == "put":
                    root_ctx.config_provider.legacy_etcd_config_loader.get_manager_status.cache_clear()
                    updated_status = await root_ctx.config_provider.legacy_etcd_config_loader.get_manager_status()
                    log.debug(
                        "Process-{0} detected manager status update: {1}",
                        root_ctx.pidx,
                        updated_status,
                    )
    except asyncio.CancelledError:
        pass


async def report_status_bgtask(root_ctx: RootContext) -> None:
    interval = root_ctx.config_provider.config.manager.status_update_interval
    if interval is None:
        return
    try:
        while True:
            await asyncio.sleep(interval)
            try:
                await report_manager_status(
                    root_ctx.valkey_stat, root_ctx.db, root_ctx.config_provider
                )
            except Exception as e:
                log.exception(f"Failed to report manager health status (e:{e!s})")
    except asyncio.CancelledError:
        pass


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    status_watch_task: asyncio.Task[Any]
    db_status_report_task: asyncio.Task[Any]


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["manager.context"]
    app_ctx.status_watch_task = asyncio.create_task(detect_status_update(root_ctx))
    app_ctx.db_status_report_task = asyncio.create_task(report_status_bgtask(root_ctx))


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["manager.context"]
    if app_ctx.status_watch_task is not None:
        app_ctx.status_watch_task.cancel()
        await asyncio.sleep(0)
        if not app_ctx.status_watch_task.done():
            await app_ctx.status_watch_task
    if app_ctx.db_status_report_task is not None:
        app_ctx.db_status_report_task.cancel()
        await asyncio.sleep(0)
        if not app_ctx.db_status_report_task.done():
            await app_ctx.db_status_report_task


# ------------------------------------------------------------------
# Lazy handler initialization helpers
# ------------------------------------------------------------------

_HANDLER_APP_KEY = "_manager_handler_wrapped"


def _ensure_handler(app: web.Application) -> dict[str, WebRequestHandler]:
    """Lazily create ManagerHandler and wrap its methods on first request."""
    if _HANDLER_APP_KEY not in app:
        from ai.backend.manager.api.rest.manager.handler import ManagerHandler
        from ai.backend.manager.api.rest.routing import _wrap_api_handler

        root_ctx: RootContext = app["_root.context"]
        handler = ManagerHandler(processors=root_ctx.processors)
        app[_HANDLER_APP_KEY] = {
            name: _wrap_api_handler(getattr(handler, name))
            for name in (
                "fetch_manager_status",
                "update_manager_status",
                "get_announcement",
                "update_announcement",
                "perform_scheduler_ops",
                "scheduler_trigger",
                "scheduler_healthcheck",
                "get_manager_status_for_prom",
            )
        }
    result: dict[str, WebRequestHandler] = app[_HANDLER_APP_KEY]
    return result


def _delegate(method_name: str) -> WebRequestHandler:
    """Return a handler function that delegates to the new-style ManagerHandler."""

    async def _handler(request: web.Request) -> web.StreamResponse:
        wrapped = _ensure_handler(request.app)
        return await wrapped[method_name](request)

    _handler.__name__ = method_name
    _handler.__qualname__ = f"manager._delegate.<{method_name}>"
    return _handler


# ------------------------------------------------------------------
# Legacy create_app() entry point
# ------------------------------------------------------------------


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (2, 3, 4)
    app["manager.context"] = PrivateContext()
    app["prefix"] = "manager"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    status_resource = cors.add(app.router.add_resource("/status"))
    cors.add(status_resource.add_route("GET", _delegate("fetch_manager_status")))
    cors.add(
        status_resource.add_route("PUT", superadmin_required(_delegate("update_manager_status")))
    )
    announcement_resource = cors.add(app.router.add_resource("/announcement"))
    cors.add(announcement_resource.add_route("GET", _delegate("get_announcement")))
    cors.add(
        announcement_resource.add_route(
            "POST", superadmin_required(_delegate("update_announcement"))
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/scheduler/operation",
            superadmin_required(_delegate("perform_scheduler_ops")),
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/scheduler/trigger",
            superadmin_required(_delegate("scheduler_trigger")),
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/scheduler/status",
            superadmin_required(_delegate("scheduler_healthcheck")),
        )
    )
    prom_resource = cors.add(app.router.add_resource("/prom"))
    cors.add(prom_resource.add_route("GET", _delegate("get_manager_status_for_prom")))
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    return app, []
