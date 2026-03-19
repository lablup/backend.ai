"""GraphQL types for model revisions."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID, PageInfo
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.deployment.request import (
    ActivateRevisionInput as ActivateRevisionInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AddRevisionInput as AddRevisionInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ExtraVFolderMountInput as ExtraVFolderMountInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RevisionFilter as RevisionFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RevisionInput as RevisionInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RevisionOrder as RevisionOrderDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    RevisionNode as RevisionNodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    OrderDirection as DTOOrderDirection,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    RevisionOrderField as DTORevisionOrderField,
)
from ai.backend.common.types import ClusterMode as CommonClusterMode
from ai.backend.common.types import MountPermission as CommonMountPermission
from ai.backend.common.types import RuntimeVariant
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
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.image_federation import Image
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.resource_group.federation import ResourceGroup
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.vfolder import (
    ExtraVFolderMount,
    ExtraVFolderMountConnection,
    ExtraVFolderMountEdge,
    VFolder,
)
from ai.backend.manager.api.gql_legacy.image import ImageNode
from ai.backend.manager.api.gql_legacy.scaling_group import ScalingGroupNode
from ai.backend.manager.api.gql_legacy.vfolder import VirtualFolderNode
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRevisionOrderField,
    ModelRuntimeConfigData,
    ResourceConfigData,
)

if TYPE_CHECKING:
    from .deployment import ModelDeployment

MountPermission: type[CommonMountPermission] = strawberry.enum(
    CommonMountPermission,
    name="MountPermission",
    description="Added in 25.19.0. This enum represents the permission level for a mounted volume. It can be ro, rw, wd",
)


@strawberry.type(
    name="EnvironmentVariableEntry",
    description="Added in 26.1.0. A single environment variable entry with name and value.",
)
class EnvironmentVariableEntryGQL:
    """A single environment variable entry with name and value."""

    name: str = strawberry.field(
        description="Environment variable name (e.g., CUDA_VISIBLE_DEVICES)."
    )
    value: str = strawberry.field(description="Environment variable value.")


@strawberry.type(
    name="EnvironmentVariables",
    description="Added in 26.1.0. A collection of environment variable entries.",
)
class EnvironmentVariablesGQL:
    """A collection of environment variable entries."""

    entries: list[EnvironmentVariableEntryGQL] = strawberry.field(
        description="List of environment variable entries."
    )


@strawberry.type
class ModelMountConfig:
    """
    Added in 25.19.0.

    Configuration for mounting the model data into the inference container.
    Specifies the virtual folder, mount destination, and model definition path.
    """

    _vfolder_id: strawberry.Private[UUID]
    mount_destination: str = strawberry.field(
        description="Path inside the container where the model is mounted."
    )
    definition_path: str = strawberry.field(
        description="Path to the model definition file within the mounted folder."
    )

    @strawberry.field
    async def vfolder(self, info: Info[StrawberryGQLContext]) -> VFolder:
        vfolder_global_id = to_global_id(
            VirtualFolderNode, self._vfolder_id, is_target_graphene_object=True
        )
        return VFolder(id=ID(vfolder_global_id))

    @classmethod
    def from_dataclass(cls, data: ModelMountConfigData) -> ModelMountConfig | None:
        if data.vfolder_id is None or data.mount_destination is None:
            return None
        return cls(
            _vfolder_id=data.vfolder_id,
            mount_destination=data.mount_destination,
            definition_path=data.definition_path,
        )


@strawberry.type
class ModelRuntimeConfig:
    """
    Added in 25.19.0.

    Runtime configuration for the inference framework.
    Includes the runtime variant, framework-specific configuration,
    and environment variables.
    """

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

    @classmethod
    def from_dataclass(cls, data: ModelRuntimeConfigData) -> ModelRuntimeConfig:
        environ_gql: EnvironmentVariablesGQL | None = None
        if data.environ is not None:
            environ_gql = EnvironmentVariablesGQL(
                entries=[
                    EnvironmentVariableEntryGQL(name=key, value=value)
                    for key, value in data.environ.items()
                ]
            )
        return cls(
            runtime_variant=data.runtime_variant,
            inference_runtime_config=data.inference_runtime_config,
            environ=environ_gql,
        )


@strawberry.type
class ResourceConfig:
    """
    Added in 25.19.0.

    Compute resource configuration for the deployment.
    Specifies CPU, memory, GPU allocations and additional resource options.
    """

    _resource_group_name: strawberry.Private[str]
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
            ScalingGroupNode, self._resource_group_name, is_target_graphene_object=True
        )
        return ResourceGroup(id=ID(global_id))

    @classmethod
    def from_dataclass(cls, data: ResourceConfigData) -> ResourceConfig:
        return cls(
            _resource_group_name=data.resource_group_name,
            resource_slots=ResourceSlotGQL.from_resource_slot(data.resource_slot),
            resource_opts=ResourceOptsGQL.from_mapping(data.resource_opts)
            if data.resource_opts
            else None,
        )


@strawberry.type
class ClusterConfig:
    """
    Added in 25.19.0.

    Cluster configuration for model deployment replicas.
    Defines the clustering mode and number of replicas.
    """

    mode: ClusterModeGQL = strawberry.field(description="The clustering mode (e.g., SINGLE_NODE).")
    size: int = strawberry.field(description="Number of replicas in the cluster.")

    @classmethod
    def from_dataclass(cls, data: ClusterConfigData) -> ClusterConfig:
        return cls(
            mode=ClusterModeGQL(data.mode.name),
            size=data.size,
        )


@strawberry.type
class ModelRevision(PydanticNodeMixin):
    """
    Added in 25.19.0.

    Represents a versioned configuration snapshot of a model deployment.
    Each revision captures the complete configuration including cluster settings,
    resource allocations, runtime configuration, and model mount settings.

    Revisions enable version control and rollback capabilities for deployments.
    """

    _image_id: strawberry.Private[UUID]
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
    extra_mounts: ExtraVFolderMountConnection = strawberry.field(
        description="Additional volume folder mounts."
    )
    created_at: datetime = strawberry.field(description="Timestamp when the revision was created.")

    @strawberry.field
    async def image(self, info: Info[StrawberryGQLContext]) -> Image:
        image_global_id = to_global_id(ImageNode, self._image_id, is_target_graphene_object=True)
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
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_dataclass(cls, data: ModelRevisionData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            cluster_config=ClusterConfig.from_dataclass(data.cluster_config),
            resource_config=ResourceConfig.from_dataclass(data.resource_config),
            model_runtime_config=ModelRuntimeConfig.from_dataclass(data.model_runtime_config),
            model_mount_config=ModelMountConfig.from_dataclass(data.model_mount_config),
            extra_mounts=ExtraVFolderMountConnection.from_dataclass(data.extra_vfolder_mounts),
            _image_id=data.image_id,
            created_at=data.created_at,
        )

    @classmethod
    def from_node(cls, node: RevisionNodeDTO) -> Self:
        info = node.revision_info
        environ_gql: EnvironmentVariablesGQL | None = None
        if info.environ:
            environ_gql = EnvironmentVariablesGQL(
                entries=[
                    EnvironmentVariableEntryGQL(name=k, value=v) for k, v in info.environ.items()
                ]
            )
        model_mount_config: ModelMountConfig | None = None
        if info.model_vfolder_id and info.model_mount_destination:
            model_mount_config = ModelMountConfig(
                _vfolder_id=info.model_vfolder_id,
                mount_destination=info.model_mount_destination,
                definition_path=info.model_definition_path or "",
            )
        extra_mount_nodes = [
            ExtraVFolderMount(
                id=ID(f"{m.vfolder_id}:{m.mount_destination}"),
                mount_destination=m.mount_destination or "",
                _vfolder_id=m.vfolder_id,
            )
            for m in node.extra_mounts
        ]
        extra_mount_edges = [
            ExtraVFolderMountEdge(node=n, cursor=str(n.id)) for n in extra_mount_nodes
        ]
        from strawberry.relay import PageInfo

        extra_mounts = ExtraVFolderMountConnection(
            count=len(extra_mount_nodes),
            edges=extra_mount_edges,
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=extra_mount_edges[0].cursor if extra_mount_edges else None,
                end_cursor=extra_mount_edges[-1].cursor if extra_mount_edges else None,
            ),
        )
        return cls(
            id=ID(str(node.id)),
            name=node.name,
            cluster_config=ClusterConfig(
                mode=ClusterModeGQL(info.cluster_mode.name),
                size=info.cluster_size,
            ),
            resource_config=ResourceConfig(
                _resource_group_name=info.resource_group,
                resource_slots=ResourceSlotGQL.from_resource_slot(info.resource_slots),
                resource_opts=ResourceOptsGQL.from_mapping(info.resource_opts),
            ),
            model_runtime_config=ModelRuntimeConfig(
                runtime_variant=info.runtime_variant,
                inference_runtime_config=info.inference_runtime_config,
                environ=environ_gql,
            ),
            model_mount_config=model_mount_config,
            extra_mounts=extra_mounts,
            _image_id=info.image_id,
            created_at=node.created_at,
        )


# Filter and Order Types
@strawberry.experimental.pydantic.input(
    model=RevisionFilterDTO,
    description="Added in 25.19.0",
)
class ModelRevisionFilter:
    name: StringFilter | None = None
    deployment_id: ID | None = None

    AND: list[ModelRevisionFilter] | None = None
    OR: list[ModelRevisionFilter] | None = None
    NOT: list[ModelRevisionFilter] | None = None

    def to_pydantic(self) -> RevisionFilterDTO:
        return RevisionFilterDTO(
            name=self.name.to_pydantic() if self.name else None,
            deployment_id=UUID(self.deployment_id) if self.deployment_id else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@strawberry.experimental.pydantic.input(
    model=RevisionOrderDTO,
    description="Added in 25.19.0",
)
class ModelRevisionOrderBy:
    field: ModelRevisionOrderField
    direction: OrderDirection = OrderDirection.DESC

    def to_pydantic(self) -> RevisionOrderDTO:
        return RevisionOrderDTO(
            field=DTORevisionOrderField(self.field.value.lower()),
            direction=DTOOrderDirection(self.direction.value.lower()),
        )


# Payload Types
@strawberry.type(description="Added in 25.19.0")
class AddRevisionPayload:
    revision: ModelRevision


@strawberry.experimental.pydantic.input(
    model=ActivateRevisionInputDTO,
    name="ActivateRevisionInput",
    description="Added in 25.19.0. Input for activating a revision to be the current revision.",
)
class ActivateRevisionInputGQL:
    deployment_id: ID
    revision_id: ID


@strawberry.type(
    name="ActivateRevisionPayload",
    description="Added in 25.19.0. Result of activating a revision.",
)
class ActivateRevisionPayloadGQL:
    deployment: Annotated[ModelDeployment, strawberry.lazy(".deployment")]
    previous_revision_id: ID | None
    activated_revision_id: ID


# Input Types
@strawberry.input(description="Added in 25.19.0")
class ClusterConfigInput:
    mode: ClusterModeGQL
    size: int


@strawberry.input(description="Added in 25.19.0")
class ResourceGroupInput:
    name: str


@strawberry.input(
    description=(
        "Added in 26.1.0. A single entry representing one resource type and its allocated quantity."
    )
)
class ResourceSlotEntryInput:
    """Single resource slot entry input with resource type and quantity."""

    resource_type: str = strawberry.field(
        description="Resource type identifier (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    quantity: str = strawberry.field(description="Quantity of the resource as a decimal string.")


@strawberry.input(
    description=("Added in 26.1.0. A collection of compute resource allocations for input.")
)
class ResourceSlotInput:
    """Resource slot input containing multiple resource type entries."""

    entries: list[ResourceSlotEntryInput] = strawberry.field(
        description="List of resource allocations."
    )


@strawberry.input(description="Added in 25.19.0")
class ResourceConfigInput:
    resource_group: ResourceGroupInput
    resource_slots: ResourceSlotInput = strawberry.field(
        description="Added in 26.1.0. Resources allocated for the deployment."
    )
    resource_opts: ResourceOptsInput | None = strawberry.field(
        description="Added in 26.1.0. Additional options for the resources such as shared memory.",
        default=None,
    )


@strawberry.input(description="Added in 25.19.0")
class ImageInput:
    id: ID


@strawberry.input(
    name="EnvironmentVariableEntryInput",
    description="Added in 26.1.0. A single environment variable entry with name and value.",
)
class EnvironmentVariableEntryInputGQL:
    """A single environment variable entry with name and value."""

    name: str = strawberry.field(
        description="Environment variable name (e.g., CUDA_VISIBLE_DEVICES)."
    )
    value: str = strawberry.field(description="Environment variable value.")


@strawberry.input(
    name="EnvironmentVariablesInput",
    description="Added in 26.1.0. A collection of environment variable entries.",
)
class EnvironmentVariablesInputGQL:
    """A collection of environment variable entries."""

    entries: list[EnvironmentVariableEntryInputGQL] = strawberry.field(
        description="List of environment variable entries."
    )


@strawberry.input(description="Added in 25.19.0")
class ModelRuntimeConfigInput:
    runtime_variant: str
    inference_runtime_config: JSON | None = None
    environ: EnvironmentVariablesInputGQL | None = strawberry.field(
        description="Environment variables for the service.",
        default=None,
    )


@strawberry.input(description="Added in 25.19.0")
class ModelMountConfigInput:
    vfolder_id: ID
    mount_destination: str
    definition_path: str


@strawberry.input(description="Added in 25.19.0")
class ExtraVFolderMountInput:
    vfolder_id: ID
    mount_destination: str | None


@strawberry.experimental.pydantic.input(
    model=RevisionInputDTO,
    description="Added in 25.19.0. Input for specifying revision configuration within a deployment.",
)
class CreateRevisionInput:
    name: str | None = None
    cluster_config: ClusterConfigInput
    resource_config: ResourceConfigInput
    image: ImageInput
    model_runtime_config: ModelRuntimeConfigInput
    model_mount_config: ModelMountConfigInput
    extra_mounts: list[ExtraVFolderMountInput] | None

    def to_pydantic(self) -> RevisionInputDTO:
        resource_slots_dict = {
            e.resource_type: e.quantity for e in self.resource_config.resource_slots.entries
        }
        resource_opts_dict: dict[str, str] | None = None
        if self.resource_config.resource_opts is not None:
            resource_opts_dict = {
                e.name: e.value for e in self.resource_config.resource_opts.entries
            }
        environ_dict: dict[str, str] | None = None
        if self.model_runtime_config.environ is not None:
            environ_dict = {e.name: e.value for e in self.model_runtime_config.environ.entries}
        return RevisionInputDTO(
            name=self.name,
            image_id=UUID(str(self.image.id)),
            cluster_mode=CommonClusterMode(self.cluster_config.mode),
            cluster_size=self.cluster_config.size,
            resource_group=self.resource_config.resource_group.name,
            resource_slots=resource_slots_dict,
            resource_opts=resource_opts_dict,
            runtime_variant=RuntimeVariant(self.model_runtime_config.runtime_variant),
            inference_runtime_config=dict(self.model_runtime_config.inference_runtime_config)
            if self.model_runtime_config.inference_runtime_config is not None
            else None,
            model_vfolder_id=UUID(str(self.model_mount_config.vfolder_id)),
            model_mount_destination=self.model_mount_config.mount_destination,
            model_definition_path=self.model_mount_config.definition_path,
            extra_mounts=[
                ExtraVFolderMountInputDTO(
                    vfolder_id=UUID(str(m.vfolder_id)),
                    mount_destination=m.mount_destination,
                )
                for m in self.extra_mounts
            ]
            if self.extra_mounts is not None
            else None,
            environ=environ_dict,
        )


@strawberry.experimental.pydantic.input(
    model=AddRevisionInputDTO,
    description="Added in 25.19.0",
)
class AddRevisionInput:
    name: str | None = None
    deployment_id: ID
    cluster_config: ClusterConfigInput
    resource_config: ResourceConfigInput
    image: ImageInput
    model_runtime_config: ModelRuntimeConfigInput
    model_mount_config: ModelMountConfigInput
    extra_mounts: list[ExtraVFolderMountInput] | None

    def to_pydantic(self) -> AddRevisionInputDTO:
        resource_slots_dict = {
            e.resource_type: e.quantity for e in self.resource_config.resource_slots.entries
        }
        resource_opts_dict: dict[str, str] | None = None
        if self.resource_config.resource_opts is not None:
            resource_opts_dict = {
                e.name: e.value for e in self.resource_config.resource_opts.entries
            }
        environ_dict: dict[str, str] | None = None
        if self.model_runtime_config.environ is not None:
            environ_dict = {e.name: e.value for e in self.model_runtime_config.environ.entries}
        return AddRevisionInputDTO(
            deployment_id=UUID(self.deployment_id),
            revision=RevisionInputDTO(
                name=self.name,
                image_id=UUID(str(self.image.id)),
                cluster_mode=CommonClusterMode(self.cluster_config.mode),
                cluster_size=self.cluster_config.size,
                resource_group=self.resource_config.resource_group.name,
                resource_slots=resource_slots_dict,
                resource_opts=resource_opts_dict,
                runtime_variant=RuntimeVariant(self.model_runtime_config.runtime_variant),
                inference_runtime_config=dict(self.model_runtime_config.inference_runtime_config)
                if self.model_runtime_config.inference_runtime_config is not None
                else None,
                model_vfolder_id=UUID(str(self.model_mount_config.vfolder_id)),
                model_mount_destination=self.model_mount_config.mount_destination,
                model_definition_path=self.model_mount_config.definition_path,
                extra_mounts=[
                    ExtraVFolderMountInputDTO(
                        vfolder_id=UUID(str(m.vfolder_id)),
                        mount_destination=m.mount_destination,
                    )
                    for m in self.extra_mounts
                ]
                if self.extra_mounts is not None
                else None,
                environ=environ_dict,
            ),
        )


ModelRevisionEdge = Edge[ModelRevision]


@strawberry.type(description="Added in 25.19.0")
class ModelRevisionConnection(Connection[ModelRevision]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count

    @classmethod
    def from_dataclass(cls, revisions_data: list[ModelRevisionData]) -> ModelRevisionConnection:
        nodes = [ModelRevision.from_dataclass(data) for data in revisions_data]
        edges = [ModelRevisionEdge(node=node, cursor=str(node.id)) for node in nodes]

        page_info = PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        )

        return cls(count=len(nodes), edges=edges, page_info=page_info)
