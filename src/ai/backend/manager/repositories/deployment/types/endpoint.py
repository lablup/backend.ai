"""Endpoint and route data types for deployment repository."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteSubStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.repositories.base.types import ExistenceCheck, QueryCondition, SearchScope


@dataclass
class EndpointCreationArgs:
    """Arguments for creating an endpoint."""

    name: str
    model_id: uuid.UUID
    owner_id: uuid.UUID
    group_id: uuid.UUID
    domain_name: str
    is_public: bool
    runtime_variant: str
    desired_session_count: int
    resource_opts: dict[str, Any] | None = None
    scaling_group: str | None = None


@dataclass
class EndpointData:
    """Data structure for model service endpoint."""

    deployment_id: DeploymentID
    name: str
    model_id: uuid.UUID
    owner_id: uuid.UUID
    group_id: uuid.UUID
    domain_name: str
    lifecycle: EndpointLifecycle
    is_public: bool
    runtime_variant: str
    desired_session_count: int
    created_at: datetime
    updated_at: datetime | None = None
    service_endpoint: str | None = None
    resource_opts: dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteData:
    """Data structure for model service route."""

    route_id: ReplicaID
    deployment_id: DeploymentID
    session_id: SessionId | None
    status: RouteStatus
    health_status: RouteHealthStatus
    traffic_ratio: float
    created_at: datetime
    revision_id: DeploymentRevisionID
    traffic_status: RouteTrafficStatus
    health_check: ModelHealthCheck | None
    replica_host: str | None = None
    replica_port: int | None = None
    updated_at: datetime | None = None
    sub_status: RouteSubStatus | None = None
    last_transition_at: datetime | None = None
    error_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteSessionKernelInfo:
    """Kernel connection info — only present when session is RUNNING with inference port."""

    replica_host: str
    replica_port: int


@dataclass(frozen=True)
class RouteSessionInfo:
    """Session state for a STARTING route. kernel is None when not yet RUNNING or no port."""

    status: SessionStatus
    kernel: RouteSessionKernelInfo | None


@dataclass
class RouteServiceDiscoveryInfo:
    """Service discovery information for a model service route."""

    route_id: ReplicaID
    deployment_id: DeploymentID
    endpoint_name: str
    runtime_variant: str
    kernel_host: str
    kernel_port: int
    session_owner: uuid.UUID
    project: uuid.UUID


@dataclass(frozen=True)
class ProjectDeploymentSearchScope(SearchScope):
    """Required scope for searching endpoints within a project.

    Used for project-scoped deployment search (project admin).
    """

    project_id: UUID

    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.project == project_id

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        return [
            ExistenceCheck(
                column=GroupRow.id,
                value=self.project_id,
                error=ProjectNotFound(str(self.project_id)),
            ),
        ]


@dataclass(frozen=True)
class UserDeploymentSearchScope(SearchScope):
    """Required scope for searching deployments created by a given user.

    Backs the v2 adapter's ``my_search`` path; the adapter resolves the
    current user and constructs the scope before invoking the action.
    """

    user_id: UUID

    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.created_user == user_id

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        return []
