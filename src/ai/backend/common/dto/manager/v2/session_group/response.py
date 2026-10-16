"""
Response DTOs for SessionGroup v2 API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupPlacementDirectionEnum,
    SessionGroupPlacementEnforcementEnum,
)

__all__ = (
    "AdminSearchSessionGroupsPayload",
    "PurgeSessionGroupPayload",
    "SessionGroupNode",
)


class SessionGroupNode(BaseResponseModel):
    """A set of sessions sharing a placement policy."""

    id: UUID = Field(description="ID of the session group.")
    entity_id: UUID = Field(description="ID of the session group.")
    domain_id: UUID = Field(description="ID of the domain the group belongs to.")
    project_id: UUID = Field(description="ID of the project the group belongs to.")
    owner_user_id: UUID = Field(
        description="ID of the user owning the group. Every member session belongs to this user."
    )
    placement_direction: SessionGroupPlacementDirectionEnum = Field(
        description="Whether member sessions are spread across agents or packed onto them."
    )
    placement_enforcement: SessionGroupPlacementEnforcementEnum = Field(
        description="Whether the direction is a preference or a hard constraint."
    )
    created_at: datetime = Field(description="Creation timestamp.")
    deleted_at: datetime | None = Field(
        default=None, description="Deletion timestamp. Null while the group is in use."
    )


class AdminSearchSessionGroupsPayload(BaseResponseModel):
    """Payload for paginated session group search results."""

    items: list[SessionGroupNode] = Field(description="List of session group nodes.")
    total_count: int = Field(description="Total number of session groups matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class PurgeSessionGroupPayload(BaseResponseModel):
    """Payload naming the session group removed."""

    id: UUID = Field(description="ID of the purged session group.")
