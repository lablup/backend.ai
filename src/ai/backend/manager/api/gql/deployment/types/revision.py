"""GraphQL types for model revisions."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, cast
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.deployment.request import (
    ActivateRevisionInput as ActivateRevisionInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AddRevisionGQLInputDTO,
    CreateRevisionInputDTO,
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
    ResourceSlotEntryInput as ResourceSlotEntryInputDTO,
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
    ModelMountConfigInfoDTO,
    ModelRuntimeConfigInfoDTO,
    ResourceConfigInfoDTO,
)
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
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.image_federation import Image
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.resource_group.federation import ResourceGroup
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.vfolder import VFolder
from ai.backend.manager.api.gql_legacy.image import ImageNode
from ai.backend.manager.api.gql_legacy.scaling_group import ScalingGroupNode
from ai.backend.manager.api.gql_legacy.vfolder import VirtualFolderNode

if TYPE_CHECKING:
    from .deployment import ModelDeployment

MountPermission: type[CommonMountPermission] = strawberry.enum(
    CommonMountPermission,
    name="MountPermission",
    description="Added in 25.19.0. This enum represents the permission level for a mounted volume. It can be ro, rw, wd",
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

    name: str = strawberry.field(
        description="Environment variable name (e.g., CUDA_VISIBLE_DEVICES)."
    )
    value: str = strawberry.field(description="Environment variable value.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0", description="A collection of environment variable entries."
    ),
    model=EnvironmentVariablesInfoDTO,
    name="EnvironmentVariables",
)
class EnvironmentVariablesGQL:
    """A collection of environment variable entries."""

    entries: list[EnvironmentVariableEntryGQL] = strawberry.field(
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
    mode: ClusterModeGQL = strawberry.field(description="The clustering mode (e.g., SINGLE_NODE).")
    size: int = strawberry.field(description="Number of replicas in the cluster.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Compute resource configuration for the deployment. Specifies CPU, memory, GPU allocations and additional resource options.",
    ),
    model=ResourceConfigInfoDTO,
)
class ResourceConfig:
    resource_group_name: str
    resource_slots: ResourceSlotGQL = strawberry.field(
        description="Added in 26.1.0. Allocated compute resources including CPU, memory, and accelerators."
    )
    resource_opts: ResourceOptsGQL | None = strawberry.field(
        description="Added in 26.1.0. Additional resource options such as shared memory.",
        default=None,
    )

    @strawberry.field
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
    runtime_variant: str = strawberry.field(
        description="The inference runtime variant (e.g., vllm, triton)."
    )
    inference_runtime_config: JSON | None = strawberry.field(
        description="Framework-specific configuration in JSON format.",
        default=None,
    )
    environ: EnvironmentVariablesGQL | None = strawberry.field(
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
    mount_destination: str = strawberry.field(
        description="Path inside the container where the model is mounted."
    )
    definition_path: str = strawberry.field(
        description="Path to the model definition file within the mounted folder."
    )

    @strawberry.field
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
    mount_destination: str | None = strawberry.field(
        description="Mount destination path inside the container.",
        default=None,
    )

    @strawberry.field
    async def vfolder(self, info: Info[StrawberryGQLContext]) -> VFolder:
        vfolder_global_id = to_global_id(
            VirtualFolderNode, UUID(str(self.vfolder_id)), is_target_graphene_object=True
        )
        return VFolder(id=ID(vfolder_global_id))


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Represents a versioned configuration snapshot of a model deployment. Each revision captures the complete configuration including cluster settings, resource allocations, runtime configuration, and model mount settings. Revisions enable version control and rollback capabilities for deployments.",
    )
)
class ModelRevision(PydanticNodeMixin[RevisionNodeDTO]):
    image_id: ID
    id: NodeID[str]
    name: str = strawberry.field(description="The name identifier for this revision.")
    cluster_config: ClusterConfig = strawberry.field(
        description="Cluster configuration for replica distribution."
    )
    resource_config: ResourceConfig = strawberry.field(
        description="Compute resource allocation settings."
    )
    model_runtime_config: ModelRuntimeConfig = strawberry.field(
        description="Runtime configuration for the inference framework."
    )
    model_mount_config: ModelMountConfig | None = strawberry.field(
        description="Model data mount configuration."
    )
    extra_mounts: list[ExtraVFolderMountInfoGQL] = strawberry.field(
        description="Additional volume folder mounts."
    )
    created_at: datetime = strawberry.field(description="Timestamp when the revision was created.")

    @strawberry.field
    async def image(self, info: Info[StrawberryGQLContext]) -> Image:
        image_global_id = to_global_id(
            ImageNode, UUID(str(self.image_id)), is_target_graphene_object=True
        )
        return Image(id=ID(image_global_id))

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


@strawberry.enum(
    name="ModelRevisionOrderField",
    description="Added in 25.19.0. Fields available for ordering model revisions.",
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
        description="A single entry representing one resource type and its allocated quantity.",
        added_version="26.1.0",
    ),
)
class ResourceSlotEntryInput(PydanticInputMixin[ResourceSlotEntryInputDTO]):
    """Single resource slot entry input with resource type and quantity."""

    resource_type: str = strawberry.field(
        description="Resource type identifier (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    quantity: str = strawberry.field(description="Quantity of the resource as a decimal string.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="A collection of compute resource allocations for input.",
        added_version="26.1.0",
    ),
)
class ResourceSlotInput(PydanticInputMixin[ResourceSlotInputDTO]):
    """Resource slot input containing multiple resource type entries."""

    entries: list[ResourceSlotEntryInput] = strawberry.field(
        description="List of resource allocations."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ResourceConfigInput(PydanticInputMixin[ResourceConfigInputDTO]):
    resource_group: ResourceGroupInput
    resource_slots: ResourceSlotInput = strawberry.field(
        description="Added in 26.1.0. Resources allocated for the deployment."
    )
    resource_opts: ResourceOptsInput | None = strawberry.field(
        description="Added in 26.1.0. Additional options for the resources such as shared memory.",
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

    name: str = strawberry.field(
        description="Environment variable name (e.g., CUDA_VISIBLE_DEVICES)."
    )
    value: str = strawberry.field(description="Environment variable value.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="A collection of environment variable entries.", added_version="26.1.0"
    ),
    name="EnvironmentVariablesInput",
)
class EnvironmentVariablesInputGQL(PydanticInputMixin[EnvironmentVariablesInputDTO]):
    """A collection of environment variable entries."""

    entries: list[EnvironmentVariableEntryInputGQL] = strawberry.field(
        description="List of environment variable entries."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ModelRuntimeConfigInput(PydanticInputMixin[ModelRuntimeConfigInputDTO]):
    runtime_variant: str
    inference_runtime_config: JSON | None = None
    environ: EnvironmentVariablesInputGQL | None = strawberry.field(
        description="Environment variables for the service.",
        default=None,
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
        description="Input for specifying revision configuration within a deployment.",
        added_version="25.19.0",
    ),
)
class CreateRevisionInput(PydanticInputMixin[CreateRevisionInputDTO]):
    name: str | None = None
    cluster_config: ClusterConfigInput
    resource_config: ResourceConfigInput
    image: ImageInput
    model_runtime_config: ModelRuntimeConfigInput
    model_mount_config: ModelMountConfigInput
    extra_mounts: list[ExtraVFolderMountInput] | None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class AddRevisionInput(PydanticInputMixin[AddRevisionGQLInputDTO]):
    name: str | None = None
    deployment_id: ID
    cluster_config: ClusterConfigInput
    resource_config: ResourceConfigInput
    image: ImageInput
    model_runtime_config: ModelRuntimeConfigInput
    model_mount_config: ModelMountConfigInput
    extra_mounts: list[ExtraVFolderMountInput] | None


ModelRevisionEdge = Edge[ModelRevision]


@gql_connection_type(
    BackendAIGQLMeta(added_version="25.19.0", description="Connection for model revisions.")
)
class ModelRevisionConnection(Connection[ModelRevision]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
