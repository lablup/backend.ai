"""Endpoint and route data types for deployment repository."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import RouteStatus


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

    endpoint_id: uuid.UUID
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

    route_id: uuid.UUID
    endpoint_id: uuid.UUID
    session_id: SessionId | None
    status: RouteStatus
    traffic_ratio: float
    created_at: datetime
    updated_at: datetime | None = None
    error_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteServiceDiscoveryInfo:
    """Service discovery information for a model service route."""

    route_id: uuid.UUID
    endpoint_id: uuid.UUID
    endpoint_name: str
    runtime_variant: str
    kernel_host: str
    kernel_port: int
