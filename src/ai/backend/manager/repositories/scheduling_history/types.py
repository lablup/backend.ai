"""Types for scheduling history repository scopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ai.backend.manager.api.gql.base import UUIDEqualMatchSpec
from ai.backend.manager.errors.deployment import EndpointNotFound
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.errors.service import RouteNotFound
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base import QueryCondition, SearchScope
from ai.backend.manager.repositories.base.types import ExistenceCheck

from .options import (
    DeploymentHistoryConditions,
    RouteHistoryConditions,
    SessionSchedulingHistoryConditions,
)

__all__ = (
    "SessionSchedulingHistorySearchScope",
    "DeploymentHistorySearchScope",
    "RouteHistorySearchScope",
)


# Session Scheduling History Scope


@dataclass(frozen=True)
class SessionSchedulingHistorySearchScope(SearchScope):
    """Scope for session scheduling history search.

    Used for entity-scoped queries where session_id is the scope parameter.
    """

    session_id: UUID
    """Required. The session to search history for."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for SessionSchedulingHistoryRow."""
        return SessionSchedulingHistoryConditions.by_session_id_filter(
            UUIDEqualMatchSpec(value=self.session_id, negated=False)
        )

    @property
    def existence_checks(self) -> list[ExistenceCheck[Any]]:
        """Check that the session exists."""
        return [
            ExistenceCheck(
                column=SessionRow.id,
                value=self.session_id,
                error=SessionNotFound(str(self.session_id)),
            ),
        ]


# Deployment History Scope


@dataclass(frozen=True)
class DeploymentHistorySearchScope(SearchScope):
    """Scope for deployment scheduling history search.

    Used for entity-scoped queries where deployment_id is the scope parameter.
    """

    deployment_id: UUID
    """Required. The deployment to search history for."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for DeploymentHistoryRow."""
        return DeploymentHistoryConditions.by_deployment_id_filter(
            UUIDEqualMatchSpec(value=self.deployment_id, negated=False)
        )

    @property
    def existence_checks(self) -> list[ExistenceCheck[Any]]:
        """Check that the deployment (endpoint) exists."""
        return [
            ExistenceCheck(
                column=EndpointRow.id,
                value=self.deployment_id,
                error=EndpointNotFound(str(self.deployment_id)),
            ),
        ]


# Route History Scope


@dataclass(frozen=True)
class RouteHistorySearchScope(SearchScope):
    """Scope for route scheduling history search.

    Used for entity-scoped queries where route_id is the scope parameter.
    """

    route_id: UUID
    """Required. The route to search history for."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for RouteHistoryRow."""
        return RouteHistoryConditions.by_route_id_filter(
            UUIDEqualMatchSpec(value=self.route_id, negated=False)
        )

    @property
    def existence_checks(self) -> list[ExistenceCheck[Any]]:
        """Check that the route exists."""
        return [
            ExistenceCheck(
                column=RoutingRow.id,
                value=self.route_id,
                error=RouteNotFound(str(self.route_id)),
            ),
        ]
