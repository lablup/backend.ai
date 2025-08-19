"""Route types for deployment repository."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from ai.backend.manager.models.routing import RouteStatus


@dataclass(frozen=True)
class RouteData:
    """Data representing a route."""

    id: UUID
    endpoint_id: UUID
    session_id: Optional[UUID]
    status: RouteStatus
    traffic_ratio: float
    created_at: datetime
    updated_at: datetime
    error_data: Optional[dict[str, str]] = None
