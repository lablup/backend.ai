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
    PresetClusterSpec as PresetClusterSpecDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    PresetExecutionSpec as PresetExecutionSpecDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    PresetResourceAllocation as PresetResourceAllocationDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    PresetValueInfo as PresetValueInfoDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    UpdateDeploymentRevisionPresetPayload as UpdatePayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import StringFilter as StringFilterGQL
from ai.backend.manager.api.gql.common.types import ResourceOptsEntryGQL as ResourceOptsEntryInfoGQL
from ai.backend.manager.api.gql.common_types import ResourceSlotEntryGQL as ResourceSlotEntryInfoGQL
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
from ai.backend.manager.api.gql.deployment.types.revision import (
    EnvironmentVariableEntryGQL as EnvironEntryInfoGQL,
)
from ai.backend.manager.api.gql.deployment.types.revision import (
    ModelDefinitionGQL,
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
        description="A single environment variable key-value pair injected into the inference container when a deployment revision preset is applied.",
    ),
    model=EnvironEntryInfoDTO,
    name="DeploymentRevisionPresetEnvironEntry",
)
class EnvironEntryGQL(PydanticOutputMixin[EnvironEntryInfoDTO]):
    key: str = gql_field(
        description="The environment variable name (e.g., CUDA_VISIBLE_DEVICES, HF_HOME)."
    )
    value: str = gql_field(description="The value assigned to the environment variable.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A mapping of a runtime variant preset to a specific value, used to auto-configure runtime parameters when this deployment preset is applied.",
    ),
    model=PresetValueInfoDTO,
    name="DeploymentRevisionPresetValueEntry",
)
class PresetValueEntryGQL(PydanticOutputMixin[PresetValueInfoDTO]):
    preset_id: UUID = gql_field(
        description="The runtime variant preset that this value applies to."
    )
    value: str = gql_field(
        description="The concrete value to set for the referenced preset parameter."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Cluster topology settings for the deployment, defining whether the inference workload runs on a single node or is distributed across multiple nodes.",
    ),
    model=PresetClusterSpecDTO,
    name="PresetClusterSpec",
)
class PresetClusterSpecGQL(PydanticOutputMixin[PresetClusterSpecDTO]):
    cluster_mode: str = gql_field(
        description="Deployment topology mode: 'single-node' runs on one node, 'multi-node' distributes across multiple nodes."
    )
    cluster_size: int = gql_field(
        description="Number of worker nodes in the cluster. For single-node mode, this is typically 1."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Compute resource allocation for the deployment, specifying CPU, memory, and accelerator requirements along with additional resource options.",
    ),
    model=PresetResourceAllocationDTO,
    name="PresetResourceAllocation",
)
class PresetResourceAllocationGQL(PydanticOutputMixin[PresetResourceAllocationDTO]):
    resource_slots: list[ResourceSlotEntryInfoGQL] = gql_field(
        description="CPU, memory, and accelerator allocations (e.g., cpu=4, mem=16g, cuda.device=2)."
    )
    resource_opts: list[ResourceOptsEntryInfoGQL] = gql_field(
        description="Additional resource options such as shared memory (shmem) size."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Container execution configuration for the deployment, including the inference server image, startup commands, and environment variables.",
    ),
    model=PresetExecutionSpecDTO,
    name="PresetExecutionSpec",
)
class PresetExecutionSpecGQL(PydanticOutputMixin[PresetExecutionSpecDTO]):
    image: str | None = gql_field(
        description="Container image to run the inference server (e.g., 'cr.backend.ai/stable/vllm:latest')."
    )
    startup_command: str | None = gql_field(
        description="Command to start the inference server process inside the container."
    )
    bootstrap_script: str | None = gql_field(
        description="Script executed before the main process starts, used for setup tasks like downloading model weights."
    )
    environ: list[EnvironEntryInfoGQL] = gql_field(
        description="Environment variables injected into the inference container."
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A reusable deployment configuration template. Users select a preset when deploying a model to automatically populate resource allocation, execution settings, and runtime-specific parameters. Each preset is designed for a specific runtime variant and captures the full configuration needed to launch an inference service.",
    ),
    name="DeploymentRevisionPreset",
)
class DeploymentRevisionPresetGQL(PydanticNodeMixin[NodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    row_id: UUID = gql_field(
        description="The unique database identifier of this deployment preset."
    )
    runtime_variant_id: UUID = gql_field(
        description="The runtime variant this preset is designed for (e.g., vLLM, SGLang)."
    )
    name: str = gql_field(description="Display name of this deployment configuration template.")
    description: str | None = gql_field(
        description="Detailed explanation of when and why to use this preset configuration."
    )
    rank: int = gql_field(
        description="Display ordering among presets of the same runtime variant, with lower values shown first."
    )
    cluster: PresetClusterSpecGQL = gql_field(
        description="Cluster topology settings defining single-node or multi-node deployment."
    )
    resource: PresetResourceAllocationGQL = gql_field(
        description="Compute resource allocation including CPU, memory, and accelerators."
    )
    execution: PresetExecutionSpecGQL = gql_field(
        description="Container execution configuration including image, startup command, and environment."
    )
    model_definition: ModelDefinitionGQL | None = gql_field(
        description="Parsed model definition specifying health checks, ports, and service configuration for the inference endpoint.",
        default=None,
    )
    preset_values: list[PresetValueEntryGQL] = gql_field(
        description="List of runtime variant preset values applied when using this deployment preset to auto-configure runtime parameters."
    )
    created_at: datetime = gql_field(
        description="Timestamp when this deployment preset was created."
    )
    updated_at: datetime | None = gql_field(
        description="Timestamp of the last modification to this deployment preset."
    )


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
