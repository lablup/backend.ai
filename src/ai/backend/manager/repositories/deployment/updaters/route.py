"""UpdaterSpec implementations for the route entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from ai.backend.manager.data.deployment.types import RouteStatus, RouteTrafficStatus
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class RouteStatusUpdaterSpec(UpdaterSpec[RoutingRow]):
    """UpdaterSpec for route status updates.

    Updates health status and traffic status of a route.
    """

    status: OptionalState[RouteStatus] = field(default_factory=OptionalState[RouteStatus].nop)
    traffic_status: OptionalState[RouteTrafficStatus] = field(
        default_factory=OptionalState[RouteTrafficStatus].nop
    )

    @property
    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.status.update_dict(to_update, "status")
        self.traffic_status.update_dict(to_update, "traffic_status")
        return to_update


@dataclass
class RouteSessionUpdaterSpec(UpdaterSpec[RoutingRow]):
    """UpdaterSpec for route session binding.

    Binds a session to a route for traffic routing.
    """

    session: UUID

    @property
    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def build_values(self) -> dict[str, Any]:
        return {
            "session": self.session,
            "status": RouteStatus.PROVISIONING,
        }


@dataclass
class RouteUpdaterSpec(UpdaterSpec[RoutingRow]):
    """Unified UpdaterSpec for route updates.

    Combines all route update operations into a single spec.
    Each field uses OptionalState to support partial updates.
    """

    status: OptionalState[RouteStatus] = field(default_factory=OptionalState[RouteStatus].nop)
    traffic_status: OptionalState[RouteTrafficStatus] = field(
        default_factory=OptionalState[RouteTrafficStatus].nop
    )
    session: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)
    traffic_ratio: OptionalState[float] = field(default_factory=OptionalState[float].nop)
    revision: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)
    error_data: OptionalState[dict[str, Any]] = field(
        default_factory=OptionalState[dict[str, Any]].nop
    )

    @property
    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.status.update_dict(to_update, "status")
        self.traffic_status.update_dict(to_update, "traffic_status")
        self.session.update_dict(to_update, "session")
        self.traffic_ratio.update_dict(to_update, "traffic_ratio")
        self.revision.update_dict(to_update, "revision")
        self.error_data.update_dict(to_update, "error_data")
        return to_update
