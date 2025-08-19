"""Health types for deployment repository."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class HealthData:
    """Data representing health information."""

    endpoint_id: UUID
    healthy_replicas: int
    unhealthy_replicas: int
    total_replicas: int
    last_check_time: Optional[str] = None
    details: Optional[dict[str, str]] = None


@dataclass(frozen=True)
class SessionAppproxyData:
    """Data for session appproxy endpoint."""

    session_id: UUID
    appproxy_url: Optional[str]
    port_mappings: dict[str, int]
