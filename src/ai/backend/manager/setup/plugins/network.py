from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.plugin.network import NetworkPluginContext


@dataclass
class NetworkPluginSpec:
    config: ManagerUnifiedConfig
    etcd: AsyncEtcd


class NetworkPluginProvisioner(Provisioner[NetworkPluginSpec, NetworkPluginContext]):
    @property
    def name(self) -> str:
        return "network_plugin"

    async def setup(self, spec: NetworkPluginSpec) -> NetworkPluginContext:
        ctx = NetworkPluginContext(
            spec.etcd,
            spec.config.model_dump(by_alias=True),
        )
        # Note: The actual initialization with context, allowlist, and blocklist
        # happens later when the full RootContext is available.
        # This is because NetworkPluginContext.init() requires the RootContext as a parameter.
        return ctx

    async def teardown(self, resource: NetworkPluginContext) -> None:
        await resource.cleanup()