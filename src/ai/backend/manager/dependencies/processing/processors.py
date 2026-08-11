from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.v2 import validators as v2_validators
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.factory import create_processors
from ai.backend.manager.services.processors import ProcessorArgs, Processors, ServiceArgs


@dataclass
class ProcessorsProviderInput:
    """Input required for Processors setup."""

    service_args: ServiceArgs
    action_monitors: ActionMonitors
    event_hub: EventHub
    event_fetcher: EventFetcher
    validators: ActionValidators
    v2_validators: v2_validators.ActionValidators


class ProcessorsDependency(NonMonitorableDependencyProvider[ProcessorsProviderInput, Processors]):
    """Provides Processors lifecycle management.

    Creates the Processors instance via create_processors() with
    the given ServiceArgs and action monitors.
    """

    @property
    @override
    def stage_name(self) -> str:
        return "processors"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: ProcessorsProviderInput) -> AsyncGenerator[Processors]:
        bundle = create_processors(
            ProcessorArgs(
                service_args=setup_input.service_args,
                event_hub=setup_input.event_hub,
                event_fetcher=setup_input.event_fetcher,
                validators=setup_input.v2_validators,
            ),
            setup_input.action_monitors,
            setup_input.validators,
        )
        yield bundle.processors
