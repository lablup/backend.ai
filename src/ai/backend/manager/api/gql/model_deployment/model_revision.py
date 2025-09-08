from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum, StrEnum
from pathlib import PurePosixPath
from typing import Any, Optional, cast
from uuid import UUID, uuid4

import strawberry
from aiotools import apartial
from strawberry import ID, Info
from strawberry.dataloader import DataLoader
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo
from strawberry.scalars import JSON

from ai.backend.common.exception import ModelDeploymentUnavailableError
from ai.backend.common.types import ClusterMode as CommonClusterMode
from ai.backend.common.types import MountPermission as CommonMountPermission
from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.api.gql.base import (
    JSONString,
    OrderDirection,
    StringFilter,
    resolve_global_id,
    to_global_id,
)
from ai.backend.manager.api.gql.image import (
    Image,
)
from ai.backend.manager.api.gql.resource_group import (
    ResourceGroup,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.vfolder import (
    ExtraVFolderMountConnection,
    ExtraVFolderMountEdge,
    VFolder,
    mock_extra_mount_1,
    mock_extra_mount_2,
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
    ModelRuntimeConfigData,
    MountInfo,
    ResourceConfigData,
    ResourceSpec,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.models.gql_models.image import ImageNode
from ai.backend.manager.models.gql_models.scaling_group import ScalingGroupNode
from ai.backend.manager.models.gql_models.vfolder import VirtualFolderNode
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revisions_by_deployment_id import (
    GetRevisionsByDeploymentIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.list_revisions import (
    ListRevisionsAction,
)
from ai.backend.manager.types import PaginationOptions

MountPermission = strawberry.enum(
    CommonMountPermission,
    name="MountPermission",
    description="Added in 25.13.0. This enum represents the permission level for a mounted volume. It can be ro, rw, wd",
)


@strawberry.enum(description="Added in 25.13.0")
class ClusterMode(StrEnum):
    SINGLE_NODE = "SINGLE_NODE"
    MULTI_NODE = "MULTI_NODE"


@strawberry.type(description="Added in 25.13.0")
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


@strawberry.type(description="Added in 25.13.0")
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


@strawberry.type(description="Added in 25.13.0")
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


@strawberry.type(description="Added in 25.13.0")
class ClusterConfig:
    mode: ClusterMode
    size: int

    @classmethod
    def from_dataclass(cls, data: ClusterConfigData) -> "ClusterConfig":
        return cls(
            mode=ClusterMode(data.mode.name),
            size=data.size,
        )


@strawberry.type(description="Added in 25.13.0")
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

    @classmethod
    async def batch_load_by_ids(
        cls, ctx: StrawberryGQLContext, revision_ids: Sequence[UUID]
    ) -> list["ModelRevision"]:
        """Batch load revisions by their IDs."""
        processor = ctx.processors.deployment
        if processor is None:
            raise ModelDeploymentUnavailableError(
                "Model Deployment feature is unavailable. Please contact support."
            )

        revisions = []

        for revision_id in revision_ids:
            action_result = await processor.get_revision_by_id.wait_for_complete(
                GetRevisionByIdAction(revision_id=revision_id)
            )
            revisions.append(action_result.data)

        return [cls.from_dataclass(revision) for revision in revisions if revision]

    @classmethod
    async def batch_load_by_deployment_ids(
        cls, ctx: StrawberryGQLContext, deployment_ids: Sequence[UUID]
    ) -> list["ModelRevision"]:
        processor = ctx.processors.deployment
        if processor is None:
            raise ModelDeploymentUnavailableError(
                "Model Deployment feature is unavailable. Please contact support."
            )

        revisions = []

        for deployment_id in deployment_ids:
            action_result = await processor.get_revisions_by_deployment_id.wait_for_complete(
                GetRevisionsByDeploymentIdAction(deployment_id=deployment_id)
            )
            revisions.extend(action_result.data)

        return [cls.from_dataclass(revision) for revision in revisions if revision]


# Filter and Order Types
@strawberry.input(description="Added in 25.13.0")
class ModelRevisionFilter:
    name: Optional[StringFilter] = None
    deployment_id: Optional[ID] = None
    id: Optional[ID] = None

    AND: Optional[list["ModelRevisionFilter"]] = None
    OR: Optional[list["ModelRevisionFilter"]] = None
    NOT: Optional[list["ModelRevisionFilter"]] = None


@strawberry.enum(description="Added in 25.13.0")
class ModelRevisionOrderField(Enum):
    CREATED_AT = "CREATED_AT"
    NAME = "NAME"
    ID = "ID"


@strawberry.input(description="Added in 25.13.0")
class ModelRevisionOrderBy:
    field: ModelRevisionOrderField
    direction: OrderDirection = OrderDirection.DESC


# TODO: After implementing the actual logic, remove these mock objects
# Mock Model Revisions
mock_inference_runtime_config = {
    "tp_size": 2,
    "pp_size": 4,
    "ep_enable": True,
    "sp_size": 8,
    "max_model_length": 4096,
    "batch_size": 32,
    "memory_util_percentage": Decimal("0.90"),
    "kv_storage_dtype": "float16",
    "trust_remote_code": True,
    "tool_call_parser": "granite",
    "reasoning_parser": "deepseek_r1",
}


# Payload Types
@strawberry.type(description="Added in 25.13.0")
class CreateModelRevisionPayload:
    revision: ModelRevision


@strawberry.type(description="Added in 25.13.0")
class AddModelRevisionPayload:
    revision: ModelRevision


# Input Types
@strawberry.input(description="Added in 25.13.0")
class ClusterConfigInput:
    mode: ClusterMode
    size: int


@strawberry.input(description="Added in 25.13.0")
class ResourceGroupInput:
    name: str


@strawberry.input(description="Added in 25.13.0")
class ResourceConfigInput:
    resource_group: ResourceGroupInput
    resource_slots: JSONString = strawberry.field(
        description='Resources allocated for the deployment. Example: "resourceSlots": "{\\"cpu\\": \\"1\\", \\"mem\\": \\"1073741824\\", \\"cuda.device\\": \\"0\\"}"'
    )
    resource_opts: Optional[JSONString] = strawberry.field(
        description='Additional options for the resources. This is especially used for shared memory configurations. Example: "resourceOpts": "{\\"shmem\\": \\"64m\\"}"',
        default=None,
    )


@strawberry.input(description="Added in 25.13.0")
class ImageInput:
    name: str
    architecture: str


@strawberry.input(description="Added in 25.13.0")
class ModelRuntimeConfigInput:
    runtime_variant: str
    inference_runtime_config: Optional[JSON] = None
    environ: Optional[JSONString] = strawberry.field(
        description='Environment variables for the service, e.g. {"CUDA_VISIBLE_DEVICES": "0"}',
        default=None,
    )


@strawberry.input(description="Added in 25.13.0")
class ModelMountConfigInput:
    vfolder_id: ID
    mount_destination: str
    definition_path: str


@strawberry.input(description="Added in 25.13.0")
class ExtraVFolderMountInput:
    vfolder_id: ID
    mount_destination: Optional[str]


@strawberry.input(description="Added in 25.13.0")
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


@strawberry.input(description="Added in 25.13.0")
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


@strawberry.type(description="Added in 25.13.0")
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
    description="Added in 25.13.0. Get JSON Schema for inference runtime configuration"
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
    description="Added in 25.13.0 Get configuration JSON Schemas for all inference runtimes"
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
        raise ModelDeploymentUnavailableError(
            "Model Deployment feature is unavailable. Please contact support."
        )
    action_result = await processor.list_revisions.wait_for_complete(
        ListRevisionsAction(pagination=PaginationOptions())
    )
    edges = []
    for revision in action_result.data:
        edges.append(
            ModelRevisionEdge(node=ModelRevision.from_dataclass(revision), cursor=str(revision.id))
        )

    # Mock pagination info for demonstration purposes
    connection = ModelRevisionConnection(
        count=action_result.total_count,
        edges=edges,
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor="revision-cursor-1",
            end_cursor="revision-cursor-3",
        ),
    )
    return connection


@strawberry.field(description="Added in 25.13.0")
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


@strawberry.field(description="Added in 25.13.0")
async def revision(id: ID, info: Info[StrawberryGQLContext]) -> ModelRevision:
    """Get a specific revision by ID."""
    _, revision_id = resolve_global_id(id)
    revision_loader = DataLoader(apartial(ModelRevision.batch_load_by_ids, info.context))
    revision: list[ModelRevision] = await revision_loader.load(revision_id)
    return revision[0]


@strawberry.mutation(description="Added in 25.13.0")
async def add_model_revision(
    input: AddModelRevisionInput, info: Info[StrawberryGQLContext]
) -> AddModelRevisionPayload:
    """Add a model revision to a deployment."""

    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailableError(
            "Model Deployment feature is unavailable. Please contact support."
        )

    result = await processor.add_model_revision.wait_for_complete(
        AddModelRevisionAction(input.to_model_revision_creator())
    )

    return AddModelRevisionPayload(revision=ModelRevision.from_dataclass(result.revision))


@strawberry.mutation(
    description="Added in 25.13.0. Create model revision which is not attached to any deployment."
)
async def create_model_revision(
    input: CreateModelRevisionInput, info: Info[StrawberryGQLContext]
) -> CreateModelRevisionPayload:
    """Create a new model revision."""
    return CreateModelRevisionPayload(
        revision=ModelRevision(
            id=UUID("d19f8f78-f308-45a9-ab7b-1c63346024fd"),
            name="llama-3-8b-instruct-v1.0",
            cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
            resource_config=ResourceConfig(
                _resource_group_name="default",
                resource_slots=cast(
                    JSONString,
                    '{"cpu": 8, "mem": "32G", "cuda.shares": 1, "cuda.device": 1}',
                ),
                resource_opts=cast(
                    JSONString,
                    '{"shmem": "2G", "reserved_time": "24h", "scaling_group": "us-east-1"}',
                ),
            ),
            model_runtime_config=ModelRuntimeConfig(
                runtime_variant="custom",
                inference_runtime_config=mock_inference_runtime_config,
                environ=cast(JSONString, '{"CUDA_VISIBLE_DEVICES": "0"}'),
            ),
            model_mount_config=ModelMountConfig(
                _vfolder_id=uuid4(),
                mount_destination="/models",
                definition_path="models/llama-3-8b/config.yaml",
            ),
            extra_mounts=ExtraVFolderMountConnection(
                count=2,
                edges=[
                    ExtraVFolderMountEdge(node=mock_extra_mount_1, cursor="extra-mount-cursor-1"),
                    ExtraVFolderMountEdge(node=mock_extra_mount_2, cursor="extra-mount-cursor-2"),
                ],
                page_info=PageInfo(
                    has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
                ),
            ),
            _image_id=uuid4(),
            created_at=datetime.now() - timedelta(days=10),
        )
    )
