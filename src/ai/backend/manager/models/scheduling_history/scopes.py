"""Operation scopes for scheduling history."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.errors.deployment import EndpointNotFound
from ai.backend.manager.errors.kernel import KernelNotFound, SessionNotFound
from ai.backend.manager.errors.service import RouteNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scheduling_history.conditions import (
    DeploymentHistoryConditions,
    KernelSchedulingHistoryConditions,
    RouteHistoryConditions,
    SessionSchedulingHistoryConditions,
)
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope, ScopeTarget
from ai.backend.manager.models.session import SessionRow

__all__ = (
    "DeploymentHistoryTarget",
    "DeploymentReplicaGroupHistoryTarget",
    "KernelHistoryTarget",
    "KernelKernelHistoryTarget",
    "RouteHistoryTarget",
    "SessionKernelHistoryTarget",
    "SessionSchedulingHistoryTarget",
)


@dataclass(frozen=True)
class SessionSchedulingHistoryTarget(ScopeTarget):
    """Scope for session scheduling history search.

    Used for entity-scoped queries where session_id is the scope parameter.
    """

    session_id: UUID
    """Required. The session to search history for."""

    @override
    def scope_id(self) -> EntityIdentifier:
        return SessionID(self.session_id)

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


class KernelHistoryTarget(ScopeTarget, ABC):
    """One side a kernel's scheduling history is read from."""


@dataclass(frozen=True)
class KernelKernelHistoryTarget(KernelHistoryTarget):
    """Scope for kernel scheduling history search bounded by one kernel.

    Not reachable yet: kernels hold no RBAC permission records of their own, so
    a kernel-keyed query is authorized on the owning session and narrowed with a
    ``kernel_id`` condition instead. This is what it should scope by once
    virtual entities land.
    """

    kernel_id: KernelId
    """Required. The kernel to search history for."""

    @override
    def scope_id(self) -> EntityIdentifier:
        return SessionID(self.kernel_id)

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
class SessionKernelHistoryTarget(KernelHistoryTarget):
    """Scope for kernel scheduling history search bounded by the owning session.

    Returns the history of every kernel belonging to the session.
    """

    session_id: SessionId
    """Required. The session whose kernels' history is searched."""

    @override
    def scope_id(self) -> EntityIdentifier:
        return SessionID(self.session_id)

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


@dataclass(frozen=True)
class DeploymentHistoryTarget(ScopeTarget):
    """Scope for deployment scheduling history search.

    Used for entity-scoped queries where deployment_id is the scope parameter.
    """

    deployment_id: UUID
    """Required. The deployment to search history for."""

    @override
    def scope_id(self) -> EntityIdentifier:
        return DeploymentID(self.deployment_id)

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


@dataclass(frozen=True)
class DeploymentReplicaGroupHistoryTarget(ScopeTarget):
    """Scope for replica-group history search bounded by the owning deployment.

    Returns the history of every replica group belonging to the deployment.
    """

    deployment_id: DeploymentID
    """Required. The deployment whose replica groups' history is searched."""

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.deployment_id

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for ReplicaGroupHistoryRow."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.deployment_id == self.deployment_id

        return inner

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


@dataclass(frozen=True)
class RouteHistoryTarget(OperationScope):
    """Scope for route scheduling history search.

    Used for entity-scoped queries where route_id is the scope parameter.

    Names no scope of its own: a replica is authorized through the deployment that owns
    it, and this carries only the replica's id.
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
