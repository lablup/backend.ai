"""Types for scheduling history repository scopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.errors.deployment import EndpointNotFound
from ai.backend.manager.errors.kernel import (
    KernelNotFound,
    SessionNotFound,
)
from ai.backend.manager.errors.service import RouteNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scheduling_history.conditions import (
    DeploymentHistoryConditions,
    KernelSchedulingHistoryConditions,
    RouteHistoryConditions,
    SessionSchedulingHistoryConditions,
)
from ai.backend.manager.models.scopes import ExistenceCheck, SearchScope
from ai.backend.manager.models.session import SessionRow

__all__ = (
    "SessionSchedulingHistorySearchScope",
    "KernelSchedulingHistoryBySessionSearchScope",
    "KernelSchedulingHistorySearchScope",
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

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for SessionSchedulingHistoryRow."""
        return SessionSchedulingHistoryConditions.by_session_id_filter(
            UUIDEqualMatchSpec(value=self.session_id, negated=False)
        )

    @property
    @override
    def existence_checks(self) -> list[ExistenceCheck[Any]]:
        """Check that the session exists."""
        return [
            ExistenceCheck(
                column=SessionRow.id,
                value=self.session_id,
                error=SessionNotFound(str(self.session_id)),
            ),
        ]


# Kernel Scheduling History Scope


@dataclass(frozen=True)
class KernelSchedulingHistorySearchScope(SearchScope):
    """Scope for kernel scheduling history search.

    Used for entity-scoped queries where kernel_id is the scope parameter.
    """

    kernel_id: KernelId
    """Required. The kernel to search history for."""

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for KernelSchedulingHistoryRow."""
        return KernelSchedulingHistoryConditions.by_kernel_id_filter(
            UUIDEqualMatchSpec(value=self.kernel_id, negated=False)
        )

    @property
    @override
    def existence_checks(self) -> list[ExistenceCheck[Any]]:
        """Check that the kernel exists."""
        return [
            ExistenceCheck(
                column=KernelRow.id,
                value=self.kernel_id,
                error=KernelNotFound(str(self.kernel_id)),
            ),
        ]


@dataclass(frozen=True)
class KernelSchedulingHistoryBySessionSearchScope(SearchScope):
    """Scope for kernel scheduling history search bounded by the owning session.

    Returns the history of every kernel belonging to the session, as opposed to
    ``KernelSchedulingHistorySearchScope`` which bounds the query to one kernel.
    """

    session_id: SessionId
    """Required. The session whose kernels' history is searched."""

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for KernelSchedulingHistoryRow."""
        return KernelSchedulingHistoryConditions.by_session_id_filter(
            UUIDEqualMatchSpec(value=self.session_id, negated=False)
        )

    @property
    @override
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

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for DeploymentHistoryRow."""
        return DeploymentHistoryConditions.by_deployment_id_filter(
            UUIDEqualMatchSpec(value=self.deployment_id, negated=False)
        )

    @property
    @override
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

    route_id: ReplicaID
    """Required. The route to search history for."""

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for RouteHistoryRow."""
        return RouteHistoryConditions.by_route_id_filter(
            UUIDEqualMatchSpec(value=self.route_id, negated=False)
        )

    @property
    @override
    def existence_checks(self) -> list[ExistenceCheck[Any]]:
        """Check that the route exists."""
        return [
            ExistenceCheck(
                column=RoutingRow.id,
                value=self.route_id,
                error=RouteNotFound(str(self.route_id)),
            ),
        ]
