"""Manager sub-app lifecycle hooks.

Extracted from the legacy ``api/manager.py`` module so that the
``rest/manager`` package owns its own startup/shutdown concerns.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import attrs
import graphene
from aiohttp import web
from aiotools import aclosing

from ai.backend.common.types import QueueSentinel
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.errors.common import ServerFrozen
from ai.backend.manager.models.health import report_manager_status

if TYPE_CHECKING:
    from collections.abc import Callable

    from ai.backend.manager.api.context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
