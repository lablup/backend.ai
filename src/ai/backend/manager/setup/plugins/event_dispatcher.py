from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.config.unified import ManagerUnifiedConfig


@dataclass
class EventDispatcherPluginSpec:
    config: ManagerUnifiedConfig
    etcd: AsyncEtcd


class EventDispatcherPluginProvisioner(Provisioner[EventDispatcherPluginSpec, EventDispatcherPluginContext]):
    @property
    def name(self) -> str:
        return "event_dispatcher_plugin"

    async def setup(self, spec: EventDispatcherPluginSpec) -> EventDispatcherPluginContext:
        ctx = EventDispatcherPluginContext(
            spec.etcd,
            spec.config.model_dump(by_alias=True),
        )
        # Note: The actual initialization with context, allowlist, and blocklist
        # happens later when the full RootContext is available.
        # This is because EventDispatcherPluginContext.init() requires the RootContext as a parameter.
        return ctx

    async def teardown(self, resource: EventDispatcherPluginContext) -> None:
        await resource.cleanup()