"""Entity reference GQL input."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.entity.types import EntityTarget
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

__all__ = ("EntityTargetGQL",)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "One entity, named by its type and its id. `entityTypes` lists the types a "
            "request may name."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="EntityTarget",
)
class EntityTargetGQL(PydanticInputMixin[EntityTarget]):
    entity_type: str = gql_field(description="Type of the entity.")
    entity_id: UUID = gql_field(description="ID of the entity.")
