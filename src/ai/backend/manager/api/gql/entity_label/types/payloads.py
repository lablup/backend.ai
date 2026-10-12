"""Label GQL mutation payload types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.entity_label.response import (
    PurgeEntityLabelPayload as PurgeEntityLabelPayloadDTO,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    UpsertEntityLabelPayload as UpsertEntityLabelPayloadDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

from .node import EntityLabelGQL

__all__ = (
    "PurgeEntityLabelPayloadGQL",
    "UpsertEntityLabelPayloadGQL",
)


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Payload returned after putting a label on an entity.",
        added_version="26.9.0",
    ),
    model=UpsertEntityLabelPayloadDTO,
    name="UpsertEntityLabelPayload",
)
class UpsertEntityLabelPayloadGQL(PydanticOutputMixin[UpsertEntityLabelPayloadDTO]):
    label: EntityLabelGQL = gql_field(description="The label as it now stands.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Payload returned after taking a label off an entity.",
        added_version="26.9.0",
    ),
    model=PurgeEntityLabelPayloadDTO,
    name="PurgeEntityLabelPayload",
)
class PurgeEntityLabelPayloadGQL(PydanticOutputMixin[PurgeEntityLabelPayloadDTO]):
    label: EntityLabelGQL = gql_field(description="The label taken off the entity.")
