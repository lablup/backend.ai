from datetime import datetime, timedelta
from enum import Enum, StrEnum
from typing import Annotated, Any, Optional, cast

import strawberry
from strawberry import ID, Info, relay
from strawberry.relay import Connection, Edge, PageInfo
from strawberry.relay.types import NodeIterableType

from ai.backend.manager.api.gql.base import JSONString, OrderDirection, StringFilter
from ai.backend.manager.api.gql.federated_types import Image, ResourceGroup, VFolder


@strawberry.enum
class ClusterMode(StrEnum):
    SINGLE_NODE = "SINGLE_NODE"
    MULTI_NODE = "MULTI_NODE"


@strawberry.enum
class MountPermission(StrEnum):
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"


@strawberry.enum
class MountType(StrEnum):
    BIND = "BIND"
    VOLUME = "VOLUME"


# Types
@strawberry.type
class ClusterConfig:
    mode: ClusterMode
    size: int


@strawberry.type
class Mount:
    vfolder_id: ID
    destination: str
    type: MountType
    permission: MountPermission


@strawberry.type
class ModelVFolderConfig:
    vfolder: VFolder
    mount_destination: str
    definition_path: str


@strawberry.type
class ResourceConfig:
    resource_group: ResourceGroup
    resource_slots: JSONString
    resource_opts: Optional[JSONString] = None


@strawberry.type
class RawServiceConfig:
    config: JSONString
    extra_cli_parameters: Optional[str] = None


ServiceConfig = Annotated[
    RawServiceConfig,
    strawberry.union(
        "ServiceConfig", description="Different service configurations for model runtime"
    ),
]


@strawberry.type
class ModelRuntimeConfig:
    runtime_variant: str
    service_config: Optional[ServiceConfig] = None
    environ: Optional[JSONString] = None


@strawberry.type
class ModelRevision(relay.Node):
    id: relay.NodeID
    name: str

    cluster_config: ClusterConfig
    resource_config: ResourceConfig
    model_runtime_config: ModelRuntimeConfig
    model_vfolder_config: ModelVFolderConfig
    mounts: list[Mount]

    image: Image

    created_at: datetime


# Filter and Order Types
@strawberry.input
class ModelRevisionFilter:
    name: Optional[StringFilter] = None
    deployment_id: Optional[ID] = None

    AND: Optional["ModelRevisionFilter"] = None
    OR: Optional["ModelRevisionFilter"] = None
    NOT: Optional["ModelRevisionFilter"] = None
    DISTINCT: Optional[bool] = None


@strawberry.enum
class ModelRevisionOrderField(Enum):
    CREATED_AT = "CREATED_AT"
    NAME = "NAME"


@strawberry.input
class ModelRevisionOrder:
    field: ModelRevisionOrderField
    direction: OrderDirection = OrderDirection.DESC


# TODO: After implementing the actual logic, remove these mock objects
# Mock Model Revisions
mock_model_revision_1 = ModelRevision(
    id="rev-001",
    name="llama-3-8b-instruct-v1.0",
    cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
    resource_config=ResourceConfig(
        resource_group=ResourceGroup(id=ID("rg-us-east-1")),
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
        service_config=RawServiceConfig(
            config=cast(
                JSONString,
                '{"max_model_length": 4096, "parallelism": {"tensor_parallel_size": 1}, "extra_cli_parameters": "--enable-prefix-caching"}',
            ),
        ),
        environ=cast(JSONString, '{"CUDA_VISIBLE_DEVICES": "0"}'),
    ),
    model_vfolder_config=ModelVFolderConfig(
        vfolder=VFolder(id=ID("vf-model-001")),
        mount_destination="/models",
        definition_path="models/llama-3-8b/config.yaml",
    ),
    mounts=[
        Mount(
            vfolder_id=ID("vf-cache-001"),
            destination="/cache",
            type=MountType.VOLUME,
            permission=MountPermission.READ_WRITE,
        )
    ],
    image=Image(id=ID("img-vllm-001")),
    created_at=datetime.now() - timedelta(days=10),
)

mock_model_revision_2 = ModelRevision(
    id="rev-002",
    name="llama-3-8b-instruct-v1.1",
    cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
    resource_config=ResourceConfig(
        resource_group=ResourceGroup(id=ID("rg-us-east-1")),
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
        service_config=RawServiceConfig(
            config=cast(
                JSONString,
                '{"max_model_length": 4096, "parallelism": {"tensor_parallel_size": 1}, "extra_cli_parameters": "--enable-prefix-caching"}',
            ),
        ),
        environ=cast(JSONString, '{"CUDA_VISIBLE_DEVICES": "0,1"}'),
    ),
    model_vfolder_config=ModelVFolderConfig(
        vfolder=VFolder(id=ID("vf-model-002")),
        mount_destination="/models",
        definition_path="models/llama-3-8b/config.yaml",
    ),
    mounts=[
        Mount(
            vfolder_id=ID("vf-cache-002"),
            destination="/cache",
            type=MountType.VOLUME,
            permission=MountPermission.READ_WRITE,
        )
    ],
    image=Image(id=ID("img-vllm-002")),
    created_at=datetime.now() - timedelta(days=5),
)

mock_model_revision_3 = ModelRevision(
    id="rev-003",
    name="mistral-7b-v0.3-initial",
    cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
    resource_config=ResourceConfig(
        resource_group=ResourceGroup(id=ID("rg-us-west-2")),
        resource_slots=cast(
            JSONString,
            '{"cpu": 4, "mem": "16G", "cuda.shares": 0.5, "cuda.device": 1}',
        ),
        resource_opts=cast(
            JSONString,
            '{"shmem": "1G", "reserved_time": "12h", "scaling_group": "us-west-2"}',
        ),
    ),
    model_runtime_config=ModelRuntimeConfig(
        runtime_variant="vllm",
        service_config=RawServiceConfig(
            config=cast(
                JSONString,
                '{"max_model_length": 4096, "parallelism": {"tensor_parallel_size": 1}, "extra_cli_parameters": "--enable-prefix-caching"}',
            ),
        ),
        environ=cast(JSONString, '{"CUDA_VISIBLE_DEVICES": "2"}'),
    ),
    model_vfolder_config=ModelVFolderConfig(
        vfolder=VFolder(id=ID("vf-model-003")),
        mount_destination="/models",
        definition_path="models/mistral-7b/config.yaml",
    ),
    mounts=[],
    image=Image(id=ID("img-vllm-003")),
    created_at=datetime.now() - timedelta(days=20),
)


# Payload Types
@strawberry.type
class CreateModelRevisionPayload:
    revision: ModelRevision


# Input Types
@strawberry.input
class ImageInput:
    name: str
    architecture: str


@strawberry.input
class ClusterConfigInput:
    mode: ClusterMode
    size: int


@strawberry.input
class ResourceGroupInput:
    id: ID


@strawberry.input
class ScalingGroupNodeInput:
    name: str


@strawberry.input
class ResourceConfigInput:
    resource_group: ScalingGroupNodeInput
    resource_slots: JSONString
    resource_opts: Optional[JSONString] = None


@strawberry.input
class ModelRuntimeConfigInput:
    runtime_variant: str
    service_config: Optional[JSONString] = None
    environ: Optional[JSONString] = None


@strawberry.input
class ModelVFolderConfigInput:
    vfolder_id: ID
    mount_destination: str
    definition_path: str


@strawberry.input
class MountInput:
    vfolder_id: ID
    destination: str
    type: MountType
    permission: MountPermission


@strawberry.input
class CreateModelRevisionInput:
    deployment_id: ID
    name: str
    image: ImageInput
    model_runtime_config: ModelRuntimeConfigInput
    model_vfolder_config: ModelVFolderConfigInput
    mounts: Optional[list[MountInput]] = None
    resource_config: ResourceConfigInput


ModelRevisionEdge = Edge[ModelRevision]


@strawberry.type
class ModelRevisionConnection(Connection[ModelRevision]):
    """Connection type for ModelRevision, used for Relay pagination."""

    @strawberry.field
    def count(self) -> int:
        return 0

    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[ModelRevision],
        *,
        info: Optional[Info] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        max_results: Optional[int] = None,
        **kwargs: Any,
    ):
        """Resolve the connection for Relay pagination."""
        revisions = [mock_model_revision_1, mock_model_revision_2, mock_model_revision_3]
        edges = [ModelRevisionEdge(node=rev, cursor=str(i)) for i, rev in enumerate(revisions)]
        return cls(
            edges=edges,
            page_info=PageInfo(
                has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
            ),
        )


@strawberry.relay.connection(ModelRevisionConnection)
async def revisions(
    filter: Optional[ModelRevisionFilter] = None,
    order: Optional[ModelRevisionOrder] = None,
    first: Optional[int] = None,
    after: Optional[str] = None,
) -> list[ModelRevision]:
    """List revisions with optional filtering and pagination."""
    return [mock_model_revision_1, mock_model_revision_2, mock_model_revision_3]


@strawberry.field
async def revision(id: ID) -> Optional[ModelRevision]:
    """Get a specific revision by ID."""
    return None


@strawberry.mutation
async def create_model_revision(input: CreateModelRevisionInput) -> CreateModelRevisionPayload:
    """Create a new model revision."""
    revision = ModelRevision(
        id=ID(f"rev-new-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
        name=input.name,
        cluster_config=ClusterConfig(
            mode=ClusterMode.SINGLE_NODE,
            size=1,
        ),
        resource_config=ResourceConfig(
            resource_group=ResourceGroup(id=ID(input.resource_config.resource_group.name)),
            resource_slots=cast(
                JSONString,
                input.resource_config.resource_slots,
            ),
            resource_opts=cast(
                JSONString,
                input.resource_config.resource_opts,
            ),
        ),
        model_runtime_config=ModelRuntimeConfig(
            runtime_variant=input.model_runtime_config.runtime_variant,
            service_config=None,
            environ=None,
        ),
        model_vfolder_config=ModelVFolderConfig(
            vfolder=VFolder(id=ID("vf-id")),
            mount_destination="/models",
            definition_path="model.yaml",
        ),
        mounts=[],
        image=Image(id=ID("image-id")),
        created_at=datetime.now(),
    )
    return CreateModelRevisionPayload(revision=revision)
