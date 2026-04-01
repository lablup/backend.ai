from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput as CreateInputDTO,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    ModelCardFilter as FilterDTO,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    ModelCardOrder as OrderDTO,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    UpdateModelCardInput as UpdateInputDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    CreateModelCardPayload as CreatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    DeleteModelCardPayload as DeletePayloadDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    ModelCardNode as NodeDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    UpdateModelCardPayload as UpdatePayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import StringFilter as StringFilterGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Order fields for model cards.",
    ),
    name="ModelCardV2OrderField",
)
class ModelCardOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A model card entity.",
    ),
    name="ModelCardV2",
)
class ModelCardGQL(PydanticNodeMixin[NodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    row_id: UUID = gql_field(description="Model card ID.")
    name: str = gql_field(description="Model card name.")
    vfolder_id: UUID = gql_field(description="VFolder ID.")
    domain_name: str = gql_field(description="Domain name.")
    project_id: UUID = gql_field(description="Project ID.")
    creator_id: UUID = gql_field(description="Creator user ID.")
    author: str | None = gql_field(description="Author.")
    title: str | None = gql_field(description="Title.")
    model_version: str | None = gql_field(description="Model version.")
    description: str | None = gql_field(description="Description.")
    task: str | None = gql_field(description="Task type.")
    category: str | None = gql_field(description="Category.")
    architecture: str | None = gql_field(description="Architecture.")
    framework: list[str] = gql_field(description="Frameworks.")
    label: list[str] = gql_field(description="Labels.")
    license: str | None = gql_field(description="License.")
    readme: str | None = gql_field(description="README content.")
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime | None = gql_field(description="Last update timestamp.")


ModelCardV2Edge = Edge[ModelCardGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated list of model cards.",
    )
)
class ModelCardV2Connection(Connection[ModelCardGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Filter for model cards."),
    name="ModelCardV2Filter",
)
class ModelCardFilterGQL(PydanticInputMixin[FilterDTO]):
    name: StringFilterGQL | None = gql_field(default=None, description="Name filter.")
    domain_name: str | None = gql_field(default=None, description="Domain filter.")
    project_id: UUID | None = gql_field(default=None, description="Project filter.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Order specification."),
    name="ModelCardV2OrderBy",
)
class ModelCardOrderByGQL(PydanticInputMixin[OrderDTO]):
    field: ModelCardOrderFieldGQL = gql_field(description="Field to order by.")
    direction: str = gql_field(default="ASC", description="ASC or DESC.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Create model card input."),
    name="CreateModelCardV2Input",
)
class CreateModelCardInputGQL(PydanticInputMixin[CreateInputDTO]):
    name: str = gql_field(description="Model card name.")
    vfolder_id: UUID = gql_field(description="VFolder ID.")
    project_id: UUID = gql_field(description="Project ID.")
    domain_name: str = gql_field(description="Domain name.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Update model card input."),
    name="UpdateModelCardV2Input",
)
class UpdateModelCardInputGQL(PydanticInputMixin[UpdateInputDTO]):
    id: UUID = gql_field(description="Model card ID.")
    name: str | None = gql_field(default=None, description="New name.")
    description: str | None = gql_field(default=None, description="New description.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Create model card payload."),
    model=CreatePayloadDTO,
)
class CreateModelCardPayloadGQL(PydanticOutputMixin[CreatePayloadDTO]):
    model_card: ModelCardGQL = gql_field(description="The created model card.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Update model card payload."),
    model=UpdatePayloadDTO,
)
class UpdateModelCardPayloadGQL(PydanticOutputMixin[UpdatePayloadDTO]):
    model_card: ModelCardGQL = gql_field(description="The updated model card.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Delete model card payload."),
    model=DeletePayloadDTO,
)
class DeleteModelCardPayloadGQL(PydanticOutputMixin[DeletePayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted model card.")
