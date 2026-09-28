"""Dependency provider for manager status monitoring tasks.

Watches for manager status updates via etcd and periodically reports
manager health status to the database.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.common.asyncio import ConsecutiveFailures
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.types import QueueSentinel
from ai.backend.manager.data.manager_status.types import ManagerStatus
from ai.backend.manager.repositories.manager_admin.health import report_manager_status

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

import logging

from aiotools import aclosing

from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_WATCH_MAX_RETRY_DELAY_SEC = 30.0


async def _detect_status_update(
    config_provider: ManagerConfigProvider,
    pidx: int,
) -> None:
    loader = config_provider.legacy_etcd_config_loader
    last_status: ManagerStatus | None = None
    watch_failures = ConsecutiveFailures(max_delay_sec=_WATCH_MAX_RETRY_DELAY_SEC)
    try:
        while True:
            try:
                async with aclosing(loader.watch_manager_status()) as agen:
                    async for ev in agen:
                        if isinstance(ev, QueueSentinel):
                            continue
                        if failure_count := watch_failures.record_success():
                            log.info(
                                "manager status watch recovered",
                                pidx=pidx,
                                failure_count=failure_count,
                            )
                        if ev.event == "put":
                            loader.get_manager_status.cache_clear()
                            updated_status = await loader.get_manager_status()
                            if updated_status != last_status:
                                log.info(
                                    "manager status changed",
                                    pidx=pidx,
                                    manager_status=updated_status,
                                )
                                last_status = updated_status
            except Exception:
                if watch_failures.record_failure():
                    log.exception("manager status watch failed", pidx=pidx)
                else:
                    log.debug(
                        "manager status watch failed",
                        pidx=pidx,
                        failure_count=watch_failures.count,
                    )
            await asyncio.sleep(watch_failures.delay_sec())
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
                log.warning("failed to report manager health status", exc_info=e)
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
    @override
    def stage_name(self) -> str:
        return "manager-status-watcher"

    @asynccontextmanager
    @override
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
            try:
                await status_watch_task
            except asyncio.CancelledError:
                pass
            db_status_report_task.cancel()
            try:
                await db_status_report_task
            except asyncio.CancelledError:
                pass
