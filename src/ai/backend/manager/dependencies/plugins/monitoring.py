from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ai.backend.common.dependencies import NonMonitorableDependencyProvider, ResourceT
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.plugin.monitor import ManagerErrorPluginContext, ManagerStatsPluginContext

if TYPE_CHECKING:
    from ai.backend.manager.repositories.error_log import ErrorLogRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class MonitoringInput:
    """Input required for monitoring plugin setup.

    Separated from PluginsInput because monitoring plugins require
    error_log_repository which is only available after DomainComposer (Stage 6).
    """

    etcd: AsyncEtcd
    local_config: Mapping[str, Any]
    allowed_plugins: set[str] | None
    disabled_plugins: set[str] | None
    error_log_repository: ErrorLogRepository


class MonitoringDependency(NonMonitorableDependencyProvider[MonitoringInput, ResourceT]):
    """Base class for monitoring plugin dependencies."""

    pass


class ErrorMonitorDependency(MonitoringDependency[ManagerErrorPluginContext | None]):
    """Provides ManagerErrorPluginContext lifecycle management.

    Tolerates initialization failures — yields None if init fails.
    Injects error_log_repository directly, bypassing root_ctx lookup.
    """

    @property
    def stage_name(self) -> str:
        return "error-monitor-plugin"

    @asynccontextmanager
    async def provide(
        self, setup_input: MonitoringInput
    ) -> AsyncIterator[ManagerErrorPluginContext | None]:
        ctx = ManagerErrorPluginContext(setup_input.etcd, setup_input.local_config)
        try:
            await ctx.init(
                context={"error_log_repository": setup_input.error_log_repository},
                allowlist=setup_input.allowed_plugins,
            )
        except Exception:
            log.error("Failed to initialize error monitor plugin")
            yield None
            return
        log.info(
            "ManagerErrorPluginContext initialized with plugins: {}",
            list(ctx.plugins.keys()),
        )
        try:
            yield ctx
        finally:
            await ctx.cleanup()


class StatsMonitorDependency(MonitoringDependency[ManagerStatsPluginContext | None]):
    """Provides ManagerStatsPluginContext lifecycle management.

    Tolerates initialization failures — yields None if init fails.
    Does not use error_log_repository.
    """

    @property
    def stage_name(self) -> str:
        return "stats-monitor-plugin"

    @asynccontextmanager
    async def provide(
        self, setup_input: MonitoringInput
    ) -> AsyncIterator[ManagerStatsPluginContext | None]:
        ctx = ManagerStatsPluginContext(setup_input.etcd, setup_input.local_config)
        try:
            await ctx.init(
                allowlist=setup_input.allowed_plugins,
            )
        except Exception:
            log.error("Failed to initialize stats monitor plugin")
            yield None
            return
        log.info(
            "ManagerStatsPluginContext initialized with plugins: {}",
            list(ctx.plugins.keys()),
        )
        try:
            yield ctx
        finally:
            await ctx.cleanup()
