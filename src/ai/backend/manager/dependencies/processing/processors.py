from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.services.processors import ProcessorArgs, Processors, ServiceArgs


@dataclass
class ProcessorsProviderInput:
    """Input required for Processors setup."""

    service_args: ServiceArgs
    action_monitors: list[ActionMonitor]


class ProcessorsDependency(NonMonitorableDependencyProvider[ProcessorsProviderInput, Processors]):
    """Provides Processors lifecycle management.

    Creates the Processors instance via Processors.create() with
    the given ServiceArgs and action monitors.
    """

    @property
    def stage_name(self) -> str:
        return "processors"

    @asynccontextmanager
    async def provide(self, setup_input: ProcessorsProviderInput) -> AsyncIterator[Processors]:
        processors = Processors.create(
            ProcessorArgs(service_args=setup_input.service_args),
            setup_input.action_monitors,
        )
        yield processors
