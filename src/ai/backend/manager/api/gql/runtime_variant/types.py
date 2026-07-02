from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID

from strawberry import UNSET
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    CreateRuntimeVariantInput as CreateRuntimeVariantInputDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    DeleteRuntimeVariantsInput as DeleteRuntimeVariantsInputDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    RuntimeVariantFilter as RuntimeVariantFilterDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    RuntimeVariantOrder as RuntimeVariantOrderDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    UpdateRuntimeVariantInput as UpdateRuntimeVariantInputDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import (
    CreateRuntimeVariantPayload as CreateRuntimeVariantPayloadDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import (
    DeleteRuntimeVariantPayload as DeleteRuntimeVariantPayloadDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import (
    DeleteRuntimeVariantsPayload as DeleteRuntimeVariantsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import (
    RuntimeVariantNode as RuntimeVariantNodeDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import (
    UpdateRuntimeVariantPayload as UpdateRuntimeVariantPayloadDTO,
)
from ai.backend.manager.api.gql.base import StringFilter as StringFilterGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin


@gql_enum(
    BackendAIGQLMeta(added_version="26.4.2", description="Order fields for runtime variants."),
    name="RuntimeVariantOrderField",
)
class RuntimeVariantOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Represents an inference runtime engine definition (e.g., vLLM, SGLang, NIM, TGI). Previously hardcoded as an enum, runtime variants are now managed as dynamic database entities to allow administrators to register and configure new inference runtimes without code changes.",
    ),
    name="RuntimeVariant",
)
class RuntimeVariantGQL(PydanticNodeMixin[RuntimeVariantNodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    name: str = gql_field(
        description="Unique short identifier for the runtime engine (e.g., 'vllm', 'sglang', 'nim', 'tgi')."
    )
    description: str | None = gql_field(
        description="Human-readable description explaining the runtime engine and its typical use cases."
    )
    created_at: datetime = gql_field(
        description="Timestamp when this runtime variant was registered."
    )
    updated_at: datetime | None = gql_field(
        description="Timestamp of the last modification to this runtime variant."
    )


RuntimeVariantEdge = Edge[RuntimeVariantGQL]


@gql_connection_type(
    BackendAIGQLMeta(added_version="26.4.2", description="Paginated list of runtime variants.")
)
class RuntimeVariantConnection(Connection[RuntimeVariantGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(added_version="26.4.2", description="Filter for runtime variants."),
    name="RuntimeVariantFilter",
)
class RuntimeVariantFilterGQL(PydanticInputMixin[RuntimeVariantFilterDTO]):
    name: StringFilterGQL | None = gql_field(default=None, description="Name filter.")
    AND: list[Self] | None = gql_added_field(
        BackendAIGQLMeta(added_version="26.7.0", description="Match all of the given sub-filters."),
        default=None,
    )
    OR: list[Self] | None = gql_added_field(
        BackendAIGQLMeta(added_version="26.7.0", description="Match any of the given sub-filters."),
        default=None,
    )
    NOT: list[Self] | None = gql_added_field(
        BackendAIGQLMeta(added_version="26.7.0", description="Negate the given sub-filters."),
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(added_version="26.4.2", description="Order specification."),
    name="RuntimeVariantOrderBy",
)
class RuntimeVariantOrderByGQL(PydanticInputMixin[RuntimeVariantOrderDTO]):
    field: RuntimeVariantOrderFieldGQL = gql_field(description="Field to order by.")
    direction: str = gql_field(default="ASC", description="ASC or DESC.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version="26.4.2", description="Input for creating a runtime variant."),
    name="CreateRuntimeVariantInput",
)
class CreateRuntimeVariantInputGQL(PydanticInputMixin[CreateRuntimeVariantInputDTO]):
    name: str = gql_field(
        description="Unique short identifier for the runtime engine (e.g., 'vllm', 'sglang')."
    )
    description: str | None = gql_field(
        default=None, description="Human-readable description of the runtime engine."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(added_version="26.4.2", description="Input for updating a runtime variant."),
    name="UpdateRuntimeVariantInput",
)
class UpdateRuntimeVariantInputGQL(PydanticInputMixin[UpdateRuntimeVariantInputDTO]):
    id: UUID = gql_field(description="Runtime variant ID.")
    name: str | None = gql_field(default=None, description="New name.")
    description: str | None = gql_field(
        default=UNSET, description="New description. Set to null to clear."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.4.2", description="Payload for runtime variant creation."),
    model=CreateRuntimeVariantPayloadDTO,
    name="CreateRuntimeVariantPayload",
)
class CreateRuntimeVariantPayloadGQL(PydanticOutputMixin[CreateRuntimeVariantPayloadDTO]):
    runtime_variant: RuntimeVariantGQL = gql_field(description="The created runtime variant.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.4.2", description="Payload for runtime variant update."),
    model=UpdateRuntimeVariantPayloadDTO,
    name="UpdateRuntimeVariantPayload",
)
class UpdateRuntimeVariantPayloadGQL(PydanticOutputMixin[UpdateRuntimeVariantPayloadDTO]):
    runtime_variant: RuntimeVariantGQL = gql_field(description="The updated runtime variant.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.4.2", description="Payload for runtime variant deletion."),
    model=DeleteRuntimeVariantPayloadDTO,
    name="DeleteRuntimeVariantPayload",
)
class DeleteRuntimeVariantPayloadGQL(PydanticOutputMixin[DeleteRuntimeVariantPayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted runtime variant.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for deleting multiple runtime variants.",
    ),
    name="DeleteRuntimeVariantsInput",
)
class DeleteRuntimeVariantsInputGQL(PydanticInputMixin[DeleteRuntimeVariantsInputDTO]):
    ids: list[UUID] = gql_field(description="List of runtime variant UUIDs to delete.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for bulk runtime variant deletion.",
    ),
    model=DeleteRuntimeVariantsPayloadDTO,
    name="DeleteRuntimeVariantsPayload",
)
class DeleteRuntimeVariantsPayloadGQL(PydanticOutputMixin[DeleteRuntimeVariantsPayloadDTO]):
    deleted_count: int = gql_field(description="Number of runtime variants successfully deleted.")
