"""Response DTOs for Label DTO v2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "UpsertEntityLabelPayload",
    "UpsertEntityLabelError",
    "PartialBulkUpsertEntityLabelPayload",
    "EntityLabelNode",
    "PurgeEntityLabelPayload",
    "PurgeEntityLabelError",
    "PartialBulkPurgeEntityLabelPayload",
    "SearchEntityLabelsPayload",
)


class EntityLabelNode(BaseResponseModel):
    """One `key=value` label and the entity carrying it."""

    id: UUID = Field(description="Label ID")
    field_id: UUID = Field(
        description="UUID of the entity label. Added in 26.9.0.",
    )
    entity_type: str = Field(description="Type of the labeled entity")
    entity_id: UUID = Field(description="ID of the labeled entity")
    key: str = Field(description="Label key")
    value: str = Field(description="Label value")
    created_at: datetime = Field(description="When the label was first put on the entity")
    updated_at: datetime = Field(description="When the label's value was last replaced")


class UpsertEntityLabelPayload(BaseResponseModel):
    """Payload for the label as it now stands."""

    label: EntityLabelNode = Field(description="The label put on the entity")


class UpsertEntityLabelError(BaseResponseModel):
    """One entity a bulk upsert could not label, and the keys it was going to carry."""

    entity_type: str = Field(description="Type of the entity the failed item targeted")
    entity_id: UUID = Field(description="ID of the entity the failed item targeted")
    keys: list[str] = Field(description="The keys that were to be put on the entity")
    message: str = Field(description="Reason the item failed")


class PartialBulkUpsertEntityLabelPayload(BaseResponseModel):
    """Partial-success payload for a bulk label upsert, answered per entity."""

    items: list[EntityLabelNode] = Field(description="The labels put on the entities")
    failed: list[UpsertEntityLabelError] = Field(
        description="Per-entity failures, each naming the entity and the keys it targeted"
    )


class PurgeEntityLabelPayload(BaseResponseModel):
    """Payload for the label that was removed."""

    label: EntityLabelNode = Field(description="The label taken off the entity")


class PurgeEntityLabelError(BaseResponseModel):
    """One label a bulk purge could not take off."""

    id: UUID = Field(description="ID of the label the failed item targeted")
    message: str = Field(description="Reason the item failed")


class PartialBulkPurgeEntityLabelPayload(BaseResponseModel):
    """Partial-success payload for a bulk label purge, answered per label."""

    successes: list[UUID] = Field(description="Ids of the labels taken off")
    failed: list[PurgeEntityLabelError] = Field(
        description="Per-label failures, each naming the label it targeted"
    )


class SearchEntityLabelsPayload(BaseResponseModel):
    """Payload for a page of labels."""

    items: list[EntityLabelNode] = Field(description="Label list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")
