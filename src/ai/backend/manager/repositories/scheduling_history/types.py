"""Types for scheduling history repository scopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.manager.errors.deployment import EndpointNotFound
from ai.backend.manager.errors.kernel import (
    EmptyKernelSchedulingHistoryScope,
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

    Either axis may be given; when both are, they intersect. At least one is required —
    an empty scope would degenerate into an unscoped (admin) search.
    """

    session_id: UUID | None = None
    """Restrict to the kernels of this session."""

    kernel_id: UUID | None = None
    """Restrict to this kernel."""

    def __post_init__(self) -> None:
        if self.session_id is None and self.kernel_id is None:
            raise EmptyKernelSchedulingHistoryScope()

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for KernelSchedulingHistoryRow."""
        conditions: list[QueryCondition] = []
        if self.session_id is not None:
            conditions.append(
                KernelSchedulingHistoryConditions.by_session_id_filter(
                    UUIDEqualMatchSpec(value=self.session_id, negated=False)
                )
            )
        if self.kernel_id is not None:
            conditions.append(
                KernelSchedulingHistoryConditions.by_kernel_id_filter(
                    UUIDEqualMatchSpec(value=self.kernel_id, negated=False)
                )
            )

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(*(cond() for cond in conditions))

        return inner

    @property
    @override
    def existence_checks(self) -> list[ExistenceCheck[Any]]:
        """Check that each scoped entity exists."""
        checks: list[ExistenceCheck[Any]] = []
        if self.session_id is not None:
            checks.append(
                ExistenceCheck(
                    column=SessionRow.id,
                    value=self.session_id,
                    error=SessionNotFound(str(self.session_id)),
                )
            )
        if self.kernel_id is not None:
            checks.append(
                ExistenceCheck(
                    column=KernelRow.id,
                    value=self.kernel_id,
                    error=KernelNotFound(str(self.kernel_id)),
                )
            )
        return checks


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
