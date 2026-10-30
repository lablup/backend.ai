"""Endpoint and route data types for deployment repository."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.scheduling_history.creators import (
    DeploymentHistoryCreator,
    RouteHistoryCreator,
)


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
    resource_group: str | None = None


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


@dataclass
class RouteHistoryToCreate:
    """One replica transition to record, under the deployment it serves."""

    deployment_id: DeploymentID
    creator: RouteHistoryCreator


@dataclass
class DeploymentHistoryToCreate:
    """One deployment transition to record, under the deployment it is about."""

    deployment_id: DeploymentID
    creator: DeploymentHistoryCreator
