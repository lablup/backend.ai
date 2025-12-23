from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import StrEnum
from functools import lru_cache
from pathlib import PurePosixPath
from typing import Any, Optional, cast, override
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo
from strawberry.scalars import JSON

from ai.backend.common.exception import ModelDeploymentUnavailable
from ai.backend.common.types import ClusterMode as CommonClusterMode
from ai.backend.common.types import MountPermission as CommonMountPermission
from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import (
    JSONString,
    OrderDirection,
    StringFilter,
    encode_cursor,
    resolve_global_id,
    to_global_id,
)
from ai.backend.manager.api.gql.image import (
    Image,
)
from ai.backend.manager.api.gql.resource_group import (
    ResourceGroup,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.vfolder import (
    ExtraVFolderMountConnection,
    VFolder,
)
from ai.backend.manager.data.deployment.creator import ModelRevisionCreator, VFolderMountsCreator
from ai.backend.manager.data.deployment.inference_runtime_config import (
    MOJORuntimeConfig,
    NVDIANIMRuntimeConfig,
    SGLangRuntimeConfig,
    VLLMRuntimeConfig,
)
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
from ai.backend.manager.data.image.types import ImageIdentifier
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
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.create_model_revision import (
    CreateModelRevisionAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revisions import (
    SearchRevisionsAction,
)


# Pagination spec
@lru_cache(maxsize=1)
def _get_revision_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RevisionOrders.created_at(ascending=False),
        backward_order=RevisionOrders.created_at(ascending=True),
        forward_condition_factory=RevisionConditions.by_cursor_forward,
        backward_condition_factory=RevisionConditions.by_cursor_backward,
    )


MountPermission = strawberry.enum(
    CommonMountPermission,
    name="MountPermission",
    description="Added in 25.16.0. This enum represents the permission level for a mounted volume. It can be ro, rw, wd",
)


@strawberry.enum(description="Added in 25.16.0")
class ClusterMode(StrEnum):
    SINGLE_NODE = "SINGLE_NODE"
    MULTI_NODE = "MULTI_NODE"


@strawberry.type(description="Added in 25.16.0")
class ModelMountConfig:
    _vfolder_id: strawberry.Private[UUID]
    mount_destination: str
    definition_path: str

    @strawberry.field
    async def vfolder(self, info: Info[StrawberryGQLContext]) -> VFolder:
        vfolder_global_id = to_global_id(
            VirtualFolderNode, self._vfolder_id, is_target_graphene_object=True
        )
        return VFolder(id=ID(vfolder_global_id))

    @classmethod
    def from_dataclass(cls, data: ModelMountConfigData) -> "ModelMountConfig":
        return cls(
            _vfolder_id=data.vfolder_id,
            mount_destination=data.mount_destination,
            definition_path=data.definition_path,
        )


@strawberry.type(description="Added in 25.16.0")
class ModelRuntimeConfig:
    runtime_variant: str
    inference_runtime_config: Optional[JSON] = None
    environ: Optional[JSONString] = strawberry.field(
        description='Environment variables for the service, e.g. {"CUDA_VISIBLE_DEVICES": "0"}',
        default=None,
    )

    @classmethod
    def from_dataclass(cls, data: ModelRuntimeConfigData) -> "ModelRuntimeConfig":
        return cls(
            runtime_variant=data.runtime_variant,
            inference_runtime_config=data.inference_runtime_config,
            environ=JSONString.serialize(data.environ) if data.environ else None,
        )


@strawberry.type(description="Added in 25.16.0")
class ResourceConfig:
    _resource_group_name: strawberry.Private[str]
    resource_slots: JSONString = strawberry.field(
        description='Resource Slots are a JSON string that describes the resources allocated for the deployment. Example: "resourceSlots": "{\\"cpu\\": \\"1\\", \\"mem\\": \\"1073741824\\", \\"cuda.device\\": \\"0\\"}"'
    )
    resource_opts: Optional[JSONString] = strawberry.field(
        description='Resource Options are a JSON string that describes additional options for the resources. This is especially used for shared memory configurations. Example: "resourceOpts": "{\\"shmem\\": \\"64m\\"}"',
        default=None,
    )

    @strawberry.field
    def resource_group(self) -> "ResourceGroup":
        """Resolves the federated ResourceGroup."""
        global_id = to_global_id(
            ScalingGroupNode, self._resource_group_name, is_target_graphene_object=True
        )
        return ResourceGroup(id=ID(global_id))

    @classmethod
    def from_dataclass(cls, data: ResourceConfigData) -> "ResourceConfig":
        return cls(
            _resource_group_name=data.resource_group_name,
            resource_slots=JSONString.from_resource_slot(data.resource_slot),
            resource_opts=JSONString.serialize(data.resource_opts),
        )


@strawberry.type(description="Added in 25.16.0")
class ClusterConfig:
    mode: ClusterMode
    size: int

    @classmethod
    def from_dataclass(cls, data: ClusterConfigData) -> "ClusterConfig":
        return cls(
            mode=ClusterMode(data.mode.name),
            size=data.size,
        )


@strawberry.type(description="Added in 25.16.0")
class ModelRevision(Node):
    _image_id: strawberry.Private[UUID]
    id: NodeID
    name: str
    cluster_config: ClusterConfig
    resource_config: ResourceConfig
    model_runtime_config: ModelRuntimeConfig
    model_mount_config: ModelMountConfig
    extra_mounts: ExtraVFolderMountConnection
    created_at: datetime

    @strawberry.field
    async def image(self, info: Info[StrawberryGQLContext]) -> Image:
        image_global_id = to_global_id(ImageNode, self._image_id, is_target_graphene_object=True)
        return Image(id=ID(image_global_id))

    @classmethod
    def from_dataclass(cls, data: ModelRevisionData) -> "ModelRevision":
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
@strawberry.input(description="Added in 25.16.0")
class ModelRevisionFilter(GQLFilter):
    name: Optional[StringFilter] = None
    deployment_id: Optional[ID] = None
    id: Optional[ID] = None
    ids_in: strawberry.Private[Optional[Sequence[UUID]]] = None

    AND: Optional[list["ModelRevisionFilter"]] = None
    OR: Optional[list["ModelRevisionFilter"]] = None
    NOT: Optional[list["ModelRevisionFilter"]] = None

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

        # Apply id filter
        if self.id:
            field_conditions.append(RevisionConditions.by_ids([UUID(self.id)]))

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


@strawberry.input(description="Added in 25.16.0")
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
@strawberry.type(description="Added in 25.16.0")
class CreateModelRevisionPayload:
    revision: ModelRevision


@strawberry.type(description="Added in 25.16.0")
class AddModelRevisionPayload:
    revision: ModelRevision


# Input Types
@strawberry.input(description="Added in 25.16.0")
class ClusterConfigInput:
    mode: ClusterMode
    size: int


@strawberry.input(description="Added in 25.16.0")
class ResourceGroupInput:
    name: str


@strawberry.input(description="Added in 25.16.0")
class ResourceConfigInput:
    resource_group: ResourceGroupInput
    resource_slots: JSONString = strawberry.field(
        description='Resources allocated for the deployment. Example: "resourceSlots": "{\\"cpu\\": \\"1\\", \\"mem\\": \\"1073741824\\", \\"cuda.device\\": \\"0\\"}"'
    )
    resource_opts: Optional[JSONString] = strawberry.field(
        description='Additional options for the resources. This is especially used for shared memory configurations. Example: "resourceOpts": "{\\"shmem\\": \\"64m\\"}"',
        default=None,
    )


@strawberry.input(description="Added in 25.16.0")
class ImageInput:
    name: str
    architecture: str


@strawberry.input(description="Added in 25.16.0")
class ModelRuntimeConfigInput:
    runtime_variant: str
    inference_runtime_config: Optional[JSON] = None
    environ: Optional[JSONString] = strawberry.field(
        description='Environment variables for the service, e.g. {"CUDA_VISIBLE_DEVICES": "0"}',
        default=None,
    )


@strawberry.input(description="Added in 25.16.0")
class ModelMountConfigInput:
    vfolder_id: ID
    mount_destination: str
    definition_path: str


@strawberry.input(description="Added in 25.16.0")
class ExtraVFolderMountInput:
    vfolder_id: ID
    mount_destination: Optional[str]


@strawberry.input(description="Added in 25.16.0")
class CreateModelRevisionInput:
    name: Optional[str] = None
    cluster_config: ClusterConfigInput
    resource_config: ResourceConfigInput
    image: ImageInput
    model_runtime_config: ModelRuntimeConfigInput
    model_mount_config: ModelMountConfigInput
    extra_mounts: Optional[list[ExtraVFolderMountInput]]

    def to_model_revision_creator(self) -> ModelRevisionCreator:
        image_identifier = ImageIdentifier(
            canonical=self.image.name,
            architecture=self.image.architecture,
        )

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
            image_identifier=image_identifier,
            resource_spec=resource_spec,
            mounts=mounts,
            execution=execution_spec,
        )


@strawberry.input(description="Added in 25.16.0")
class AddModelRevisionInput:
    name: Optional[str] = None
    deployment_id: ID
    cluster_config: ClusterConfigInput
    resource_config: ResourceConfigInput
    image: ImageInput
    model_runtime_config: ModelRuntimeConfigInput
    model_mount_config: ModelMountConfigInput
    extra_mounts: Optional[list[ExtraVFolderMountInput]]

    def to_model_revision_creator(self) -> ModelRevisionCreator:
        image_identifier = ImageIdentifier(
            canonical=self.image.name,
            architecture=self.image.architecture,
        )

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
            image_identifier=image_identifier,
            resource_spec=resource_spec,
            mounts=mounts,
            execution=execution_spec,
        )


ModelRevisionEdge = Edge[ModelRevision]


@strawberry.type(description="Added in 25.16.0")
class ModelRevisionConnection(Connection[ModelRevision]):
    count: int

    def __init__(self, *args, count: int, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.count = count

    @classmethod
    def from_dataclass(cls, revisions_data: list[ModelRevisionData]) -> "ModelRevisionConnection":
        nodes = [ModelRevision.from_dataclass(data) for data in revisions_data]
        edges = [ModelRevisionEdge(node=node, cursor=str(node.id)) for node in nodes]

        page_info = PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        )

        return cls(count=len(nodes), edges=edges, page_info=page_info)


@strawberry.field(
    description="Added in 25.16.0. Get JSON Schema for inference runtime configuration"
)
async def inference_runtime_config(name: str) -> JSON:
    match name.lower():
        case "vllm":
            return VLLMRuntimeConfig.to_json_schema()
        case "sglang":
            return SGLangRuntimeConfig.to_json_schema()
        case "nvdianim":
            return NVDIANIMRuntimeConfig.to_json_schema()
        case "mojo":
            return MOJORuntimeConfig.to_json_schema()
        case _:
            return {
                "error": "Unknown service name",
            }


@strawberry.field(
    description="Added in 25.16.0 Get configuration JSON Schemas for all inference runtimes"
)
async def inference_runtime_configs(info: Info[StrawberryGQLContext]) -> JSON:
    all_configs = {
        "vllm": VLLMRuntimeConfig.to_json_schema(),
        "sglang": SGLangRuntimeConfig.to_json_schema(),
        "nvdianim": NVDIANIMRuntimeConfig.to_json_schema(),
        "mojo": MOJORuntimeConfig.to_json_schema(),
    }

    return all_configs


async def resolve_revisions(
    info: Info[StrawberryGQLContext],
    filter: Optional[ModelRevisionFilter] = None,
    order_by: Optional[list[ModelRevisionOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ModelRevisionConnection:
    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )

    # Build querier using gql_adapter
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_revision_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processor.search_revisions.wait_for_complete(
        SearchRevisionsAction(querier=querier)
    )

    nodes = [ModelRevision.from_dataclass(data) for data in action_result.data]
    edges = [ModelRevisionEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ModelRevisionConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


@strawberry.field(description="Added in 25.16.0")
async def revisions(
    info: Info[StrawberryGQLContext],
    filter: Optional[ModelRevisionFilter] = None,
    order_by: Optional[list[ModelRevisionOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ModelRevisionConnection:
    """List revisions with optional filtering and pagination."""
    return await resolve_revisions(
        info=info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )


@strawberry.field(description="Added in 25.16.0")
async def revision(id: ID, info: Info[StrawberryGQLContext]) -> ModelRevision:
    """Get a specific revision by ID."""
    _, revision_id = resolve_global_id(id)
    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )
    result = await processor.get_revision_by_id.wait_for_complete(
        GetRevisionByIdAction(revision_id=UUID(revision_id))
    )
    return ModelRevision.from_dataclass(result.data)


@strawberry.mutation(description="Added in 25.16.0")
async def add_model_revision(
    input: AddModelRevisionInput, info: Info[StrawberryGQLContext]
) -> AddModelRevisionPayload:
    """Add a model revision to a deployment."""

    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )

    result = await processor.add_model_revision.wait_for_complete(
        AddModelRevisionAction(
            model_deployment_id=UUID(input.deployment_id), adder=input.to_model_revision_creator()
        )
    )

    return AddModelRevisionPayload(revision=ModelRevision.from_dataclass(result.revision))


@strawberry.mutation(
    description="Added in 25.16.0. Create model revision which is not attached to any deployment."
)
async def create_model_revision(
    input: CreateModelRevisionInput, info: Info[StrawberryGQLContext]
) -> CreateModelRevisionPayload:
    """Create a new model revision without attaching it to any deployment."""
    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailable(
            "Model Deployment feature is unavailable. Please contact support."
        )

    result = await processor.create_model_revision.wait_for_complete(
        CreateModelRevisionAction(creator=input.to_model_revision_creator())
    )

    return CreateModelRevisionPayload(revision=ModelRevision.from_dataclass(result.revision))
