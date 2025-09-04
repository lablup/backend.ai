"""Endpoint and route data types for deployment repository."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from ai.backend.common.types import SessionId
from ai.backend.manager.data.model_serving.types import EndpointLifecycle, RouteStatus


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
    resource_opts: Optional[dict[str, Any]] = None
    scaling_group: Optional[str] = None


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
    updated_at: Optional[datetime] = None
    service_endpoint: Optional[str] = None
    resource_opts: dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteData:
    """Data structure for model service route."""

    route_id: uuid.UUID
    endpoint_id: uuid.UUID
    session_id: Optional[SessionId]
    status: RouteStatus
    traffic_ratio: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_data: dict[str, Any] = field(default_factory=dict)
