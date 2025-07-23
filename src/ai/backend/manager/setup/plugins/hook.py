from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.config.unified import ManagerUnifiedConfig


@dataclass
class HookPluginSpec:
    config: ManagerUnifiedConfig
    etcd: AsyncEtcd


class HookPluginProvisioner(Provisioner[HookPluginSpec, HookPluginContext]):
    @property
    def name(self) -> str:
        return "hook_plugin"

    async def setup(self, spec: HookPluginSpec) -> HookPluginContext:
        ctx = HookPluginContext(
            spec.etcd,
            spec.config.model_dump(by_alias=True),
        )
        # Note: The actual initialization with context, allowlist, and blocklist
        # happens later when the full RootContext is available.
        # This is because HookPluginContext.init() requires the RootContext as a parameter.
        return ctx

    async def teardown(self, resource: HookPluginContext) -> None:
        await resource.cleanup()