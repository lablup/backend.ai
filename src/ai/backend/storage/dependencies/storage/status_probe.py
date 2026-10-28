from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.storage.probe.registry import VolumeStatusReporterRegistry
from ai.backend.common.storage.probe.runner import ProbeCheckRunner, ProbeCheckRunnerArgs
from ai.backend.storage.volumes.pool import VolumePool


@dataclass
class StatusProbeInput:
    """Input required for the status probe setup."""

    pidx: int
    volume_pool: VolumePool


@dataclass
class StatusProbeResources:
    """Container for status probe resources."""

    registry: VolumeStatusReporterRegistry


class StatusProbeProvider(NonMonitorableDependencyProvider[StatusProbeInput, StatusProbeResources]):
    """Provider for the volume status check registry and the runner that drives it.

    Only worker 0 runs the checks, so a node checks each volume once; every worker holds
    the registry.
    """

    @property
    @override
    def stage_name(self) -> str:
        return "status-probe"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: StatusProbeInput) -> AsyncIterator[StatusProbeResources]:
        registry = VolumeStatusReporterRegistry(setup_input.volume_pool.volume_status_reporters())
        runner = ProbeCheckRunner(
            ProbeCheckRunnerArgs(checks=setup_input.volume_pool.volume_status_checks())
        )
        if setup_input.pidx == 0:
            await runner.start()
        try:
            yield StatusProbeResources(registry=registry)
        finally:
            if setup_input.pidx == 0:
                await runner.stop()
