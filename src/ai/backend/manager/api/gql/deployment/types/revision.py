"""GraphQL types for model revisions."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, cast
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID, PageInfo
from strawberry.scalars import JSON

from ai.backend.common.config import (
    ModelConfig as ModelConfigDTO,
)
from ai.backend.common.config import (
    ModelDefinition as ModelDefinitionDTO,
)
from ai.backend.common.config import (
    ModelHealthCheck as ModelHealthCheckDTO,
)
from ai.backend.common.config import (
    ModelMetadata as ModelMetadataDTO,
)
from ai.backend.common.config import (
    ModelServiceConfig as ModelServiceConfigDTO,
)
from ai.backend.common.config import (
    PreStartAction as PreStartActionDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ActivateRevisionInput as ActivateRevisionInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AddRevisionGQLInputDTO,
    CreateRevisionInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AddRevisionOptions as AddRevisionOptionsDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ClusterConfigInput as ClusterConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    EnvironmentVariableEntryInput as EnvironmentVariableEntryInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    EnvironmentVariablesInput as EnvironmentVariablesInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ExtraVFolderMountInput as ExtraVFolderMountInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ImageInput as ImageInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelMountConfigInput as ModelMountConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelRuntimeConfigInput as ModelRuntimeConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ResourceConfigInput as ResourceConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ResourceGroupInput as ResourceGroupInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ResourceSlotInput as ResourceSlotInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RevisionFilter as RevisionFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RevisionOrder as RevisionOrderDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    ActivateRevisionPayload as ActivateRevisionPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    AddRevisionPayload as AddRevisionPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    RevisionNode as RevisionNodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    ClusterConfigInfoDTO,
    EnvironmentVariableEntryInfoDTO,
    EnvironmentVariablesInfoDTO,
    ExtraVFolderMountGQLDTO,
    ModelConfigInfoDTO,
    ModelDefinitionInfoDTO,
    ModelHealthCheckInfoDTO,
    ModelMetadataInfoDTO,
    ModelMountConfigInfoDTO,
    ModelRuntimeConfigInfoDTO,
    ModelServiceConfigInfoDTO,
    PreStartActionInfoDTO,
    ResourceConfigInfoDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.common.types import MountPermission as CommonMountPermission
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    StringFilter,
    to_global_id,
)
from ai.backend.manager.api.gql.common.types import (
    ClusterModeGQL,
    ResourceOptsGQL,
    ResourceOptsInput,
)
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
from ai.backend.manager.api.gql.image_federation import Image
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.resource_group.federation import ResourceGroup
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.vfolder import VFolder
from ai.backend.manager.api.gql_legacy.image import ImageNode
from ai.backend.manager.api.gql_legacy.scaling_group import ScalingGroupNode
from ai.backend.manager.api.gql_legacy.vfolder import VirtualFolderNode

from .resource_slot import (
    AllocatedResourceSlotConnection,
    AllocatedResourceSlotEdge,
    AllocatedResourceSlotFilterGQL,
    AllocatedResourceSlotNodeGQL,
    AllocatedResourceSlotOrderByGQL,
)

if TYPE_CHECKING:
    from .deployment import ModelDeployment
    from .policy import DeploymentPolicyGQL

MountPermission: type[CommonMountPermission] = gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="This enum represents the permission level for a mounted volume. It can be ro, rw, wd",
    ),
    CommonMountPermission,
    name="MountPermission",
)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="A single environment variable entry with name and value.",
    ),
    model=EnvironmentVariableEntryInfoDTO,
    name="EnvironmentVariableEntry",
)
class EnvironmentVariableEntryGQL:
    """A single environment variable entry with name and value."""

    name: str = gql_field(description="Environment variable name (e.g., CUDA_VISIBLE_DEVICES).")
    value: str = gql_field(description="Environment variable value.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0", description="A collection of environment variable entries."
    ),
    model=EnvironmentVariablesInfoDTO,
    name="EnvironmentVariables",
)
class EnvironmentVariablesGQL:
    """A collection of environment variable entries."""

    entries: list[EnvironmentVariableEntryGQL] = gql_field(
        description="List of environment variable entries."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Cluster configuration for model deployment replicas. Defines the clustering mode and number of replicas.",
    ),
    model=ClusterConfigInfoDTO,
)
class ClusterConfig:
    mode: ClusterModeGQL = gql_field(description="The clustering mode (e.g., SINGLE_NODE).")
    size: int = gql_field(description="Number of replicas in the cluster.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Compute resource configuration for the deployment. Specifies CPU, memory, GPU allocations and additional resource options.",
    ),
    model=ResourceConfigInfoDTO,
)
class ResourceConfig:
    resource_group_name: str
    resource_opts: ResourceOptsGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.1.0", description="Additional resource options such as shared memory."
        ),
        default=None,
    )

    @gql_field(description="The resource group of this entity.")  # type: ignore[misc]
    def resource_group(self) -> ResourceGroup:
        """Resolves the federated ResourceGroup."""
        global_id = to_global_id(
            ScalingGroupNode, self.resource_group_name, is_target_graphene_object=True
        )
        return ResourceGroup(id=ID(global_id))


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Runtime configuration for the inference framework. Includes the runtime variant, framework-specific configuration, and environment variables.",
    ),
    model=ModelRuntimeConfigInfoDTO,
)
class ModelRuntimeConfig:
    runtime_variant: str = gql_field(
        description="The inference runtime variant (e.g., vllm, triton)."
    )
    inference_runtime_config: JSON | None = gql_field(
        description="Framework-specific configuration in JSON format.", default=None
    )
    environ: EnvironmentVariablesGQL | None = gql_field(
        description="Environment variables for the service, e.g. CUDA_VISIBLE_DEVICES=0.",
        default=None,
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Configuration for mounting the model data into the inference container. Specifies the virtual folder, mount destination, and model definition path.",
    ),
    model=ModelMountConfigInfoDTO,
)
class ModelMountConfig:
    vfolder_id: ID
    mount_destination: str = gql_field(
        description="Path inside the container where the model is mounted."
    )
    definition_path: str = gql_field(
        description="Path to the model definition file within the mounted folder."
    )

    @gql_field(description="The vfolder of this entity.")  # type: ignore[misc]
    async def vfolder(self, info: Info[StrawberryGQLContext]) -> VFolder:
        vfolder_global_id = to_global_id(
            VirtualFolderNode, UUID(str(self.vfolder_id)), is_target_graphene_object=True
        )
        return VFolder(id=ID(vfolder_global_id))


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="An extra virtual folder mount attached to a model revision.",
    ),
    model=ExtraVFolderMountGQLDTO,
)
class ExtraVFolderMountInfoGQL:
    vfolder_id: ID
    mount_destination: str | None = gql_field(
        description="Mount destination path inside the container.", default=None
    )

    @gql_field(description="The vfolder of this entity.")  # type: ignore[misc]
    async def vfolder(self, info: Info[StrawberryGQLContext]) -> VFolder:
        vfolder_global_id = to_global_id(
            VirtualFolderNode, UUID(str(self.vfolder_id)), is_target_graphene_object=True
        )
        return VFolder(id=ID(vfolder_global_id))


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A pre-start action to execute before starting the model service.",
    ),
    model=PreStartActionInfoDTO,
    name="PreStartAction",
)
class PreStartActionGQL:
    action: str = gql_field(description="The name of the pre-start action to execute.")
    args: JSON = gql_field(description="Arguments for the pre-start action.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Health check configuration for a model service.",
    ),
    model=ModelHealthCheckInfoDTO,
    name="ModelHealthCheck",
)
class ModelHealthCheckGQL:
    interval: float = gql_field(description="Interval in seconds between health checks.")
    path: str = gql_field(description="Path to check for health status.")
    max_retries: int = gql_field(description="Maximum number of retries for health check.")
    max_wait_time: float = gql_field(
        description="Maximum time in seconds to wait for a health check response."
    )
    expected_status_code: int = gql_field(
        description="Expected HTTP status code for a healthy response."
    )
    initial_delay: float = gql_field(
        description="Initial delay in seconds before the first health check."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Service configuration for a model entry.",
    ),
    model=ModelServiceConfigInfoDTO,
    name="ModelServiceConfig",
)
class ModelServiceConfigGQL:
    pre_start_actions: list[PreStartActionGQL] = gql_field(
        description="List of pre-start actions to execute before starting the model service."
    )
    start_command: JSON = gql_field(description="Command to start the model service.")
    shell: str = gql_field(description="Shell to use if start_command is a string.")
    port: int = gql_field(description="Port number for the model service.")
    health_check: ModelHealthCheckGQL | None = gql_field(
        description="Health check configuration for the model service.",
        default=None,
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Metadata describing a model entry.",
    ),
    model=ModelMetadataInfoDTO,
    name="ModelMetadata",
)
class ModelMetadataGQL:
    author: str | None = gql_field(description="Author of the model.", default=None)
    title: str | None = gql_field(description="Title of the model.", default=None)
    version: JSON | None = gql_field(description="Version identifier of the model.", default=None)
    created: str | None = gql_field(description="Creation date of the model.", default=None)
    last_modified: str | None = gql_field(
        description="Last modification date of the model.", default=None
    )
    description: str | None = gql_field(description="Description of the model.", default=None)
    task: str | None = gql_field(description="Task type of the model.", default=None)
    category: str | None = gql_field(description="Category of the model.", default=None)
    architecture: str | None = gql_field(
        description="Architecture metadata for the model.", default=None
    )
    framework: list[str] | None = gql_field(
        description="Frameworks used by the model.", default=None
    )
    label: list[str] | None = gql_field(description="Labels attached to the model.", default=None)
    license: str | None = gql_field(description="License of the model.", default=None)
    min_resource: JSON | None = gql_field(
        description="Minimum resource requirements for the model.", default=None
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Configuration for a single model in the model definition.",
    ),
    model=ModelConfigInfoDTO,
    name="ModelConfig",
)
class ModelConfigGQL:
    name: str = gql_field(description="Name of the model.")
    model_path: str = gql_field(description="Path to the model file.")
    service: ModelServiceConfigGQL | None = gql_field(
        description="Configuration for the model service.", default=None
    )
    metadata: ModelMetadataGQL | None = gql_field(
        description="Metadata about the model.", default=None
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Model definition containing one or more model entries.",
    ),
    model=ModelDefinitionInfoDTO,
    name="ModelDefinition",
)
class ModelDefinitionGQL:
    models: list[ModelConfigGQL] = gql_field(description="List of models in the model definition.")


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Represents a versioned configuration snapshot of a model deployment. Each revision captures the complete configuration including cluster settings, resource allocations, runtime configuration, and model mount settings. Revisions enable version control and rollback capabilities for deployments.",
    )
)
class ModelRevision(PydanticNodeMixin[RevisionNodeDTO]):
    image_id: ID
    id: NodeID[str]
    name: str = gql_field(description="The name identifier for this revision.")
    cluster_config: ClusterConfig = gql_field(
        description="Cluster configuration for replica distribution."
    )
    resource_config: ResourceConfig = gql_field(description="Compute resource allocation settings.")
    model_runtime_config: ModelRuntimeConfig = gql_field(
        description="Runtime configuration for the inference framework."
    )
    model_mount_config: ModelMountConfig | None = gql_field(
        description="Model data mount configuration."
    )
    model_definition: ModelDefinitionGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Resolved model definition stored for this revision.",
        ),
        default=None,
    )
    extra_mounts: list[ExtraVFolderMountInfoGQL] = gql_field(
        description="Additional volume folder mounts."
    )
    created_at: datetime = gql_field(description="Timestamp when the revision was created.")

    @gql_field(description="The image of this entity.")  # type: ignore[misc]
    async def image(self, info: Info[StrawberryGQLContext]) -> Image:
        image_global_id = to_global_id(
            ImageNode, UUID(str(self.image_id)), is_target_graphene_object=True
        )
        return Image(id=ID(image_global_id))

    @gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Resource slot allocations for this revision.",
        )
    )  # type: ignore[misc]
    async def resource_slots(
        self,
        info: Info[StrawberryGQLContext],
        filter: AllocatedResourceSlotFilterGQL | None = None,
        order_by: list[AllocatedResourceSlotOrderByGQL] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AllocatedResourceSlotConnection:
        from ai.backend.common.dto.manager.v2.resource_slot.request import (
            SearchAllocatedResourceSlotsInput,
        )

        pydantic_filter = filter.to_pydantic() if filter else None
        pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
        payload = await info.context.adapters.deployment.search_revision_resource_slots(
            revision_id=UUID(str(self.id)),
            input=SearchAllocatedResourceSlotsInput(
                filter=pydantic_filter,
                order=pydantic_order,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        nodes = [AllocatedResourceSlotNodeGQL.from_pydantic(item) for item in payload.items]
        edges = [AllocatedResourceSlotEdge(node=node, cursor=node.slot_name) for node in nodes]
        return AllocatedResourceSlotConnection(
            count=payload.total_count,
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
        )

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.revision_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


@gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Fields available for ordering model revisions."
    ),
    name="ModelRevisionOrderField",
)
class ModelRevisionOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"


# Filter and Order Types
@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
    name="ModelRevisionFilter",
)
class ModelRevisionFilter(PydanticInputMixin[RevisionFilterDTO]):
    name: StringFilter | None = None
    deployment_id: ID | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ModelRevisionOrderBy(PydanticInputMixin[RevisionOrderDTO]):
    field: ModelRevisionOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC


# Payload Types
@gql_pydantic_type(
    BackendAIGQLMeta(added_version="25.19.0", description="Payload for adding a revision."),
    model=AddRevisionPayloadDTO,
)
class AddRevisionPayload:
    revision: ModelRevision


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for activating a revision to be the current revision.",
        added_version="25.19.0",
    ),
    name="ActivateRevisionInput",
)
class ActivateRevisionInputGQL(PydanticInputMixin[ActivateRevisionInputDTO]):
    deployment_id: ID
    revision_id: ID


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="25.19.0", description="Result of activating a revision."),
    model=ActivateRevisionPayloadDTO,
    name="ActivateRevisionPayload",
)
class ActivateRevisionPayloadGQL:
    deployment: Annotated[ModelDeployment, strawberry.lazy(".deployment")]
    previous_revision_id: ID | None
    activated_revision_id: ID
    deployment_policy: Annotated[DeploymentPolicyGQL, strawberry.lazy(".policy")]


# Input Types
@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ClusterConfigInput(PydanticInputMixin[ClusterConfigInputDTO]):
    mode: ClusterModeGQL
    size: int


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ResourceGroupInput(PydanticInputMixin[ResourceGroupInputDTO]):
    name: str


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="A collection of compute resource allocations for input.",
        added_version="26.1.0",
    ),
)
class ResourceSlotInput(PydanticInputMixin[ResourceSlotInputDTO]):
    """Resource slot input containing multiple resource type entries."""

    entries: list[ResourceSlotEntryInputGQL] = gql_field(
        description="List of resource allocations."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ResourceConfigInput(PydanticInputMixin[ResourceConfigInputDTO]):
    resource_group: ResourceGroupInput
    resource_slots: ResourceSlotInput = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.1.0", description="Resources allocated for the deployment."
        )
    )
    resource_opts: ResourceOptsInput | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.1.0",
            description="Additional options for the resources such as shared memory.",
        ),
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ImageInput(PydanticInputMixin[ImageInputDTO]):
    id: ID


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="A single environment variable entry with name and value.",
        added_version="26.1.0",
    ),
    name="EnvironmentVariableEntryInput",
)
class EnvironmentVariableEntryInputGQL(PydanticInputMixin[EnvironmentVariableEntryInputDTO]):
    """A single environment variable entry with name and value."""

    name: str = gql_field(description="Environment variable name (e.g., CUDA_VISIBLE_DEVICES).")
    value: str = gql_field(description="Environment variable value.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="A collection of environment variable entries.", added_version="26.1.0"
    ),
    name="EnvironmentVariablesInput",
)
class EnvironmentVariablesInputGQL(PydanticInputMixin[EnvironmentVariablesInputDTO]):
    """A collection of environment variable entries."""

    entries: list[EnvironmentVariableEntryInputGQL] = gql_field(
        description="List of environment variable entries."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ModelRuntimeConfigInput(PydanticInputMixin[ModelRuntimeConfigInputDTO]):
    runtime_variant: str
    inference_runtime_config: JSON | None = None
    environ: EnvironmentVariablesInputGQL | None = gql_field(
        description="Environment variables for the service.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ModelMountConfigInput(PydanticInputMixin[ModelMountConfigInputDTO]):
    vfolder_id: ID
    mount_destination: str
    definition_path: str


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ExtraVFolderMountInput(PydanticInputMixin[ExtraVFolderMountInputDTO]):
    vfolder_id: ID
    mount_destination: str | None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for a pre-start action to execute before starting the model service.",
        added_version="26.4.0",
    ),
    name="PreStartActionInput",
)
class PreStartActionInputGQL(PydanticInputMixin[PreStartActionDTO]):
    action: str = gql_field(description="The name of the pre-start action to execute.")
    args: JSON = gql_field(
        description="Arguments for the pre-start action.", default=strawberry.UNSET
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Health check configuration for a model service.",
        added_version="26.4.0",
    ),
    name="ModelHealthCheckInput",
)
class ModelHealthCheckInputGQL(PydanticInputMixin[ModelHealthCheckDTO]):
    interval: float = gql_field(
        description="Interval in seconds between health checks.", default=10.0
    )
    path: str = gql_field(description="Path to check for health status.")
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
        description="Initial delay in seconds before the first health check.", default=60.0
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Service configuration for a model, including startup command and health check.",
        added_version="26.4.0",
    ),
    name="ModelServiceConfigInput",
)
class ModelServiceConfigInputGQL(PydanticInputMixin[ModelServiceConfigDTO]):
    pre_start_actions: list[PreStartActionInputGQL] = gql_field(
        description="List of pre-start actions to execute before starting the model service.",
        default=strawberry.UNSET,
    )
    start_command: JSON = gql_field(description="Command to start the model service.")
    shell: str = gql_field(
        description="Shell to use if start_command is a string.", default="/bin/bash"
    )
    port: int = gql_field(description="Port number for the model service. Must be greater than 1.")
    health_check: ModelHealthCheckInputGQL | None = gql_field(
        description="Health check configuration for the model service.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Metadata about a model such as author, title, and resource requirements.",
        added_version="26.4.0",
    ),
    name="ModelMetadataInput",
)
class ModelMetadataInputGQL(PydanticInputMixin[ModelMetadataDTO]):
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
        description="Configuration for a single model within a model definition.",
        added_version="26.4.0",
    ),
    name="ModelConfigInput",
)
class ModelConfigInputGQL(PydanticInputMixin[ModelConfigDTO]):
    name: str = gql_field(description="Name of the model.")
    model_path: str = gql_field(description="Path to the model file.")
    service: ModelServiceConfigInputGQL | None = gql_field(
        description="Configuration for the model service.", default=None
    )
    metadata: ModelMetadataInputGQL | None = gql_field(
        description="Metadata about the model.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Model definition containing a list of model configurations.",
        added_version="26.4.0",
    ),
    name="ModelDefinitionInput",
)
class ModelDefinitionInputGQL(PydanticInputMixin[ModelDefinitionDTO]):
    models: list[ModelConfigInputGQL] = gql_field(
        description="List of models in the model definition."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for specifying revision configuration within a deployment.",
        added_version="25.19.0",
    ),
)
class CreateRevisionInput(PydanticInputMixin[CreateRevisionInputDTO]):
    name: str | None = None
    revision_preset_id: UUID | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="DeploymentRevisionPreset ID. When specified, preset values are used as defaults and can be overridden by explicitly provided fields.",
        ),
        default=None,
    )
    cluster_config: ClusterConfigInput
    resource_config: ResourceConfigInput
    image: ImageInput
    model_runtime_config: ModelRuntimeConfigInput
    model_mount_config: ModelMountConfigInput
    model_definition: ModelDefinitionInputGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Model definition to override the default values generated by the server",
        ),
        default=None,
    )
    extra_mounts: list[ExtraVFolderMountInput] | None = gql_field(
        description="Extra vfolder mounts",
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Options for the add_model_revision mutation.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AddRevisionOptions",
)
class AddRevisionOptionsGQL(PydanticInputMixin[AddRevisionOptionsDTO]):
    auto_activate: bool = gql_field(
        default=False,
        description="When true, automatically activate the newly added revision immediately after creation.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class AddRevisionInput(PydanticInputMixin[AddRevisionGQLInputDTO]):
    name: str | None = None
    revision_preset_id: UUID | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="DeploymentRevisionPreset ID. When specified, preset values are used as defaults and can be overridden by explicitly provided fields.",
        ),
        default=None,
    )
    deployment_id: ID
    cluster_config: ClusterConfigInput
    resource_config: ResourceConfigInput
    image: ImageInput
    model_runtime_config: ModelRuntimeConfigInput
    model_mount_config: ModelMountConfigInput
    model_definition: ModelDefinitionInputGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Model definition to override the default values generated by the server",
        ),
        default=None,
    )
    extra_mounts: list[ExtraVFolderMountInput] | None = gql_field(
        description="Extra vfolder mounts",
        default=None,
    )


ModelRevisionEdge = Edge[ModelRevision]


@gql_connection_type(
    BackendAIGQLMeta(added_version="25.19.0", description="Connection for model revisions.")
)
class ModelRevisionConnection(Connection[ModelRevision]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
