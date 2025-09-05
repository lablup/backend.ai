from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum, StrEnum
from typing import Any, Optional, cast
from uuid import UUID, uuid4

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo
from strawberry.scalars import JSON

from ai.backend.manager.api.gql.base import JSONString, OrderDirection, StringFilter
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
    mock_vfolder_id,
)
from ai.backend.manager.data.model_deployment.inference_runtime_config import (
    MOJORuntimeConfig,
    NVDIANIMRuntimeConfig,
    SGLangRuntimeConfig,
    VLLMRuntimeConfig,
)


@strawberry.enum(description="Added in 25.13.0")
class ClusterMode(StrEnum):
    SINGLE_NODE = "SINGLE_NODE"
    MULTI_NODE = "MULTI_NODE"


@strawberry.type(description="Added in 25.13.0")
class ModelMountConfig:
    vfolder: VFolder
    mount_destination: str
    definition_path: str


@strawberry.type(description="Added in 25.13.0")
class ModelRuntimeConfig:
    runtime_variant: str
    inference_runtime_config: Optional[JSON] = None
    environ: Optional[JSONString] = strawberry.field(
        description='Environment variables for the service, e.g. {"CUDA_VISIBLE_DEVICES": "0"}',
        default=None,
    )


@strawberry.type(description="Added in 25.13.0")
class ResourceConfig:
    resource_group: ResourceGroup
    resource_slots: JSONString = strawberry.field(
        description='Resource Slots are a JSON string that describes the resources allocated for the deployment. Example: "resourceSlots": "{\\"cpu\\": \\"1\\", \\"mem\\": \\"1073741824\\", \\"cuda.device\\": \\"0\\"}"'
    )
    resource_opts: Optional[JSONString] = strawberry.field(
        description='Resource Options are a JSON string that describes additional options for the resources. This is especially used for shared memory configurations. Example: "resourceOpts": "{\\"shmem\\": \\"64m\\"}"',
        default=None,
    )


@strawberry.type(description="Added in 25.13.0")
class ClusterConfig:
    mode: ClusterMode
    size: int


@strawberry.type(description="Added in 25.13.0")
class ModelRevision(Node):
    id: NodeID
    name: str

    cluster_config: ClusterConfig
    resource_config: ResourceConfig

    model_runtime_config: ModelRuntimeConfig
    model_mount_config: ModelMountConfig
    extra_mounts: ExtraVFolderMountConnection

    image: Image

    created_at: datetime


# Filter and Order Types
@strawberry.input(description="Added in 25.13.0")
class ModelRevisionFilter:
    name: Optional[StringFilter] = None
    deployment_id: Optional[ID] = None

    AND: Optional[list["ModelRevisionFilter"]] = None
    OR: Optional[list["ModelRevisionFilter"]] = None
    NOT: Optional[list["ModelRevisionFilter"]] = None
    DISTINCT: Optional[bool] = None


@strawberry.enum(description="Added in 25.13.0")
class ModelRevisionOrderField(Enum):
    CREATED_AT = "CREATED_AT"
    NAME = "NAME"


@strawberry.input(description="Added in 25.13.0")
class ModelRevisionOrderBy:
    field: ModelRevisionOrderField
    direction: OrderDirection = OrderDirection.DESC


# TODO: After implementing the actual logic, remove these mock objects
# Mock Model Revisions


def _generate_random_name() -> str:
    return f"revision-{uuid4()}"


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
mock_image_global_id = ID("SW1hZ2VOb2RlOjQwMWZjYjM4LTkwMWYtNDdjYS05YmJjLWQyMjUzYjk4YTZhMA==")
mock_revision_id_1 = "d19f8f78-f308-45a9-ab7b-1c63346024fd"
mock_model_revision_1 = ModelRevision(
    id=UUID(mock_revision_id_1),
    name="llama-3-8b-instruct-v1.0",
    cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
    resource_config=ResourceConfig(
        resource_group=ResourceGroup(id=ID("U2NhbGluZ0dyb3VwTm9kZTpkZWZhdWx0")),
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
        vfolder=VFolder(id=mock_vfolder_id),
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
    image=Image(id=mock_image_global_id),
    created_at=datetime.now() - timedelta(days=10),
)

mock_revision_id_2 = "3c81bc63-24c1-4a8f-9ad2-8a19899690c3"
mock_model_revision_2 = ModelRevision(
    id=UUID(mock_revision_id_2),
    name="llama-3-8b-instruct-v1.1",
    cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
    resource_config=ResourceConfig(
        resource_group=ResourceGroup(id=ID("U2NhbGluZ0dyb3VwTm9kZTpkZWZhdWx0")),
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
        runtime_variant="vllm",
        inference_runtime_config=mock_inference_runtime_config,
        environ=cast(JSONString, '{"CUDA_VISIBLE_DEVICES": "0,1"}'),
    ),
    model_mount_config=ModelMountConfig(
        vfolder=VFolder(id=mock_vfolder_id),
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
    image=Image(id=mock_image_global_id),
    created_at=datetime.now() - timedelta(days=5),
)


mock_revision_id_3 = "86d1a714-b177-4851-897f-da36f306fe30"
mock_model_revision_3 = ModelRevision(
    id=UUID(mock_revision_id_3),
    name="mistral-7b-v0.3-initial",
    cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
    resource_config=ResourceConfig(
        resource_group=ResourceGroup(id=ID("U2NhbGluZ0dyb3VwTm9kZTpkZWZhdWx0")),
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
        runtime_variant="vllm",
        inference_runtime_config=mock_inference_runtime_config,
        environ=cast(JSONString, '{"CUDA_VISIBLE_DEVICES": "2"}'),
    ),
    model_mount_config=ModelMountConfig(
        vfolder=VFolder(id=mock_vfolder_id),
        mount_destination="/models",
        definition_path="models/mistral-7b/config.yaml",
    ),
    extra_mounts=ExtraVFolderMountConnection(
        count=0,
        edges=[],
        page_info=PageInfo(
            has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
        ),
    ),
    image=Image(id=mock_image_global_id),
    created_at=datetime.now() - timedelta(days=20),
)


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


ModelRevisionEdge = Edge[ModelRevision]


@strawberry.type(description="Added in 25.13.0")
class ModelRevisionConnection(Connection[ModelRevision]):
    count: int

    def __init__(self, *args, count: int, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.count = count


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
    # Implement the logic to resolve the revisions based on the provided filters and pagination
    return ModelRevisionConnection(
        count=3,
        edges=[
            ModelRevisionEdge(node=mock_model_revision_1, cursor="revision-cursor-1"),
            ModelRevisionEdge(node=mock_model_revision_2, cursor="revision-cursor-2"),
            ModelRevisionEdge(node=mock_model_revision_3, cursor="revision-cursor-3"),
        ],
        page_info=PageInfo(
            has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
        ),
    )


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
    return mock_model_revision_1


@strawberry.mutation(description="Added in 25.13.0")
async def create_model_revision(
    input: CreateModelRevisionInput, info: Info[StrawberryGQLContext]
) -> CreateModelRevisionPayload:
    """Create a new model revision."""
    revision = ModelRevision(
        id=UUID("4cc91efb-7297-47ec-80c4-6e9c4378ae8b"),
        name=_generate_random_name(),
        cluster_config=ClusterConfig(
            mode=ClusterMode.SINGLE_NODE,
            size=1,
        ),
        resource_config=ResourceConfig(
            resource_group=ResourceGroup(id=ID("U2NhbGluZ0dyb3VwTm9kZTpkZWZhdWx0")),
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
            runtime_variant=input.model_runtime_config.runtime_variant,
            inference_runtime_config=input.model_runtime_config.inference_runtime_config,
            environ=None,
        ),
        model_mount_config=ModelMountConfig(
            vfolder=VFolder(id=mock_vfolder_id),
            mount_destination="/models",
            definition_path="model.yaml",
        ),
        extra_mounts=ExtraVFolderMountConnection(
            count=0,
            edges=[],
            page_info=PageInfo(
                has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
            ),
        ),
        image=Image(id=mock_image_global_id),
        created_at=datetime.now(),
    )
    return CreateModelRevisionPayload(revision=revision)


@strawberry.mutation(description="Added in 25.13.0")
async def add_model_revision(
    input: AddModelRevisionInput, info: Info[StrawberryGQLContext]
) -> AddModelRevisionPayload:
    """Add a model revision to a deployment."""
    revision = ModelRevision(
        id=UUID("dda405f0-6463-45c4-a5ca-3721cc8d730c"),
        name=_generate_random_name(),
        cluster_config=ClusterConfig(
            mode=ClusterMode.SINGLE_NODE,
            size=1,
        ),
        resource_config=ResourceConfig(
            resource_group=ResourceGroup(id=ID("U2NhbGluZ0dyb3VwTm9kZTpkZWZhdWx0")),
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
            runtime_variant=input.model_runtime_config.runtime_variant,
            inference_runtime_config=input.model_runtime_config.inference_runtime_config,
            environ=None,
        ),
        model_mount_config=ModelMountConfig(
            vfolder=VFolder(id=mock_vfolder_id),
            mount_destination="/models",
            definition_path="model.yaml",
        ),
        extra_mounts=ExtraVFolderMountConnection(
            count=0,
            edges=[],
            page_info=PageInfo(
                has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
            ),
        ),
        image=Image(id=mock_image_global_id),
        created_at=datetime.now(),
    )
    return AddModelRevisionPayload(revision=revision)
