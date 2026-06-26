"""GraphQL types for deployment revision presets."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

import strawberry
from strawberry import UNSET, Info
from strawberry.relay import Connection, Edge, NodeID
from strawberry.scalars import JSON

from ai.backend.common.config import DEFAULT_SHELL
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.request import (
    DeploymentStrategyInput as DeploymentStrategyInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    PresetValueInput as PresetValueInputDTO,
)
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
    PresetModelConfigInput as PresetModelConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    PresetModelDefinitionInput as PresetModelDefinitionInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    PresetModelHealthCheckInput as PresetModelHealthCheckInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    PresetModelMetadataInput as PresetModelMetadataInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    PresetModelServiceConfigInput as PresetModelServiceConfigInputDTO,
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
    PresetDeploymentDefaults as PresetDeploymentDefaultsDTO,
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
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import StringFilter as StringFilterGQL
from ai.backend.manager.api.gql.base import UUIDFilter as UUIDFilterGQL
from ai.backend.manager.api.gql.common.types import (
    ClusterModeGQL,
    EnvironEntryInputGQL,
    ResourceOptsEntryInput,
)
from ai.backend.manager.api.gql.common.types import ResourceOptsEntryGQL as ResourceOptsEntryInfoGQL
from ai.backend.manager.api.gql.common_types import ResourceSlotEntryInputGQL
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
from ai.backend.manager.api.gql.deployment.types.policy import (
    BlueGreenConfigInputGQL,
    RollingUpdateConfigInputGQL,
)
from ai.backend.manager.api.gql.deployment.types.resource_slot import (
    RESOURCE_SLOTS_FETCH_LIMIT,
    AllocatedResourceSlotFilterGQL,
    AllocatedResourceSlotGQL,
    AllocatedResourceSlotOrderByGQL,
)
from ai.backend.manager.api.gql.deployment.types.revision import (
    ModelDefinitionGQL,
    ModelDefinitionInputGQL,
    PreStartActionInputGQL,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.image.types import ImageV2GQL
    from ai.backend.manager.api.gql.runtime_variant.types import RuntimeVariantGQL


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.2",
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
        added_version="26.4.4",
        description="A mapping of a runtime variant preset to a specific value, used to auto-configure runtime parameters when this deployment preset is applied.",
    ),
    model=PresetValueInfoDTO,
    name="RuntimeVariantPresetValueEntry",
)
class RuntimeVariantPresetValueEntryGQL(PydanticOutputMixin[PresetValueInfoDTO]):
    preset_id: UUID = gql_field(
        description="The runtime variant preset that this value applies to."
    )
    value: str = gql_field(
        description="The concrete value to set for the referenced preset parameter."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.2",
        description="Compute resource allocation for the deployment, specifying CPU, memory, and accelerator requirements along with additional resource options.",
    ),
    model=PresetResourceAllocationDTO,
    name="PresetResourceAllocation",
)
class PresetResourceAllocationGQL(PydanticOutputMixin[PresetResourceAllocationDTO]):
    resource_opts: list[ResourceOptsEntryInfoGQL] = gql_field(
        description="Additional resource options such as shared memory (shmem) size."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Container execution configuration for the deployment, including the inference server image, startup commands, and environment variables.",
    ),
    model=PresetExecutionSpecDTO,
    name="PresetExecutionSpec",
)
class PresetExecutionSpecGQL(PydanticOutputMixin[PresetExecutionSpecDTO]):
    image_id: UUID | None = gql_field(
        description="UUID of the container image used to run the inference server."
    )
    startup_command: str | None = gql_field(
        description="Command to start the inference server process inside the container."
    )
    bootstrap_script: str | None = gql_field(
        description="Script executed before the main process starts, used for setup tasks like downloading model weights."
    )
    environ: list[EnvironEntryGQL] = gql_field(
        description="Environment variables injected into the inference container."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Deployment-level defaults stored on the preset. Any null field "
        "means the preset does not specify a default and callers should fall back to "
        "user input or the system default.",
    ),
    model=PresetDeploymentDefaultsDTO,
    name="PresetDeploymentDefaults",
)
class PresetDeploymentDefaultsGQL(PydanticOutputMixin[PresetDeploymentDefaultsDTO]):
    open_to_public: bool | None = gql_field(
        default=None,
        description="Default open_to_public for deployments created from this preset.",
    )
    replica_count: int | None = gql_field(
        default=None,
        description="Default replica count for deployments created from this preset.",
    )
    revision_history_limit: int | None = gql_field(
        default=None,
        description="Default revision history limit for deployments created from this preset.",
    )
    deployment_strategy: DeploymentStrategy | None = gql_field(
        default=None,
        description="Default deployment strategy type (ROLLING or BLUE_GREEN).",
    )
    deployment_strategy_spec: JSON | None = gql_field(
        default=None,
        description="Strategy-specific configuration (rolling or blue-green).",
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="A reusable deployment configuration template. Users select a preset when deploying a model to automatically populate resource allocation, execution settings, and runtime-specific parameters. Each preset is designed for a specific runtime variant and captures the full configuration needed to launch an inference service.",
    ),
    name="DeploymentRevisionPreset",
)
class DeploymentRevisionPresetGQL(PydanticNodeMixin[NodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
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
    deployment_defaults: PresetDeploymentDefaultsGQL = gql_field(
        description="Deployment-level default values (open_to_public, replica_count, "
        "revision_history_limit, deployment_strategy) provided by this preset."
    )
    model_definition: ModelDefinitionGQL | None = gql_field(
        description="Parsed model definition specifying health checks, ports, and service configuration for the inference endpoint.",
        default=None,
    )
    preset_values: list[RuntimeVariantPresetValueEntryGQL] = gql_field(
        description="List of runtime variant preset values applied when using this deployment preset to auto-configure runtime parameters."
    )
    created_at: datetime = gql_field(
        description="Timestamp when this deployment preset was created."
    )
    updated_at: datetime | None = gql_field(
        description="Timestamp of the last modification to this deployment preset."
    )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3",
            description="The runtime variant this preset is designed for.",
        )
    )  # type: ignore[misc]
    async def runtime_variant(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            RuntimeVariantGQL,
            strawberry.lazy("ai.backend.manager.api.gql.runtime_variant.types"),
        ]
        | None
    ):
        return await info.context.data_loaders.runtime_variant_loader.load(self.runtime_variant_id)

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="The container image used to run the inference server. None when the preset does not specify an image.",
        )
    )  # type: ignore[misc]
    async def image(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            ImageV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.image.types"),
        ]
        | None
    ):
        if self.execution.image_id is None:
            return None
        return await info.context.data_loaders.image_loader.load(ImageID(self.execution.image_id))

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.2",
            description="Resource slot allocations for this preset.",
        )
    )  # type: ignore[misc]
    async def resource_slots(
        self,
        info: Info[StrawberryGQLContext],
        filter: AllocatedResourceSlotFilterGQL | None = None,
        order_by: list[AllocatedResourceSlotOrderByGQL] | None = None,
    ) -> list[AllocatedResourceSlotGQL] | None:
        from ai.backend.common.dto.manager.v2.resource_slot.request import (
            SearchAllocatedResourceSlotsInput,
        )

        payload = await info.context.adapters.deployment_revision_preset.search_resource_slots(
            preset_id=UUID(self.id),
            input=SearchAllocatedResourceSlotsInput(
                filter=filter.to_pydantic() if filter else None,
                order=[o.to_pydantic() for o in order_by] if order_by else None,
                limit=RESOURCE_SLOTS_FETCH_LIMIT,
            ),
        )
        return [AllocatedResourceSlotGQL.from_pydantic(item) for item in payload.items]


DeploymentRevisionPresetEdge = Edge[DeploymentRevisionPresetGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.4",
        description="A mapping of a runtime variant preset to a concrete value, used to auto-configure runtime parameters when this deployment preset is applied.",
    ),
    name="RuntimeVariantPresetValueEntryInput",
)
class RuntimeVariantPresetValueEntryInputGQL(PydanticInputMixin[PresetValueInputDTO]):
    preset_id: UUID = gql_field(
        description="The runtime variant preset that this value applies to."
    )
    value: str = gql_field(
        description="The concrete value to set for the referenced preset parameter."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Filter for deployment revision presets.",
    ),
    name="DeploymentRevisionPresetFilter",
)
class DeploymentRevisionPresetFilterGQL(PydanticInputMixin[FilterDTO]):
    id: UUIDFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(added_version="26.4.4", description="Filter by preset ID."),
        default=None,
    )
    name: StringFilterGQL | None = gql_field(default=None, description="Name filter.")
    runtime_variant_id: UUIDFilterGQL | None = gql_field(
        default=None, description="Variant ID filter."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Order specification for deployment revision presets.",
    ),
    name="DeploymentRevisionPresetOrderBy",
)
class DeploymentRevisionPresetOrderByGQL(PydanticInputMixin[OrderDTO]):
    field: DeploymentRevisionPresetOrderFieldGQL = gql_field(description="Field to order by.")
    direction: str = gql_field(default="ASC", description="ASC or DESC.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Deployment strategy input for a revision preset, used to "
        "establish a default deployment strategy applied to any deployment "
        "created from this preset.",
    ),
    name="PresetDeploymentStrategyInput",
)
class PresetDeploymentStrategyInputGQL(PydanticInputMixin[DeploymentStrategyInputDTO]):
    type: DeploymentStrategy = gql_field(description="Strategy type (ROLLING or BLUE_GREEN).")
    rolling_update: RollingUpdateConfigInputGQL | None = gql_field(
        default=None,
        description="Rolling update configuration (required when type is ROLLING).",
    )
    blue_green: BlueGreenConfigInputGQL | None = gql_field(
        default=None,
        description="Blue/green configuration (required when type is BLUE_GREEN).",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Strict health check configuration for a preset model service.",
    ),
    name="PresetModelHealthCheckInput",
)
class PresetModelHealthCheckInputGQL(PydanticInputMixin[PresetModelHealthCheckInputDTO]):
    enable: bool = gql_field(
        description=(
            "Whether the route should be health-checked. When false the route activates "
            "immediately and the remaining fields are ignored."
        ),
        default=False,
    )
    interval: float = gql_field(
        description="Interval in seconds between health checks.", default=10.0
    )
    path: str = gql_field(description="Path to check for health status.", default="/health")
    max_retries: int = gql_field(
        description="Maximum number of retries for health check.", default=10
    )
    max_wait_time: float = gql_field(
        description="Maximum time in seconds to wait for a health check response.", default=15.0
    )
    expected_status_code: int = gql_field(
        description="Expected HTTP status code for a healthy response.", default=200
    )
    initial_delay: float = gql_field(
        description="Initial delay in seconds before the first health check.", default=1800.0
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Strict metadata describing a preset model entry.",
    ),
    name="PresetModelMetadataInput",
)
class PresetModelMetadataInputGQL(PydanticInputMixin[PresetModelMetadataInputDTO]):
    author: str | None = gql_field(description="Author of the model.", default=None)
    title: str | None = gql_field(description="Title of the model.", default=None)
    version: str | None = gql_field(description="Version of the model.", default=None)
    created: str | None = gql_field(description="Creation date of the model.", default=None)
    last_modified: str | None = gql_field(
        description="Last modified date of the model.", default=None
    )
    description: str | None = gql_field(description="Description of the model.", default=None)
    task: str | None = gql_field(description="Task type of the model.", default=None)
    category: str | None = gql_field(description="Category of the model.", default=None)
    architecture: str | None = gql_field(description="Architecture of the model.", default=None)
    framework: list[str] | None = gql_field(
        description="Frameworks used by the model.", default=None
    )
    label: list[str] | None = gql_field(description="Labels for the model.", default=None)
    license: str | None = gql_field(description="License of the model.", default=None)
    min_resource: JSON | None = gql_field(
        description="Minimum resource requirements for the model.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Strict service configuration for a preset model entry.",
    ),
    name="PresetModelServiceConfigInput",
)
class PresetModelServiceConfigInputGQL(PydanticInputMixin[PresetModelServiceConfigInputDTO]):
    pre_start_actions: list[PreStartActionInputGQL] = gql_field(
        description="Pre-start actions to execute before starting the model service. "
        "Provide an empty list when no pre-start actions are needed.",
    )
    command: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Single-string command to start the model service.",
        ),
        default=None,
    )
    start_command: list[str] | None = gql_field(
        description=(
            "Deprecated since 26.7.0. Command to start the model service. Do "
            "not set together with `command`; when both are set, `command` takes precedence and "
            "this field is ignored."
        ),
        default=None,
        deprecation_reason="Use `command` instead.",
    )
    shell: str = gql_field(
        description="Shell configured for the model service.", default=DEFAULT_SHELL
    )
    port: int = gql_field(
        description="Port number for the model service. Must be greater than 1.",
    )
    health_check: PresetModelHealthCheckInputGQL | None = gql_field(
        description="Health check configuration for the model service.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Strict configuration for a single model within a preset model definition.",
    ),
    name="PresetModelConfigInput",
)
class PresetModelConfigInputGQL(PydanticInputMixin[PresetModelConfigInputDTO]):
    name: str = gql_field(description="Name of the model.")
    model_path: str = gql_field(description="Path to the model file.")
    service: PresetModelServiceConfigInputGQL = gql_field(
        description="Configuration for the model service.",
    )
    metadata: PresetModelMetadataInputGQL | None = gql_field(
        description="Metadata about the model.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Strict model definition for a preset. When provided on create it must be "
        "fully populated with at least one model.",
    ),
    name="PresetModelDefinitionInput",
)
class PresetModelDefinitionInputGQL(PydanticInputMixin[PresetModelDefinitionInputDTO]):
    models: list[PresetModelConfigInputGQL] = gql_field(
        description="List of models in the model definition. Must contain at least one model.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Create deployment revision preset input.",
    ),
    name="CreateDeploymentRevisionPresetInput",
)
class CreateDeploymentRevisionPresetInputGQL(PydanticInputMixin[CreateInputDTO]):
    runtime_variant_id: UUID = gql_field(description="Runtime variant ID.")
    name: str = gql_field(description="Preset name.")
    open_to_public: bool | None = gql_field(
        default=None,
        description="Default open_to_public for deployments created from this preset.",
    )
    replica_count: int = gql_field(
        description="Default replica count for deployments created from this preset.",
    )
    revision_history_limit: int | None = gql_field(
        default=None,
        description="Default revision history limit for deployments created from this preset.",
    )
    deployment_strategy: PresetDeploymentStrategyInputGQL = gql_field(
        description="Default deployment strategy for deployments created from this preset.",
    )
    image_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Container image to run the inference server.",
        ),
    )
    description: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Detailed explanation of when and why to use this preset configuration.",
        ),
        default=None,
    )
    model_definition: PresetModelDefinitionInputGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Parsed model definition specifying health checks, ports, and service "
            "configuration for the inference endpoint. Optional, but when provided it must be "
            "fully populated with at least one model.",
        ),
        default=None,
    )
    resource_slots: list[ResourceSlotEntryInputGQL] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Resource slot allocations (e.g. cpu, mem, cuda.device).",
        ),
        default=None,
    )
    resource_opts: list[ResourceOptsEntryInput] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Additional resource options such as shared memory (shmem) size.",
        ),
        default=None,
    )
    cluster_mode: ClusterModeGQL = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Deployment topology mode (single-node or multi-node).",
        ),
    )
    cluster_size: int = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Number of worker nodes in the cluster.",
        ),
    )
    startup_command: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Command to start the inference server process inside the container.",
        ),
        default=None,
    )
    bootstrap_script: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Script executed before the main process starts (e.g. to download model weights).",
        ),
        default=None,
    )
    environ: list[EnvironEntryInputGQL] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Environment variables injected into the inference container.",
        ),
        default=None,
    )
    preset_values: list[RuntimeVariantPresetValueEntryInputGQL] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Runtime variant preset values applied when using this deployment preset.",
        ),
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Update deployment revision preset input.",
    ),
    name="UpdateDeploymentRevisionPresetInput",
)
class UpdateDeploymentRevisionPresetInputGQL(PydanticInputMixin[UpdateInputDTO]):
    id: UUID = gql_field(description="Preset ID.")
    runtime_variant_id: UUID | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="New runtime variant for the preset. Omit to leave unchanged.",
        ),
        default=None,
    )
    name: str | None = gql_field(default=None, description="New name.")
    description: str | None = gql_field(default=None, description="New description.")
    rank: int | None = gql_field(default=None, description="New rank.")
    open_to_public: bool | None = gql_field(
        default=UNSET,
        description="Default open_to_public for deployments created from this preset. "
        "Set to null to clear.",
    )
    replica_count: int | None = gql_field(
        default=UNSET,
        description="Default replica count for deployments created from this preset. "
        "Set to null to clear.",
    )
    revision_history_limit: int | None = gql_field(
        default=UNSET,
        description="Default revision history limit for deployments created from this "
        "preset. Set to null to clear.",
    )
    deployment_strategy: PresetDeploymentStrategyInputGQL | None = gql_field(
        default=UNSET,
        description="Default deployment strategy for deployments created from this "
        "preset. Set to null to clear.",
    )
    image_id: UUID | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Container image for the inference server. Set to null to clear.",
        ),
        default=UNSET,
    )
    model_definition: ModelDefinitionInputGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Parsed model definition. Set to null to clear.",
        ),
        default=UNSET,
    )
    startup_command: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Container startup command. Set to null to clear.",
        ),
        default=UNSET,
    )
    bootstrap_script: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Bootstrap script run before the main process. Set to null to clear.",
        ),
        default=UNSET,
    )
    resource_slots: list[ResourceSlotEntryInputGQL] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Replace resource slot allocations. Omit to leave unchanged.",
        ),
        default=None,
    )
    resource_opts: list[ResourceOptsEntryInput] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Replace additional resource options. Omit to leave unchanged.",
        ),
        default=None,
    )
    cluster_mode: ClusterModeGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="New cluster topology mode. Omit to leave unchanged.",
        ),
        default=None,
    )
    cluster_size: int | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="New cluster size. Omit to leave unchanged.",
        ),
        default=None,
    )
    environ: list[EnvironEntryInputGQL] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Replace environment variables. Omit to leave unchanged.",
        ),
        default=None,
    )
    preset_values: list[RuntimeVariantPresetValueEntryInputGQL] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Replace runtime variant preset values. Omit to leave unchanged.",
        ),
        default=None,
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Create deployment revision preset payload.",
    ),
    model=CreatePayloadDTO,
    name="CreateDeploymentRevisionPresetPayload",
)
class CreateDeploymentRevisionPresetPayloadGQL(PydanticOutputMixin[CreatePayloadDTO]):
    preset: DeploymentRevisionPresetGQL = gql_field(description="The created preset.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Update deployment revision preset payload.",
    ),
    model=UpdatePayloadDTO,
    name="UpdateDeploymentRevisionPresetPayload",
)
class UpdateDeploymentRevisionPresetPayloadGQL(PydanticOutputMixin[UpdatePayloadDTO]):
    preset: DeploymentRevisionPresetGQL = gql_field(description="The updated preset.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Delete deployment revision preset payload.",
    ),
    model=DeletePayloadDTO,
    name="DeleteDeploymentRevisionPresetPayload",
)
class DeleteDeploymentRevisionPresetPayloadGQL(PydanticOutputMixin[DeletePayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted preset.")
