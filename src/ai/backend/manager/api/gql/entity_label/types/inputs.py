"""Label GQL mutation input types."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.entity_label.request import (
    PartialBulkPurgeEntityLabelInput as PartialBulkPurgeEntityLabelInputDTO,
)
from ai.backend.common.dto.manager.v2.entity_label.request import (
    PartialBulkUpsertEntityLabelInput as PartialBulkUpsertEntityLabelInputDTO,
)
from ai.backend.common.dto.manager.v2.entity_label.request import (
    UpsertEntityLabelInput as UpsertEntityLabelInputDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.entity.types.inputs import EntityTargetGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

__all__ = (
    "UpsertEntityLabelInputGQL",
    "PartialBulkUpsertEntityLabelInputGQL",
    "PartialBulkPurgeEntityLabelInputGQL",
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Input for putting one key on one entity. A key holds one value, so naming a "
            "key the entity already carries replaces that value."
        ),
        added_version="26.9.0",
    ),
    name="UpsertEntityLabelInput",
)
class UpsertEntityLabelInputGQL(PydanticInputMixin[UpsertEntityLabelInputDTO]):
    target: EntityTargetGQL = gql_field(description="The entity to label.")
    key: str = gql_field(description="Label key.")
    value: str = gql_field(description="Label value.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Input for putting several keys on several entities in one call. Answered per "
            "entity: an entity's keys are written together or refused together."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="PartialBulkUpsertEntityLabelInput",
)
class PartialBulkUpsertEntityLabelInputGQL(
    PydanticInputMixin[PartialBulkUpsertEntityLabelInputDTO]
):
    items: list[UpsertEntityLabelInputGQL] = gql_field(
        description="The labels to put, each naming the entity it goes on."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for taking several labels off in one call, each named by its own id.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="PartialBulkPurgeEntityLabelInput",
)
class PartialBulkPurgeEntityLabelInputGQL(PydanticInputMixin[PartialBulkPurgeEntityLabelInputDTO]):
    ids: list[UUID] = gql_field(description="Ids of the labels to take off.")
