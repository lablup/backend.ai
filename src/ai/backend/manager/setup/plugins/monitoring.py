from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.plugin.monitor import ManagerErrorPluginContext, ManagerStatsPluginContext


@dataclass
class MonitoringSpec:
    config: ManagerUnifiedConfig
    etcd: AsyncEtcd


@dataclass
class MonitoringContext:
    error_monitor: ManagerErrorPluginContext
    stats_monitor: ManagerStatsPluginContext


class MonitoringProvisioner(Provisioner[MonitoringSpec, MonitoringContext]):
    @property
    def name(self) -> str:
        return "monitoring"

    async def setup(self, spec: MonitoringSpec) -> MonitoringContext:
        ectx = ManagerErrorPluginContext(
            spec.etcd, 
            spec.config.model_dump(by_alias=True)
        )
        sctx = ManagerStatsPluginContext(
            spec.etcd, 
            spec.config.model_dump(by_alias=True)
        )
        
        # Note: The actual initialization with context, allowlist, and blocklist
        # happens later when the full RootContext is available.
        # This is because ManagerErrorPluginContext.init() requires the RootContext as a parameter.
        
        return MonitoringContext(
            error_monitor=ectx,
            stats_monitor=sctx,
        )

    async def teardown(self, resource: MonitoringContext) -> None:
        await resource.stats_monitor.cleanup()
        await resource.error_monitor.cleanup()