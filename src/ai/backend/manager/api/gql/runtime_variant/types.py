from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    CreateRuntimeVariantInput as CreateRuntimeVariantInputDTO,
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
    RuntimeVariantNode as RuntimeVariantNodeDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import (
    UpdateRuntimeVariantPayload as UpdateRuntimeVariantPayloadDTO,
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
        added_version=NEXT_RELEASE_VERSION, description="Order fields for runtime variants."
    ),
    name="RuntimeVariantOrderField",
)
class RuntimeVariantOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Represents an inference runtime engine definition (e.g., vLLM, SGLang, NIM, TGI). Previously hardcoded as an enum, runtime variants are now managed as dynamic database entities to allow administrators to register and configure new inference runtimes without code changes.",
    ),
    name="RuntimeVariant",
)
class RuntimeVariantGQL(PydanticNodeMixin[RuntimeVariantNodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    row_id: UUID = gql_field(description="The unique database identifier of this runtime variant.")
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
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Paginated list of runtime variants."
    )
)
class RuntimeVariantConnection(Connection[RuntimeVariantGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Filter for runtime variants."
    ),
    name="RuntimeVariantFilter",
)
class RuntimeVariantFilterGQL(PydanticInputMixin[RuntimeVariantFilterDTO]):
    name: StringFilterGQL | None = gql_field(default=None, description="Name filter.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Order specification."),
    name="RuntimeVariantOrderBy",
)
class RuntimeVariantOrderByGQL(PydanticInputMixin[RuntimeVariantOrderDTO]):
    field: RuntimeVariantOrderFieldGQL = gql_field(description="Field to order by.")
    direction: str = gql_field(default="ASC", description="ASC or DESC.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Input for creating a runtime variant."
    ),
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
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Input for updating a runtime variant."
    ),
    name="UpdateRuntimeVariantInput",
)
class UpdateRuntimeVariantInputGQL(PydanticInputMixin[UpdateRuntimeVariantInputDTO]):
    id: UUID = gql_field(description="Runtime variant ID.")
    name: str | None = gql_field(default=None, description="New name.")
    description: str | None = gql_field(default=None, description="New description.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Payload for runtime variant creation."
    ),
    model=CreateRuntimeVariantPayloadDTO,
)
class CreateRuntimeVariantPayloadGQL(PydanticOutputMixin[CreateRuntimeVariantPayloadDTO]):
    runtime_variant: RuntimeVariantGQL = gql_field(description="The created runtime variant.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Payload for runtime variant update."
    ),
    model=UpdateRuntimeVariantPayloadDTO,
)
class UpdateRuntimeVariantPayloadGQL(PydanticOutputMixin[UpdateRuntimeVariantPayloadDTO]):
    runtime_variant: RuntimeVariantGQL = gql_field(description="The updated runtime variant.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Payload for runtime variant deletion."
    ),
    model=DeleteRuntimeVariantPayloadDTO,
)
class DeleteRuntimeVariantPayloadGQL(PydanticOutputMixin[DeleteRuntimeVariantPayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted runtime variant.")
