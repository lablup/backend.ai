"""GraphQL types for model revisions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Annotated, Any, Optional, cast, override
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo
from strawberry.scalars import JSON

from ai.backend.common.types import ClusterMode as CommonClusterMode
from ai.backend.common.types import MountPermission as CommonMountPermission
from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.api.gql.base import (
    JSONString,
    OrderDirection,
    StringFilter,
    to_global_id,
)
from ai.backend.manager.api.gql.image import Image
from ai.backend.manager.api.gql.resource_group import ResourceGroup
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.vfolder import ExtraVFolderMountConnection, VFolder
from ai.backend.manager.data.deployment.creator import ModelRevisionCreator, VFolderMountsCreator
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    ExecutionSpec,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRevisionOrderField,
    ModelRuntimeConfigData,
    MountInfo,
    ResourceConfigData,
    ResourceSpec,
)
from ai.backend.manager.models.gql_models.image import ImageNode
from ai.backend.manager.models.gql_models.scaling_group import ScalingGroupNode
from ai.backend.manager.models.gql_models.vfolder import VirtualFolderNode
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.deployment.options import RevisionConditions, RevisionOrders

if TYPE_CHECKING:
    from .deployment import ModelDeployment

MountPermission: type[CommonMountPermission] = strawberry.enum(
    CommonMountPermission,
    name="MountPermission",
    description="Added in 25.19.0. This enum represents the permission level for a mounted volume. It can be ro, rw, wd",
)


@strawberry.enum(description="Added in 25.19.0")
class ClusterMode(StrEnum):
    SINGLE_NODE = "SINGLE_NODE"
    MULTI_NODE = "MULTI_NODE"


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
    def from_dataclass(cls, data: ModelMountConfigData) -> ModelMountConfig:
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
    inference_runtime_config: Optional[JSON] = strawberry.field(
        description="Framework-specific configuration in JSON format.",
        default=None,
    )
    environ: Optional[JSONString] = strawberry.field(
        description='Environment variables for the service, e.g. {"CUDA_VISIBLE_DEVICES": "0"}.',
        default=None,
    )

    @classmethod
    def from_dataclass(cls, data: ModelRuntimeConfigData) -> ModelRuntimeConfig:
        return cls(
            runtime_variant=data.runtime_variant,
            inference_runtime_config=data.inference_runtime_config,
            environ=JSONString.serialize(data.environ) if data.environ else None,
        )


@strawberry.type
class ResourceConfig:
    """
    Added in 25.19.0.

    Compute resource configuration for the deployment.
    Specifies CPU, memory, GPU allocations and additional resource options.
    """

    _resource_group_name: strawberry.Private[str]
    resource_slots: JSONString = strawberry.field(
        description='JSON describing allocated resources. Example: {"cpu": "1", "mem": "1073741824", "cuda.device": "0"}.'
    )
    resource_opts: Optional[JSONString] = strawberry.field(
        description='Additional resource options such as shared memory. Example: {"shmem": "64m"}.',
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
            resource_slots=JSONString.from_resource_slot(data.resource_slot),
            resource_opts=JSONString.serialize(data.resource_opts),
        )


@strawberry.type
class ClusterConfig:
    """
    Added in 25.19.0.

    Cluster configuration for model deployment replicas.
    Defines the clustering mode and number of replicas.
    """

    mode: ClusterMode = strawberry.field(description="The clustering mode (e.g., SINGLE_NODE).")
    size: int = strawberry.field(description="Number of replicas in the cluster.")

    @classmethod
    def from_dataclass(cls, data: ClusterConfigData) -> ClusterConfig:
        return cls(
            mode=ClusterMode(data.mode.name),
            size=data.size,
        )


@strawberry.type
class ModelRevision(Node):
    """
    Added in 25.19.0.

    Represents a versioned configuration snapshot of a model deployment.
    Each revision captures the complete configuration including cluster settings,
    resource allocations, runtime configuration, and model mount settings.

    Revisions enable version control and rollback capabilities for deployments.
    """

    _image_id: strawberry.Private[UUID]
    id: NodeID
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
    model_mount_config: ModelMountConfig = strawberry.field(
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
    def from_dataclass(cls, data: ModelRevisionData) -> ModelRevision:
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


# Filter and Order Types
@strawberry.input(description="Added in 25.19.0")
class ModelRevisionFilter(GQLFilter):
    name: Optional[StringFilter] = None
    deployment_id: Optional[ID] = None
    ids_in: strawberry.Private[Optional[Sequence[UUID]]] = None

    AND: Optional[list[ModelRevisionFilter]] = None
    OR: Optional[list[ModelRevisionFilter]] = None
    NOT: Optional[list[ModelRevisionFilter]] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter.

        Returns a list of QueryCondition callables that can be applied to SQLAlchemy queries.
        """
        field_conditions: list[QueryCondition] = []

        # Apply name filter
        if self.name:
            name_condition = self.name.build_query_condition(
                contains_factory=RevisionConditions.by_name_contains,
                equals_factory=RevisionConditions.by_name_equals,
            )
            if name_condition:
                field_conditions.append(name_condition)

        # Apply deployment_id filter
        if self.deployment_id:
            field_conditions.append(RevisionConditions.by_deployment_id(UUID(self.deployment_id)))

        # Apply ids_in filter
        if self.ids_in:
            field_conditions.append(RevisionConditions.by_ids(self.ids_in))

        # Handle AND logical operator - these are implicitly ANDed with field conditions
        if self.AND:
            for sub_filter in self.AND:
                field_conditions.extend(sub_filter.build_conditions())

        # Handle OR logical operator
        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                field_conditions.append(combine_conditions_or(or_sub_conditions))

        # Handle NOT logical operator
        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                field_conditions.append(negate_conditions(not_sub_conditions))

        return field_conditions


@strawberry.input(description="Added in 25.19.0")
class ModelRevisionOrderBy(GQLOrderBy):
    field: ModelRevisionOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ModelRevisionOrderField.NAME:
                return RevisionOrders.name(ascending)
            case ModelRevisionOrderField.CREATED_AT:
                return RevisionOrders.created_at(ascending)


# Payload Types
@strawberry.type(description="Added in 25.19.0")
class AddRevisionPayload:
    revision: ModelRevision


@strawberry.type(description="Added in 25.16.0")
class CreateRevisionPayload:
    revision: ModelRevision


@strawberry.input(
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
    deployment: Annotated["ModelDeployment", strawberry.lazy(".deployment")]
    previous_revision_id: Optional[ID]
    activated_revision_id: ID


# Input Types
@strawberry.input(description="Added in 25.19.0")
class ClusterConfigInput:
    mode: ClusterMode
    size: int


@strawberry.input(description="Added in 25.19.0")
class ResourceGroupInput:
    name: str


@strawberry.input(description="Added in 25.19.0")
class ResourceConfigInput:
    resource_group: ResourceGroupInput
    resource_slots: JSONString = strawberry.field(
        description='Resources allocated for the deployment. Example: "resourceSlots": "{\\"cpu\\": \\"1\\", \\"mem\\": \\"1073741824\\", \\"cuda.device\\": \\"0\\"}"'
    )
    resource_opts: Optional[JSONString] = strawberry.field(
        description='Additional options for the resources. This is especially used for shared memory configurations. Example: "resourceOpts": "{\\"shmem\\": \\"64m\\"}"',
        default=None,
    )


@strawberry.input(description="Added in 25.19.0")
class ImageInput:
    id: ID


@strawberry.input(description="Added in 25.19.0")
class ModelRuntimeConfigInput:
    runtime_variant: str
    inference_runtime_config: Optional[JSON] = None
    environ: Optional[JSONString] = strawberry.field(
        description='Environment variables for the service, e.g. {"CUDA_VISIBLE_DEVICES": "0"}',
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
    mount_destination: Optional[str]


@strawberry.input(
    description="Added in 25.19.0. Input for creating a revision without attaching to a deployment."
)
class CreateRevisionInput:
    name: Optional[str] = None
    cluster_config: ClusterConfigInput
    resource_config: ResourceConfigInput
    image: ImageInput
    model_runtime_config: ModelRuntimeConfigInput
    model_mount_config: ModelMountConfigInput
    extra_mounts: Optional[list[ExtraVFolderMountInput]]

    def to_model_revision_creator(self) -> ModelRevisionCreator:
        resource_spec = ResourceSpec(
            cluster_mode=CommonClusterMode(self.cluster_config.mode),
            cluster_size=self.cluster_config.size,
            resource_slots=cast(Mapping[str, Any], self.resource_config.resource_slots),
            resource_opts=cast(Mapping[str, Any] | None, self.resource_config.resource_opts),
        )

        extra_mounts = []
        if self.extra_mounts is not None:
            extra_mounts = [
                MountInfo(
                    vfolder_id=UUID(str(extra_mount.vfolder_id)),
                    kernel_path=PurePosixPath(
                        extra_mount.mount_destination
                        if extra_mount.mount_destination is not None
                        else ""
                    ),
                )
                for extra_mount in self.extra_mounts
            ]

        mounts = VFolderMountsCreator(
            model_vfolder_id=UUID(str(self.model_mount_config.vfolder_id)),
            model_definition_path=self.model_mount_config.definition_path,
            model_mount_destination=self.model_mount_config.mount_destination,
            extra_mounts=extra_mounts,
        )

        execution_spec = ExecutionSpec(
            environ=cast(Optional[dict[str, str]], self.model_runtime_config.environ),
            runtime_variant=RuntimeVariant(self.model_runtime_config.runtime_variant),
            inference_runtime_config=cast(
                Optional[dict[str, Any]], self.model_runtime_config.inference_runtime_config
            ),
        )

        return ModelRevisionCreator(
            image_id=UUID(str(self.image.id)),
            resource_spec=resource_spec,
            mounts=mounts,
            execution=execution_spec,
        )


@strawberry.input(description="Added in 25.19.0")
class AddRevisionInput:
    name: Optional[str] = None
    deployment_id: ID
    cluster_config: ClusterConfigInput
    resource_config: ResourceConfigInput
    image: ImageInput
    model_runtime_config: ModelRuntimeConfigInput
    model_mount_config: ModelMountConfigInput
    extra_mounts: Optional[list[ExtraVFolderMountInput]]

    def to_model_revision_creator(self) -> ModelRevisionCreator:
        """Build ModelRevisionCreator from input fields."""
        resource_spec = ResourceSpec(
            cluster_mode=CommonClusterMode(self.cluster_config.mode),
            cluster_size=self.cluster_config.size,
            resource_slots=cast(Mapping[str, Any], self.resource_config.resource_slots),
            resource_opts=cast(Mapping[str, Any] | None, self.resource_config.resource_opts),
        )

        extra_mounts = []
        if self.extra_mounts is not None:
            extra_mounts = [
                MountInfo(
                    vfolder_id=UUID(str(extra_mount.vfolder_id)),
                    kernel_path=PurePosixPath(
                        extra_mount.mount_destination
                        if extra_mount.mount_destination is not None
                        else ""
                    ),
                )
                for extra_mount in self.extra_mounts
            ]

        mounts = VFolderMountsCreator(
            model_vfolder_id=UUID(str(self.model_mount_config.vfolder_id)),
            model_definition_path=self.model_mount_config.definition_path,
            model_mount_destination=self.model_mount_config.mount_destination,
            extra_mounts=extra_mounts,
        )

        execution_spec = ExecutionSpec(
            environ=cast(Optional[dict[str, str]], self.model_runtime_config.environ),
            runtime_variant=RuntimeVariant(self.model_runtime_config.runtime_variant),
            inference_runtime_config=cast(
                Optional[dict[str, Any]], self.model_runtime_config.inference_runtime_config
            ),
        )

        return ModelRevisionCreator(
            image_id=UUID(str(self.image.id)),
            resource_spec=resource_spec,
            mounts=mounts,
            execution=execution_spec,
        )


ModelRevisionEdge = Edge[ModelRevision]


@strawberry.type(description="Added in 25.19.0")
class ModelRevisionConnection(Connection[ModelRevision]):
    count: int

    def __init__(self, *args, count: int, **kwargs: Any) -> None:
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
