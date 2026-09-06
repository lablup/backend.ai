"""Label GQL mutation input types."""

from __future__ import annotations

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

__all__ = ("UpsertEntityLabelInputGQL",)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Input for putting one key on one entity. A key holds one value, so naming a "
            "key the entity already carries replaces that value."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="UpsertEntityLabelInput",
)
class UpsertEntityLabelInputGQL(PydanticInputMixin[UpsertEntityLabelInputDTO]):
    target: EntityTargetGQL = gql_field(description="The entity to label.")
    key: str = gql_field(description="Label key.")
    value: str = gql_field(description="Label value.")
