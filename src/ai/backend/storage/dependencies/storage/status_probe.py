from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.configs.volume.base import VolumeConfigs
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.storage.probe.registry import VolumeStatusCheckRegistry
from ai.backend.common.storage.probe.runner import ProbeCheckRunner, ProbeCheckRunnerArgs
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.volumes.pool import VolumePool


@dataclass
class StatusProbeInput:
    """Input required for the status probe setup."""

    local_config: StorageProxyUnifiedConfig
    pidx: int
    volume_pool: VolumePool


@dataclass
class StatusProbeResources:
    """Container for status probe resources."""

    registry: VolumeStatusCheckRegistry


class StatusProbeProvider(NonMonitorableDependencyProvider[StatusProbeInput, StatusProbeResources]):
    """Provider for the volume status check registry and the runner that drives it.

    No volume is declared with an id yet, so the registry holds no check. Only worker 0
    runs the checks, so a node checks each volume once; every worker holds the registry.
    """

    @property
    @override
    def stage_name(self) -> str:
        return "status-probe"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: StatusProbeInput) -> AsyncIterator[StatusProbeResources]:
        # TODO: pass the volume declarations from setup_input once the storage proxy
        # configuration carries them.
        registry = VolumeStatusCheckRegistry.create(VolumeConfigs(volumes={}))
        runner = ProbeCheckRunner(ProbeCheckRunnerArgs(checks=registry.checks()))
        if setup_input.pidx == 0:
            await runner.start()
        try:
            yield StatusProbeResources(registry=registry)
        finally:
            if setup_input.pidx == 0:
                await runner.stop()
