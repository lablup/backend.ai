from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    CreateRuntimeVariantPresetInput as CreateInputDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    RuntimeVariantPresetFilter as FilterDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    RuntimeVariantPresetOrder as OrderDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    UpdateRuntimeVariantPresetInput as UpdateInputDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    CreateRuntimeVariantPresetPayload as CreatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    DeleteRuntimeVariantPresetPayload as DeletePayloadDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    PresetTargetSpec as PresetTargetSpecDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    RuntimeVariantPresetNode as NodeDTO,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    UpdateRuntimeVariantPresetPayload as UpdatePayloadDTO,
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
        description="Order fields for runtime variant presets.",
    ),
    name="RuntimeVariantPresetOrderField",
)
class RuntimeVariantPresetOrderFieldGQL(StrEnum):
    NAME = "name"
    RANK = "rank"
    CREATED_AT = "created_at"


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Specifies how a runtime variant preset value is applied to the inference container, either as an environment variable or a command-line argument.",
    ),
    model=PresetTargetSpecDTO,
    name="PresetTargetSpec",
)
class PresetTargetSpecGQL(PydanticOutputMixin[PresetTargetSpecDTO]):
    preset_target: str = gql_field(
        description="How the value is applied to the container: 'env' sets it as an environment variable, 'args' appends it as a command-line argument."
    )
    value_type: str = gql_field(
        description="Data type used for input validation (e.g., 'str', 'int', 'float', 'bool')."
    )
    default_value: str | None = gql_field(
        description="The default value shown to users when they create a deployment using this preset."
    )
    key: str = gql_field(
        description="For 'env' target, the environment variable name (e.g., VLLM_TENSOR_PARALLEL_SIZE); for 'args' target, the CLI flag name (e.g., --tensor-parallel)."
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Defines a configurable parameter for a runtime variant. Each preset maps a user-facing setting (e.g., tensor parallelism, quantization) to either an environment variable or a command-line argument that is applied to the inference container.",
    ),
    name="RuntimeVariantPreset",
)
class RuntimeVariantPresetGQL(PydanticNodeMixin[NodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    row_id: UUID = gql_field(description="The unique database identifier of this preset.")
    runtime_variant_id: UUID = gql_field(description="The runtime variant this preset belongs to.")
    name: str = gql_field(
        description="Human-readable name of the configurable parameter (e.g., 'Tensor Parallel Size', 'Quantization')."
    )
    description: str | None = gql_field(
        description="Detailed explanation of what this parameter controls and how it affects inference behavior."
    )
    rank: int = gql_field(
        description="Display ordering among presets of the same runtime variant, with lower values shown first."
    )
    target_spec: PresetTargetSpecGQL = gql_field(
        description="Specification defining how the user-provided value is applied to the inference container."
    )
    created_at: datetime = gql_field(description="Timestamp when this preset was created.")
    updated_at: datetime | None = gql_field(
        description="Timestamp of the last modification to this preset."
    )


RuntimeVariantPresetEdge = Edge[RuntimeVariantPresetGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated list of runtime variant presets.",
    )
)
class RuntimeVariantPresetConnection(Connection[RuntimeVariantPresetGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Filter for presets."),
    name="RuntimeVariantPresetFilter",
)
class RuntimeVariantPresetFilterGQL(PydanticInputMixin[FilterDTO]):
    name: StringFilterGQL | None = gql_field(default=None, description="Name filter.")
    runtime_variant_id: UUID | None = gql_field(default=None, description="Variant ID filter.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Order specification."),
    name="RuntimeVariantPresetOrderBy",
)
class RuntimeVariantPresetOrderByGQL(PydanticInputMixin[OrderDTO]):
    field: RuntimeVariantPresetOrderFieldGQL = gql_field(description="Field to order by.")
    direction: str = gql_field(default="ASC", description="ASC or DESC.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Create preset input."),
    name="CreateRuntimeVariantPresetInput",
)
class CreateRuntimeVariantPresetInputGQL(PydanticInputMixin[CreateInputDTO]):
    runtime_variant_id: UUID = gql_field(description="The runtime variant this preset belongs to.")
    name: str = gql_field(description="Human-readable name of the configurable parameter.")
    description: str | None = gql_field(
        default=None, description="Detailed explanation of what this parameter controls."
    )
    preset_target: str = gql_field(
        description="How the value is applied: 'env' for environment variable, 'args' for command-line argument."
    )
    value_type: str = gql_field(
        description="Data type for validation (e.g., 'str', 'int', 'float', 'bool')."
    )
    default_value: str | None = gql_field(
        default=None, description="The default value shown to users when creating a deployment."
    )
    key: str = gql_field(
        description="For 'env' target, the environment variable name; for 'args' target, the CLI flag name."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Update preset input."),
    name="UpdateRuntimeVariantPresetInput",
)
class UpdateRuntimeVariantPresetInputGQL(PydanticInputMixin[UpdateInputDTO]):
    id: UUID = gql_field(description="Preset ID.")
    name: str | None = gql_field(default=None, description="New name.")
    description: str | None = gql_field(default=None, description="New description.")
    rank: int | None = gql_field(default=None, description="New rank.")
    preset_target: str | None = gql_field(default=None, description="New target.")
    value_type: str | None = gql_field(default=None, description="New value type.")
    default_value: str | None = gql_field(default=None, description="New default value.")
    key: str | None = gql_field(default=None, description="New key.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Create preset payload."),
    model=CreatePayloadDTO,
)
class CreateRuntimeVariantPresetPayloadGQL(PydanticOutputMixin[CreatePayloadDTO]):
    preset: RuntimeVariantPresetGQL = gql_field(description="The created preset.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Update preset payload."),
    model=UpdatePayloadDTO,
)
class UpdateRuntimeVariantPresetPayloadGQL(PydanticOutputMixin[UpdatePayloadDTO]):
    preset: RuntimeVariantPresetGQL = gql_field(description="The updated preset.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Delete preset payload."),
    model=DeletePayloadDTO,
)
class DeleteRuntimeVariantPresetPayloadGQL(PydanticOutputMixin[DeletePayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted preset.")
