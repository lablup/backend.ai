"""Route controller for managing route lifecycle operations."""

import logging
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class RouteControllerArgs:
    """Arguments for initializing RouteController."""

    valkey_schedule: ValkeyScheduleClient


class RouteController:
    """Controller for route lifecycle management."""

    _valkey_schedule: ValkeyScheduleClient

    def __init__(self, args: RouteControllerArgs) -> None:
        """Initialize the route controller with required services."""
        self._valkey_schedule = args.valkey_schedule

    async def mark_lifecycle_needed(self, lifecycle_type: RouteLifecycleType) -> None:
        """
        Mark that a route lifecycle operation is needed for the next cycle.

        This is the public interface for hinting that route lifecycle operations
        should be processed. The actual processing will be handled by the coordinator.

        Args:
            lifecycle_type: Type of route lifecycle to mark as needed
        """
        await self._valkey_schedule.mark_route_needed(lifecycle_type.value)
        log.debug("Marked route lifecycle needed for type: {}", lifecycle_type.value)
