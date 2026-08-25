"""Request DTOs for Label DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.entity.types import EntityTarget

from .types import EntityLabelOrderField, OrderDirection

__all__ = (
    "UpsertEntityLabelInput",
    "EntityLabelFilter",
    "EntityLabelNestedFilter",
    "EntityLabelOrder",
    "EntityLabelPageInput",
    "SearchEntityLabelsInput",
)


class EntityLabelFilter(BaseRequestModel):
    """Filter over label rows.

    One instance matches a single label at a time, so `key` and `value` given together
    constrain the same label rather than two different ones.
    """

    key: StringFilter | None = Field(default=None, description="Label key filter")
    value: StringFilter | None = Field(default=None, description="Label value filter")
    entity_type: StringFilter | None = Field(default=None, description="Type of the labeled entity")
    entity_id: UUIDFilter | None = Field(default=None, description="ID of the labeled entity")
    AND: list[EntityLabelFilter] | None = Field(
        default=None, description="All conditions must match"
    )
    OR: list[EntityLabelFilter] | None = Field(
        default=None, description="At least one condition must match"
    )
    NOT: list[EntityLabelFilter] | None = Field(
        default=None, description="None of the conditions must match"
    )


EntityLabelFilter.model_rebuild()


class EntityLabelNestedFilter(BaseRequestModel):
    """The `labels` field of a labelable entity's filter.

    Each relation matches one label at a time. To require two different labels, combine
    two of these with the entity filter's own `AND`.
    """

    some: EntityLabelFilter | None = Field(
        default=None, description="At least one of the entity's labels matches"
    )
    every: EntityLabelFilter | None = Field(
        default=None,
        description="All of the entity's labels match; true for an unlabeled entity",
    )
    none: EntityLabelFilter | None = Field(
        default=None, description="None of the entity's labels matches"
    )


class EntityLabelOrder(BaseRequestModel):
    """Ordering specification for labels."""

    field: EntityLabelOrderField
    direction: OrderDirection = OrderDirection.DESC


class UpsertEntityLabelInput(BaseRequestModel):
    """Input for putting one key on one entity, replacing the value it carries."""

    target: EntityTarget = Field(description="The entity to label")
    key: str = Field(min_length=1, max_length=255, description="Label key")
    value: str = Field(min_length=1, max_length=255, description="Label value")


class EntityLabelPageInput(BaseRequestModel):
    """One page of labels, over whatever entities the caller has already been fixed to."""

    filter: EntityLabelFilter | None = Field(default=None, description="Filter criteria")
    order: list[EntityLabelOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Offset-based page size")
    offset: int | None = Field(default=None, ge=0, description="Offset-based page offset")


class SearchEntityLabelsInput(EntityLabelPageInput):
    """Input for reading the labels on the entities named."""

    scope: list[EntityTarget] = Field(
        min_length=1, description="The entities whose labels to read (OR across items)"
    )
