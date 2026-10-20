"""GraphQL filter and order input types for labels."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from ai.backend.common.dto.manager.v2.entity_label.request import (
    EntityLabelFilter,
    EntityLabelNestedFilter,
    EntityLabelOrder,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_enum,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

__all__ = (
    "EntityLabelFilterGQL",
    "EntityLabelNestedFilterGQL",
    "EntityLabelOrderByGQL",
    "EntityLabelOrderFieldGQL",
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Filter matching a single label. A key and a value given together constrain "
            "the same label rather than two different ones."
        ),
        added_version="26.9.0",
    ),
    name="EntityLabelFilter",
)
class EntityLabelFilterGQL(PydanticInputMixin[EntityLabelFilter]):
    key: StringFilter | None = None
    value: StringFilter | None = None
    entity_type: StringFilter | None = None
    entity_id: UUIDFilter | None = None
    field_id: UUIDFilter | None = gql_added_field(
        BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Filter by label ID."),
        default=None,
    )

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Filter selecting entities by the labels on them. Each relation matches one "
            "label at a time; requiring two different labels is two relations combined "
            "by the entity filter's own AND."
        ),
        added_version="26.9.0",
    ),
    name="EntityLabelNestedFilter",
)
class EntityLabelNestedFilterGQL(PydanticInputMixin[EntityLabelNestedFilter]):
    exists: bool | None = None
    some: EntityLabelFilterGQL | None = None
    every: EntityLabelFilterGQL | None = None
    none: EntityLabelFilterGQL | None = None


@gql_enum(
    BackendAIGQLMeta(
        description="Fields available for ordering labels.",
        added_version="26.9.0",
    ),
    name="EntityLabelOrderField",
)
class EntityLabelOrderFieldGQL(StrEnum):
    KEY = "key"
    VALUE = "value"
    CREATED_AT = "created_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Ordering specification for labels.",
        added_version="26.9.0",
    ),
    name="EntityLabelOrderBy",
)
class EntityLabelOrderByGQL(PydanticInputMixin[EntityLabelOrder]):
    field: EntityLabelOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC
