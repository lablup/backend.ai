"""GraphQL types for deployment revision presets."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    CreateDeploymentRevisionPresetInput as CreateInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    DeploymentRevisionPresetFilter as FilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    DeploymentRevisionPresetOrder as OrderDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    UpdateDeploymentRevisionPresetInput as UpdateInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    CreateDeploymentRevisionPresetPayload as CreatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    DeleteDeploymentRevisionPresetPayload as DeletePayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    DeploymentRevisionPresetNode as NodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    EnvironEntryInfo as EnvironEntryInfoDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    PresetValueInfo as PresetValueInfoDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    UpdateDeploymentRevisionPresetPayload as UpdatePayloadDTO,
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
        description="Order fields for deployment revision presets.",
    ),
    name="DeploymentRevisionPresetOrderField",
)
class DeploymentRevisionPresetOrderFieldGQL(StrEnum):
    NAME = "name"
    RANK = "rank"
    CREATED_AT = "created_at"


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="An environment variable entry.",
    ),
    model=EnvironEntryInfoDTO,
    name="DeploymentRevisionPresetEnvironEntry",
)
class EnvironEntryGQL(PydanticOutputMixin[EnvironEntryInfoDTO]):
    key: str = gql_field(description="Environment variable key.")
    value: str = gql_field(description="Environment variable value.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A preset value entry.",
    ),
    model=PresetValueInfoDTO,
    name="DeploymentRevisionPresetValueEntry",
)
class PresetValueEntryGQL(PydanticOutputMixin[PresetValueInfoDTO]):
    preset_id: UUID = gql_field(description="Runtime variant preset ID.")
    value: str = gql_field(description="Value for this preset.")


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A deployment revision preset entity.",
    ),
    name="DeploymentRevisionPreset",
)
class DeploymentRevisionPresetGQL(PydanticNodeMixin[NodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    row_id: UUID = gql_field(description="Preset ID.")
    runtime_variant_id: UUID = gql_field(description="Runtime variant ID.")
    name: str = gql_field(description="Preset name.")
    description: str | None = gql_field(description="Description.")
    rank: int = gql_field(description="Display order rank.")
    image: str | None = gql_field(description="Container image reference.")
    cluster_mode: str = gql_field(description="Cluster mode.")
    cluster_size: int = gql_field(description="Cluster size.")
    startup_command: str | None = gql_field(description="Startup command.")
    bootstrap_script: str | None = gql_field(description="Bootstrap script.")
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime | None = gql_field(description="Last update timestamp.")


DeploymentRevisionPresetEdge = Edge[DeploymentRevisionPresetGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated list of deployment revision presets.",
    )
)
class DeploymentRevisionPresetConnection(Connection[DeploymentRevisionPresetGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for deployment revision presets.",
    ),
    name="DeploymentRevisionPresetFilter",
)
class DeploymentRevisionPresetFilterGQL(PydanticInputMixin[FilterDTO]):
    name: StringFilterGQL | None = gql_field(default=None, description="Name filter.")
    runtime_variant_id: UUID | None = gql_field(default=None, description="Variant ID filter.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Order specification for deployment revision presets.",
    ),
    name="DeploymentRevisionPresetOrderBy",
)
class DeploymentRevisionPresetOrderByGQL(PydanticInputMixin[OrderDTO]):
    field: DeploymentRevisionPresetOrderFieldGQL = gql_field(description="Field to order by.")
    direction: str = gql_field(default="ASC", description="ASC or DESC.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create deployment revision preset input.",
    ),
    name="CreateDeploymentRevisionPresetInput",
)
class CreateDeploymentRevisionPresetInputGQL(PydanticInputMixin[CreateInputDTO]):
    runtime_variant_id: UUID = gql_field(description="Runtime variant ID.")
    name: str = gql_field(description="Preset name.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update deployment revision preset input.",
    ),
    name="UpdateDeploymentRevisionPresetInput",
)
class UpdateDeploymentRevisionPresetInputGQL(PydanticInputMixin[UpdateInputDTO]):
    id: UUID = gql_field(description="Preset ID.")
    name: str | None = gql_field(default=None, description="New name.")
    description: str | None = gql_field(default=None, description="New description.")
    rank: int | None = gql_field(default=None, description="New rank.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create deployment revision preset payload.",
    ),
    model=CreatePayloadDTO,
)
class CreateDeploymentRevisionPresetPayloadGQL(PydanticOutputMixin[CreatePayloadDTO]):
    preset: DeploymentRevisionPresetGQL = gql_field(description="The created preset.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update deployment revision preset payload.",
    ),
    model=UpdatePayloadDTO,
)
class UpdateDeploymentRevisionPresetPayloadGQL(PydanticOutputMixin[UpdatePayloadDTO]):
    preset: DeploymentRevisionPresetGQL = gql_field(description="The updated preset.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete deployment revision preset payload.",
    ),
    model=DeletePayloadDTO,
)
class DeleteDeploymentRevisionPresetPayloadGQL(PydanticOutputMixin[DeletePayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted preset.")
