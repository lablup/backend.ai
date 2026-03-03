"""Backward-compatibility shim for the manager module.

Handler logic has been migrated to ``api.rest.manager.handler.ManagerHandler``.

Exported symbols used by other modules are preserved:
- ``server_status_required``, ``READ_ALLOWED``, ``ALL_ALLOWED``
- ``GQLMutationUnfrozenRequiredMiddleware``
- ``SchedulerOps``
- ``PrivateContext``, ``init``, ``shutdown``
- ``detect_status_update``, ``report_status_bgtask``

The ``create_app()`` shim has been removed because
``global_subapp_pkgs`` is no longer used by the server bootstrap.
"""

from __future__ import annotations

import asyncio
import enum
import functools
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

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
