from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.manager.sokovan.deployment.route.route_controller import (
    RouteController,
    RouteControllerArgs,
)


@dataclass
class RouteControllerInput:
    """Input required for route controller setup."""

    valkey_schedule: ValkeyScheduleClient


class RouteControllerDependency(
    NonMonitorableDependencyProvider[RouteControllerInput, RouteController],
):
    """Provides RouteController lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "route-controller"

    @asynccontextmanager
    async def provide(self, setup_input: RouteControllerInput) -> AsyncIterator[RouteController]:
        """Initialize and provide a route controller.

        Args:
            setup_input: Input containing Valkey schedule client

        Yields:
            Initialized RouteController
        """
        controller = RouteController(
            RouteControllerArgs(
                valkey_schedule=setup_input.valkey_schedule,
            )
        )
        yield controller
