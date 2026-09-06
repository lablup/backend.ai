"""Response DTOs of the entity invitation v2 API."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.entity_invitation.types import EntityInvitationStatusDTO
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO

__all__ = (
    "EntityInvitationNode",
    "EntityInvitationPayload",
    "SearchEntityInvitationsPayload",
)


class EntityInvitationNode(BaseResponseModel):
    id: EntityInvitationID = Field(description="Invitation id")
    inviter_user_id: UserID = Field(description="Who sent the offer")
    invitee_email: str = Field(description="Address the offer goes to")
    target_entity_type: EntityType = Field(description="Type of the entity being offered")
    target_entity_id: EntityID = Field(description="Id of the entity being offered")
    permissions: list[PermissionBitDTO] = Field(
        description="Permissions the offer caps at; empty for no ceiling"
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
