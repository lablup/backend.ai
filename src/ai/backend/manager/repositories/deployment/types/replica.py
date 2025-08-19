"""Replica types for deployment repository."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ReplicaData:
    """Data representing a replica."""

    id: UUID
    endpoint_id: UUID
    session_id: UUID
    route_id: Optional[UUID]
    status: str  # ReplicaStatus from deployment.types
    created_at: datetime
    updated_at: datetime
    agent_id: Optional[str] = None
    container_id: Optional[str] = None


@dataclass(frozen=True)
class ReplicaUpdate:
    """Update data for a replica."""

    id: UUID
    status: Optional[str] = None
    agent_id: Optional[str] = None
    container_id: Optional[str] = None
    route_id: Optional[UUID] = None
