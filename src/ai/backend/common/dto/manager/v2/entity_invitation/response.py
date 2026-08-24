"""Response DTOs of the entity invitation v2 API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.permission.types import OperationType
from ai.backend.common.dto.manager.v2.entity_invitation.types import EntityInvitationStatusDTO

__all__ = (
    "EntityInvitationNode",
    "EntityInvitationPayload",
    "SearchEntityInvitationsPayload",
)


class EntityInvitationNode(BaseResponseModel):
    id: UUID = Field(description="Invitation id")
    inviter_user_id: UUID = Field(description="Who sent the offer")
    invitee_email: str = Field(description="Address the offer goes to")
    target_entity_type: str = Field(description="Type of the entity being offered")
    target_entity_id: UUID = Field(description="Id of the entity being offered")
    operations: list[OperationType] = Field(
        description="Operations the offer allows; empty for no ceiling"
    )
    status: EntityInvitationStatusDTO = Field(description="Invitation status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class EntityInvitationPayload(BaseResponseModel):
    invitation: EntityInvitationNode = Field(description="The invitation the run touched.")


class SearchEntityInvitationsPayload(BaseResponseModel):
    items: list[EntityInvitationNode] = Field(description="List of invitation nodes.")
    total_count: int = Field(description="Total number of invitations matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
