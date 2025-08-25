"""Endpoint and routing related enums.

This module contains enums that are used by both models and data modules
to avoid circular imports.
"""

from __future__ import annotations

import enum


class EndpointLifecycle(enum.Enum):
    PENDING = "pending"
    CREATED = "created"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"

    @classmethod
    def inactive_states(cls) -> set[EndpointLifecycle]:
        return {cls.PENDING, cls.DESTROYING, cls.DESTROYED}


class RouteStatus(enum.Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    TERMINATING = "terminating"
    PROVISIONING = "provisioning"
    FAILED_TO_START = "failed_to_start"

    @classmethod
    def active_route_statuses(cls) -> set[RouteStatus]:
        return {RouteStatus.HEALTHY, RouteStatus.UNHEALTHY, RouteStatus.PROVISIONING}
