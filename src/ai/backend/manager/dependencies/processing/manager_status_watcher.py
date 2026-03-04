"""Dependency provider for manager status monitoring tasks.

Watches for manager status updates via etcd and periodically reports
manager health status to the database.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.types import QueueSentinel
from ai.backend.manager.models.health import report_manager_status

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

import logging

from aiotools import aclosing, cancel_and_wait

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def _detect_status_update(
    config_provider: ManagerConfigProvider,
    pidx: int,
) -> None:
    try:
        async with aclosing(
            config_provider.legacy_etcd_config_loader.watch_manager_status()
        ) as agen:
            async for ev in agen:
                if isinstance(ev, QueueSentinel):
                    continue
                if ev.event == "put":
                    config_provider.legacy_etcd_config_loader.get_manager_status.cache_clear()
                    updated_status = (
                        await config_provider.legacy_etcd_config_loader.get_manager_status()
                    )
                    log.debug(
                        "Process-{0} detected manager status update: {1}",
                        pidx,
                        updated_status,
                    )
    except asyncio.CancelledError:
        pass


async def _report_status_bgtask(
    config_provider: ManagerConfigProvider,
    valkey_stat: ValkeyStatClient,
    db: ExtendedAsyncSAEngine,
) -> None:
    interval = config_provider.config.manager.status_update_interval
    if interval is None:
        return
    try:
        while True:
            await asyncio.sleep(interval)
            try:
                await report_manager_status(valkey_stat, db, config_provider)
            except Exception as e:
                log.exception(f"Failed to report manager health status (e:{e!s})")
    except asyncio.CancelledError:
        pass


@dataclass
class ManagerStatusWatcherResult:
    """Container for the two background tasks."""

    status_watch_task: asyncio.Task[None]
    db_status_report_task: asyncio.Task[None]


@dataclass
class ManagerStatusWatcherInput:
    """Input required for manager status watcher setup."""

    config_provider: ManagerConfigProvider
    pidx: int
    valkey_stat: ValkeyStatClient
    db: ExtendedAsyncSAEngine


class ManagerStatusWatcherDependency(
    NonMonitorableDependencyProvider[ManagerStatusWatcherInput, ManagerStatusWatcherResult]
):
    """Provides background tasks that watch and report manager status."""

    @property
    def stage_name(self) -> str:
        return "manager-status-watcher"

    @asynccontextmanager
    async def provide(
        self, setup_input: ManagerStatusWatcherInput
    ) -> AsyncIterator[ManagerStatusWatcherResult]:
        status_watch_task: asyncio.Task[None] = asyncio.create_task(
            _detect_status_update(setup_input.config_provider, setup_input.pidx)
        )
        db_status_report_task: asyncio.Task[None] = asyncio.create_task(
            _report_status_bgtask(
                setup_input.config_provider, setup_input.valkey_stat, setup_input.db
            )
        )
        try:
            yield ManagerStatusWatcherResult(
                status_watch_task=status_watch_task,
                db_status_report_task=db_status_report_task,
            )
        finally:
            status_watch_task.cancel()
            await asyncio.sleep(0)
            if not status_watch_task.done():
                await cancel_and_wait(status_watch_task)
            db_status_report_task.cancel()
            await asyncio.sleep(0)
            if not db_status_report_task.done():
                await cancel_and_wait(db_status_report_task)
