from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from ai.backend.common.types import ServiceCatalogStatus


@dataclass
class ServiceCatalogEndpointData:
    id: UUID
    service_id: UUID
    role: str
    scope: str
    address: str
    port: int
    protocol: str
    metadata: dict[str, Any] | None = field(default=None)


@dataclass
class ServiceCatalogData:
    id: UUID
    service_group: str
    instance_id: str
    display_name: str
    version: str
    labels: dict[str, Any]
    status: ServiceCatalogStatus
    startup_time: datetime
    registered_at: datetime
    last_heartbeat: datetime
    config_hash: str
    endpoints: list[ServiceCatalogEndpointData] = field(default_factory=list)
