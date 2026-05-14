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

from ai.backend.common.config import (
    PreStartAction as PreStartActionDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ActivateRevisionInput as ActivateRevisionInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AddRevisionInput as AddRevisionInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AddRevisionOptions as AddRevisionOptionsDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ClusterConfigInput as ClusterConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    CreateRevisionInput as CreateRevisionInputDTO,
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
    ModelConfigInput as ModelConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelDefinitionInput as ModelDefinitionInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelHealthCheckInput as ModelHealthCheckInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelMetadataInput as ModelMetadataInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelMountConfigInput as ModelMountConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelRuntimeConfigInput as ModelRuntimeConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelServiceConfigInput as ModelServiceConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ResourceConfigInput as ResourceConfigInputDTO,
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
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.meta import NEXT_RELEASE_VERSION
from ai.backend.common.types import MountPermission as CommonMountPermission
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    IntFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
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
    RESOURCE_SLOTS_FETCH_LIMIT,
    AllocatedResourceSlotFilterGQL,
    AllocatedResourceSlotGQL,
    AllocatedResourceSlotOrderByGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.image.types import ImageV2GQL
    from ai.backend.manager.api.gql.runtime_variant.types import RuntimeVariantGQL

    from .deployment import ModelDeployment
    from .policy import DeploymentPolicyGQL
    from .revision_preset import DeploymentRevisionPresetGQL

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
    def resource_group(self) -> ResourceGroup | None:
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
    runtime_variant_id: UUID = gql_field(
        description="The runtime variant row id. Clients can resolve the full variant node via the ``runtime_variant`` field resolver."
    )
    inference_runtime_config: JSON | None = gql_field(
        description="Framework-specific configuration in JSON format.", default=None
    )
    environ: EnvironmentVariablesGQL | None = gql_field(
        description="Environment variables for the service, e.g. CUDA_VISIBLE_DEVICES=0.",
        default=None,
    )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="The runtime variant referenced by this runtime config.",
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
    subpath: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Subpath within the model vfolder. ``null`` means the vfolder root.",
        ),
        default=None,
    )

    @gql_field(description="The vfolder of this entity.")  # type: ignore[misc]
    async def vfolder(self, info: Info[StrawberryGQLContext]) -> VFolder | None:
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
    mount_perm: MountPermission = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "The concrete permission snapshot fixed at revision-write time; "
                "later vfolder permission changes do not retroactively affect it."
            ),
        ),
    )
    subpath: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Subpath within the vfolder. ``null`` means the vfolder root.",
        ),
        default=None,
    )

    @gql_field(description="The vfolder of this entity.")  # type: ignore[misc]
    async def vfolder(self, info: Info[StrawberryGQLContext]) -> VFolder | None:
        vfolder_global_id = to_global_id(
            VirtualFolderNode, UUID(str(self.vfolder_id)), is_target_graphene_object=True
        )
        return VFolder(id=ID(vfolder_global_id))


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.2",
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
        added_version="26.4.2",
        description="Service configuration for a model entry.",
    ),
    model=ModelServiceConfigInfoDTO,
    name="ModelServiceConfig",
)
class ModelServiceConfigGQL:
    pre_start_actions: list[PreStartActionGQL] = gql_field(
        description="List of pre-start actions to execute before starting the model service."
    )
    start_command: JSON | None = gql_field(
        description=(
            "Command to start the model service. A JSON array (``list[str]``) "
            "is exec'ed directly as argv; a JSON string is wrapped as "
            "``[shell, '-c', str]`` by the kernel runner so shell semantics "
            "(line continuations, ``$VAR`` expansion, pipes) apply."
        ),
        default=None,
    )
    shell: str = gql_field(description="Shell configured for the model service.")
    port: int = gql_field(description="Port number for the model service.")
    health_check: ModelHealthCheckGQL | None = gql_field(
        description="Health check configuration for the model service.",
        default=None,
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.2",
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
        added_version="26.4.2",
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
    revision_number: int = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "Per-deployment sequential revision number assigned at "
                "insert time (UNIQUE per deployment). Use this to surface "
                "'Revision #N' labels and to order revisions client-side."
            ),
        ),
    )
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
            added_version="26.4.2",
            description="Resolved model definition stored for this revision.",
        ),
        default=None,
    )
    extra_mounts: list[ExtraVFolderMountInfoGQL] = gql_field(
        description="Additional volume folder mounts."
    )
    revision_preset_id: UUID | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "ID of the deployment-level preset that produced this "
                "revision. ``None`` when the revision was created without a "
                "preset, when the originating preset row has since been "
                "deleted (SET NULL FK), or for legacy rows that predate "
                "this field."
            ),
        ),
        default=None,
    )
    deployment_id: ID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "ID of the parent deployment that owns this revision. "
                "Exposed alongside the resolved ``deployment`` node so "
                "clients can navigate without re-fetching."
            ),
        ),
    )
    created_at: datetime = gql_field(description="Timestamp when the revision was created.")

    @gql_field(
        description="The image of this entity.",
        deprecation_reason="Use image_v2 instead.",
    )  # type: ignore[misc]
    async def image(self, info: Info[StrawberryGQLContext]) -> Image | None:
        image_global_id = to_global_id(
            ImageNode, UUID(str(self.image_id)), is_target_graphene_object=True
        )
        return Image(id=ID(image_global_id))

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3",
            description="The container image used by this revision, resolved via DataLoader.",
        )
    )  # type: ignore[misc]
    async def image_v2(
        self, info: Info[StrawberryGQLContext]
    ) -> (
        Annotated[
            ImageV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.image.types"),
        ]
        | None
    ):
        from ai.backend.common.types import ImageID

        return await info.context.data_loaders.image_loader.load(ImageID(UUID(str(self.image_id))))

    @gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "The deployment-level preset that produced this revision, "
                "resolved via DataLoader. ``None`` when the revision was "
                "created without a preset, when the originating preset row "
                "has since been deleted (SET NULL FK), or for legacy rows "
                "that predate this field."
            ),
        )
    )  # type: ignore[misc]
    async def revision_preset(
        self, info: Info[StrawberryGQLContext]
    ) -> (
        Annotated[
            DeploymentRevisionPresetGQL,
            strawberry.lazy("ai.backend.manager.api.gql.deployment.types.revision_preset"),
        ]
        | None
    ):
        if self.revision_preset_id is None:
            return None
        return await info.context.data_loaders.revision_preset_loader.load(self.revision_preset_id)

    @gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="The parent deployment owning this revision, resolved via DataLoader.",
        )
    )  # type: ignore[misc]
    async def deployment(
        self, info: Info[StrawberryGQLContext]
    ) -> Annotated[ModelDeployment, strawberry.lazy(".deployment")] | None:
        return await info.context.data_loaders.deployment_loader.load(UUID(str(self.deployment_id)))

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.2",
            description="Resource slot allocations for this revision.",
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

        payload = await info.context.adapters.deployment.search_revision_resource_slots(
            revision_id=DeploymentRevisionID(UUID(str(self.id))),
            input=SearchAllocatedResourceSlotsInput(
                filter=filter.to_pydantic() if filter else None,
                order=[o.to_pydantic() for o in order_by] if order_by else None,
                limit=RESOURCE_SLOTS_FETCH_LIMIT,
            ),
        )
        return [AllocatedResourceSlotGQL.from_pydantic(item) for item in payload.items]

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
    REVISION_NUMBER = "revision_number"
    CREATED_AT = "created_at"
    RESOURCE_GROUP = "resource_group"
    CLUSTER_MODE = "cluster_mode"
    RUNTIME_VARIANT_NAME = "runtime_variant_name"


# Filter and Order Types
@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
    name="ModelRevisionFilter",
)
class ModelRevisionFilter(PydanticInputMixin[RevisionFilterDTO]):
    revision_number: IntFilter | None = None
    deployment_id: ID | None = None
    image_id: UUIDFilter | None = gql_added_field(
        BackendAIGQLMeta(added_version="26.4.3", description="Filter by container image ID."),
        default=None,
    )
    model_vfolder_id: UUIDFilter | None = gql_added_field(
        BackendAIGQLMeta(added_version="26.4.3", description="Filter by model VFolder ID."),
        default=None,
    )
    resource_group: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(added_version="26.4.3", description="Filter by resource group name."),
        default=None,
    )
    cluster_mode: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3",
            description="Filter by cluster mode (SINGLE_NODE / MULTI_NODE).",
        ),
        default=None,
    )
    created_at: DateTimeFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3", description="Filter by revision creation datetime."
        ),
        default=None,
    )

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
    runtime_variant_id: UUID
    environ: EnvironmentVariablesInputGQL | None = gql_field(
        description="Environment variables for the service.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ModelMountConfigInput(PydanticInputMixin[ModelMountConfigInputDTO]):
    vfolder_id: ID
    mount_destination: str
    definition_path: str | None = None
    subpath: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "Subpath within the model vfolder. ``null`` (default) mounts the vfolder root."
            ),
        ),
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class ExtraVFolderMountInput(PydanticInputMixin[ExtraVFolderMountInputDTO]):
    vfolder_id: ID
    mount_destination: str | None
    subpath: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=("Subpath within the vfolder. ``null`` (default) mounts the vfolder root."),
        ),
        default=None,
    )


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
class ModelHealthCheckInputGQL(PydanticInputMixin[ModelHealthCheckInputDTO]):
    interval: float | None = gql_field(
        description="Interval in seconds between health checks.", default=None
    )
    path: str | None = gql_field(description="Path to check for health status.", default=None)
    max_retries: int | None = gql_field(
        description="Maximum number of retries for health check.", default=None
    )
    max_wait_time: float | None = gql_field(
        description="Maximum time in seconds to wait for a health check response.", default=None
    )
    expected_status_code: int | None = gql_field(
        description="Expected HTTP status code for a healthy response.", default=None
    )
    initial_delay: float | None = gql_field(
        description="Initial delay in seconds before the first health check.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Service configuration for a model, including startup command and health check.",
        added_version="26.4.0",
    ),
    name="ModelServiceConfigInput",
)
class ModelServiceConfigInputGQL(PydanticInputMixin[ModelServiceConfigInputDTO]):
    pre_start_actions: list[PreStartActionInputGQL] | None = gql_field(
        description="List of pre-start actions to execute before starting the model service.",
        default=None,
    )
    start_command: JSON | None = gql_field(
        description=(
            "Command to start the model service. A JSON array (``list[str]``) "
            "is exec'ed directly as argv; a JSON string is wrapped as "
            "``[shell, '-c', str]`` by the kernel runner so shell semantics "
            "(line continuations, ``$VAR`` expansion, pipes) apply."
        ),
        default=None,
    )
    shell: str | None = gql_field(
        description="Shell configured for the model service.", default=None
    )
    port: int | None = gql_field(description="Port number for the model service.", default=None)
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
class ModelMetadataInputGQL(PydanticInputMixin[ModelMetadataInputDTO]):
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
class ModelConfigInputGQL(PydanticInputMixin[ModelConfigInputDTO]):
    name: str | None = gql_field(description="Name of the model.", default=None)
    model_path: str | None = gql_field(description="Path to the model file.", default=None)
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
class ModelDefinitionInputGQL(PydanticInputMixin[ModelDefinitionInputDTO]):
    models: list[ModelConfigInputGQL] | None = gql_field(
        description="List of models in the model definition.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for specifying revision configuration within a deployment.",
        added_version="25.19.0",
    ),
)
class CreateRevisionInput(PydanticInputMixin[CreateRevisionInputDTO]):
    revision_preset_id: UUID | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.2",
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
            added_version="26.4.2",
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
        added_version="26.4.2",
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
class AddRevisionInput(PydanticInputMixin[AddRevisionInputDTO]):
    revision_preset_id: UUID | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.2",
            description="DeploymentRevisionPreset ID. When specified, preset values are used as defaults and can be overridden by explicitly provided fields.",
        ),
        default=None,
    )
    deployment_id: ID
    cluster_config: ClusterConfigInput | None = gql_field(
        description="Cluster configuration",
        default=None,
    )
    resource_config: ResourceConfigInput | None = gql_field(
        description="Resource configuration",
        default=None,
    )
    image: ImageInput | None = gql_field(
        description="Container image",
        default=None,
    )
    model_runtime_config: ModelRuntimeConfigInput | None = gql_field(
        description="Runtime configuration",
        default=None,
    )
    model_mount_config: ModelMountConfigInput = gql_field(
        description="Model mount configuration",
    )
    model_definition: ModelDefinitionInputGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.2",
            description="Model definition to override the default values generated by the server",
        ),
        default=None,
    )
    extra_mounts: list[ExtraVFolderMountInput] | None = gql_field(
        description="Extra vfolder mounts",
        default=None,
    )
    options: AddRevisionOptionsGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Additional options for the add revision operation.",
        ),
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
