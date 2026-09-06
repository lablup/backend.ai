"""Response DTOs of the entity share v2 API."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.entity_share.types import EntityShareStatusDTO
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO

__all__ = (
    "EntityShareNode",
    "EntitySharePayload",
    "SearchEntitySharesPayload",
)


class EntityShareNode(BaseResponseModel):
    id: EntityShareID = Field(description="Share id")
    sharer_user_id: UserID = Field(description="Who sent the offer")
    recipient_entity_type: EntityType | None = Field(
        default=None, description="Type of the scope the offer goes to, once it names one"
    )
    recipient_entity_id: EntityID | None = Field(
        default=None, description="Id of the scope the offer goes to, once it names one"
    )
    recipient_email: str | None = Field(
        default=None, description="Address the offer goes to, when it names one"
    )
    target_entity_type: EntityType = Field(description="Type of the entity being offered")
    target_entity_id: EntityID = Field(description="Id of the entity being offered")
    permissions: list[PermissionBitDTO] = Field(
        description="Permissions the offer caps at; empty for no ceiling"
    )
    status: EntityShareStatusDTO = Field(description="Share status")
    expires_at: datetime | None = Field(
        default=None, description="When the offer stops being answerable; empty for never"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class EntitySharePayload(BaseResponseModel):
    share: EntityShareNode = Field(description="The share the run touched.")


class SearchEntitySharesPayload(BaseResponseModel):
    items: list[EntityShareNode] = Field(description="List of share nodes.")
    total_count: int = Field(description="Total number of shares matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
