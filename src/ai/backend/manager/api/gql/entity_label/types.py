"""GraphQL input types for filtering entities by the labels on them."""

from __future__ import annotations

from typing import Self

from ai.backend.common.dto.manager.v2.entity_label.request import (
    EntityLabelFilter,
    EntityLabelNestedFilter,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import StringFilter, UUIDFilter
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_pydantic_input
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

__all__ = (
    "EntityLabelFilterGQL",
    "EntityLabelNestedFilterGQL",
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Filter matching a single label. A key and a value given together constrain "
            "the same label rather than two different ones."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="EntityLabelFilter",
)
class EntityLabelFilterGQL(PydanticInputMixin[EntityLabelFilter]):
    key: StringFilter | None = None
    value: StringFilter | None = None
    entity_type: StringFilter | None = None
    entity_id: UUIDFilter | None = None

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
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="EntityLabelNestedFilter",
)
class EntityLabelNestedFilterGQL(PydanticInputMixin[EntityLabelNestedFilter]):
    some: EntityLabelFilterGQL | None = None
    every: EntityLabelFilterGQL | None = None
    none: EntityLabelFilterGQL | None = None
