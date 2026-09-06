"""Response DTOs for Label DTO v2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "UpsertEntityLabelPayload",
    "EntityLabelNode",
    "PurgeEntityLabelPayload",
    "SearchEntityLabelsPayload",
)


class EntityLabelNode(BaseResponseModel):
    """One `key=value` label and the entity carrying it."""

    id: UUID = Field(description="Label ID")
    entity_type: str = Field(description="Type of the labeled entity")
    entity_id: UUID = Field(description="ID of the labeled entity")
    key: str = Field(description="Label key")
    value: str = Field(description="Label value")
    created_at: datetime = Field(description="When the label was first put on the entity")
    updated_at: datetime = Field(description="When the label's value was last replaced")


class UpsertEntityLabelPayload(BaseResponseModel):
    """Payload for the label as it now stands."""

    label: EntityLabelNode = Field(description="The label put on the entity")


class PurgeEntityLabelPayload(BaseResponseModel):
    """Payload for the label that was removed."""

    label: EntityLabelNode = Field(description="The label taken off the entity")


class SearchEntityLabelsPayload(BaseResponseModel):
    """Payload for a page of labels."""

    items: list[EntityLabelNode] = Field(description="Label list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")
