from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum, StrEnum
from typing import Any, Optional, cast
from uuid import UUID, uuid4

import strawberry
from strawberry import ID, Info, relay
from strawberry.relay import Connection, Edge, PageInfo
from strawberry.relay.types import NodeIterableType
from strawberry.scalars import JSON

from ai.backend.manager.api.gql.base import JSONString, OrderDirection, StringFilter
from ai.backend.manager.api.gql.image import Image, ResourceLimit
from ai.backend.manager.api.gql.resource_group import ResourceGroup
from ai.backend.manager.api.gql.vfolder import (
    ExtraVFolderMountConnection,
    ExtraVFolderMountEdge,
    VFolder,
    mock_extra_mount_1,
    mock_extra_mount_2,
    mock_model_vfolder_1,
    mock_model_vfolder_2,
    mock_model_vfolder_3,
    mock_model_vfolder_4,
    mock_model_vfolder_5,
)
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.data.model_deployment.inference_runtime_config import (
    MOJORuntimeConfig,
    NVDIANIMRuntimeConfig,
    SGLangRuntimeConfig,
    VLLMRuntimeConfig,
)
from ai.backend.manager.models.rbac.permission_defs import (
    ImagePermission,
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
class ModelRevision(relay.Node):
    id: relay.NodeID
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
class ModelRevisionOrder:
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

mock_revision_id_1 = "d19f8f78-f308-45a9-ab7b-1c63346024fd"
mock_resource_group_id_1 = "1bd4a689-8dab-4355-aadd-9957932d896a"
mock_image_id_1 = "7609ac08-d5e0-410a-a045-10c42119ed21"
mock_model_revision_1 = ModelRevision(
    id=UUID(mock_revision_id_1),
    name="llama-3-8b-instruct-v1.0",
    cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
    resource_config=ResourceConfig(
        resource_group=ResourceGroup(
            id=UUID(mock_resource_group_id_1),
            name="gpu-cluster-01",
            description="Primary GPU cluster for inference",
            is_active=True,
            is_public=True,
            created_at=datetime.now() - timedelta(days=100),
            wsproxy_addr="http://proxy-01.backend.ai:5050",
            wsproxy_api_token="mock-token-01",
            driver="cuda",
            driver_opts=cast(JSONString, "{}"),
            scheduler="fifo",
            scheduler_opts=cast(JSONString, "{}"),
            use_host_network=False,
        ),
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
        vfolder=mock_model_vfolder_1,
        mount_destination="/models",
        definition_path="models/llama-3-8b/config.yaml",
    ),
    extra_mounts=ExtraVFolderMountConnection(
        edges=[
            ExtraVFolderMountEdge(node=mock_extra_mount_1, cursor="extra-mount-cursor-1"),
            ExtraVFolderMountEdge(node=mock_extra_mount_2, cursor="extra-mount-cursor-2"),
        ],
        page_info=PageInfo(
            has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
        ),
    ),
    image=Image(
        id=UUID(mock_image_id_1),
        row_id=uuid4(),
        name="cr.backend.ai/pytorch:2.0-cuda12.1",
        namespace="cr.backend.ai",
        base_image_name="pytorch",
        project="inference",
        humanized_name="PyTorch 2.0 Inference",
        tag="2.0-cuda12.1",
        tags=[],
        version="2.0",
        registry="cr.backend.ai",
        architecture="x86_64",
        is_local=False,
        digest="sha256:abcd1234",
        labels=[],
        size_bytes=5000000000,  # type: ignore
        status="available",
        aliases=[],
        permissions=[ImagePermission.READ_ATTRIBUTE],  # type: ignore
        installed=True,
        type=ImageType.COMPUTE,
        resource_limits=[ResourceLimit(key="cuda.device", min="1", max="8")],
        supported_accelerators=["cuda"],
    ),
    created_at=datetime.now() - timedelta(days=10),
)

mock_revision_id_2 = "3c81bc63-24c1-4a8f-9ad2-8a19899690c3"
mock_resource_id_2 = "0cc27c4c-7fa1-49ae-aa53-9c485205c78b"
mock_image_id_2 = "18c39ba3-e9c4-4353-9892-115e557b60a7"
mock_model_revision_2 = ModelRevision(
    id=UUID(mock_revision_id_2),
    name="llama-3-8b-instruct-v1.1",
    cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
    resource_config=ResourceConfig(
        resource_group=ResourceGroup(
            id=UUID(mock_resource_id_2),
            name="gpu-cluster-02",
            description="Secondary GPU cluster for inference",
            is_active=True,
            is_public=False,
            created_at=datetime.now() - timedelta(days=80),
            wsproxy_addr="http://proxy-02.backend.ai:5050",
            wsproxy_api_token="mock-token-02",
            driver="cuda",
            driver_opts=cast(JSONString, "{}"),
            scheduler="lifo",
            scheduler_opts=cast(JSONString, "{}"),
            use_host_network=False,
        ),
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
        vfolder=mock_model_vfolder_2,
        mount_destination="/models",
        definition_path="models/llama-3-8b/config.yaml",
    ),
    extra_mounts=ExtraVFolderMountConnection(
        edges=[
            ExtraVFolderMountEdge(node=mock_extra_mount_1, cursor="extra-mount-cursor-1"),
            ExtraVFolderMountEdge(node=mock_extra_mount_2, cursor="extra-mount-cursor-2"),
        ],
        page_info=PageInfo(
            has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
        ),
    ),
    image=Image(
        id=UUID(mock_image_id_2),
        row_id=uuid4(),
        name="cr.backend.ai/vllm:0.5.0-cuda12.1",
        namespace="cr.backend.ai",
        base_image_name="vllm",
        project="inference",
        humanized_name="vLLM Inference Engine",
        tag="0.5.0-cuda12.1",
        tags=[],
        version="0.5.0",
        registry="cr.backend.ai",
        architecture="x86_64",
        is_local=False,
        digest="sha256:efgh5678",
        labels=[],
        size_bytes=6000000000,  # type: ignore
        status="available",
        aliases=[],
        permissions=[ImagePermission.READ_ATTRIBUTE],  # type: ignore
        installed=True,
        type=ImageType.COMPUTE,
        resource_limits=[ResourceLimit(key="cuda.device", min="1", max="16")],
        supported_accelerators=["cuda", "rocm"],
    ),
    created_at=datetime.now() - timedelta(days=5),
)


mock_revision_id_3 = "86d1a714-b177-4851-897f-da36f306fe30"
mock_resource_id_3 = "135f7fd4-60fc-4b0d-9913-f3497d730b31"
mock_image_id_3 = "7b6ffbda-a0f4-48da-b589-b9889d33e5e9"
mock_model_revision_3 = ModelRevision(
    id=UUID(mock_revision_id_3),
    name="mistral-7b-v0.3-initial",
    cluster_config=ClusterConfig(mode=ClusterMode.SINGLE_NODE, size=1),
    resource_config=ResourceConfig(
        resource_group=ResourceGroup(
            id=UUID(mock_resource_id_3),
            name="cpu-cluster-01",
            description="CPU cluster for development",
            is_active=True,
            is_public=True,
            created_at=datetime.now() - timedelta(days=60),
            wsproxy_addr="http://proxy-03.backend.ai:5050",
            wsproxy_api_token="mock-token-03",
            driver="cpu",
            driver_opts=cast(JSONString, "{}"),
            scheduler="drf",
            scheduler_opts=cast(JSONString, "{}"),
            use_host_network=False,
        ),
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
        vfolder=mock_model_vfolder_3,
        mount_destination="/models",
        definition_path="models/mistral-7b/config.yaml",
    ),
    extra_mounts=ExtraVFolderMountConnection(
        edges=[],
        page_info=PageInfo(
            has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
        ),
    ),
    image=Image(
        id=UUID(mock_image_id_3),
        row_id=uuid4(),
        name="cr.backend.ai/vllm:0.5.0-cuda12.1",
        namespace="cr.backend.ai",
        base_image_name="vllm",
        project="inference",
        humanized_name="vLLM Inference Runtime",
        tag="0.5.0-cuda12.1",
        tags=[],
        version="0.5.0",
        registry="cr.backend.ai",
        architecture="x86_64",
        is_local=True,
        digest="sha256:ijkl9012",
        labels=[],
        size_bytes=4500000000,  # type: ignore
        status="available",
        aliases=[],
        permissions=[ImagePermission.READ_ATTRIBUTE],  # type: ignore
        installed=True,
        type=ImageType.COMPUTE,
        resource_limits=[ResourceLimit(key="cpu", min="4", max="64")],
        supported_accelerators=["cuda"],
    ),
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
async def inference_runtime_configs() -> JSON:
    all_configs = {
        "vllm": VLLMRuntimeConfig.to_json_schema(),
        "sglang": SGLangRuntimeConfig.to_json_schema(),
        "nvdianim": NVDIANIMRuntimeConfig.to_json_schema(),
        "mojo": MOJORuntimeConfig.to_json_schema(),
    }

    return all_configs


@strawberry.relay.connection(ModelRevisionConnection, description="Added in 25.13.0")
async def revisions(
    filter: Optional[ModelRevisionFilter] = None,
    order: Optional[ModelRevisionOrder] = None,
    first: Optional[int] = None,
    after: Optional[str] = None,
) -> list[ModelRevision]:
    """List revisions with optional filtering and pagination."""
    return [mock_model_revision_1, mock_model_revision_2, mock_model_revision_3]


@strawberry.field(description="Added in 25.13.0")
async def revision(id: ID) -> Optional[ModelRevision]:
    """Get a specific revision by ID."""
    return mock_model_revision_1


@strawberry.mutation(description="Added in 25.13.0")
async def create_model_revision(input: CreateModelRevisionInput) -> CreateModelRevisionPayload:
    """Create a new model revision."""
    revision = ModelRevision(
        id=UUID("4cc91efb-7297-47ec-80c4-6e9c4378ae8b"),
        name=_generate_random_name(),
        cluster_config=ClusterConfig(
            mode=ClusterMode.SINGLE_NODE,
            size=1,
        ),
        resource_config=ResourceConfig(
            resource_group=ResourceGroup(
                id=UUID("f4ea16a1-d6cf-41b2-ad0a-d2093658ec59"),
                name="default-cluster",
                description="Default resource group",
                is_active=True,
                is_public=True,
                created_at=datetime.now(),
                wsproxy_addr="http://proxy.backend.ai:5050",
                wsproxy_api_token="default-token",
                driver="auto",
                driver_opts=cast(JSONString, "{}"),
                scheduler="fifo",
                scheduler_opts=cast(JSONString, "{}"),
                use_host_network=False,
            ),
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
            vfolder=mock_model_vfolder_4,
            mount_destination="/models",
            definition_path="model.yaml",
        ),
        extra_mounts=ExtraVFolderMountConnection(
            edges=[],
            page_info=PageInfo(
                has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
            ),
        ),
        image=Image(
            id=UUID("3e52a88d-5ad1-4f72-83d0-d372a23b2a76"),
            row_id=uuid4(),
            name="cr.backend.ai/inference:latest",
            namespace="cr.backend.ai",
            base_image_name="inference",
            project="default",
            humanized_name="Default Inference Image",
            tag="latest",
            tags=[],
            version="1.0.0",
            registry="cr.backend.ai",
            architecture="x86_64",
            is_local=False,
            digest="sha256:abcdef123456",
            labels=[],
            size_bytes=1000000000,  # type: ignore
            status="available",
            aliases=[],
            permissions=[ImagePermission.READ_ATTRIBUTE],  # type: ignore
            installed=True,
            type=ImageType.COMPUTE,
            resource_limits=[],
            supported_accelerators=[],
        ),
        created_at=datetime.now(),
    )
    return CreateModelRevisionPayload(revision=revision)


@strawberry.mutation(description="Added in 25.13.0")
async def add_model_revision(input: AddModelRevisionInput) -> AddModelRevisionPayload:
    """Add a model revision to a deployment."""
    revision = ModelRevision(
        id=UUID("dda405f0-6463-45c4-a5ca-3721cc8d730c"),
        name=_generate_random_name(),
        cluster_config=ClusterConfig(
            mode=ClusterMode.SINGLE_NODE,
            size=1,
        ),
        resource_config=ResourceConfig(
            resource_group=ResourceGroup(
                id=UUID("b2a2c037-f45f-4945-91fb-1b4ff90b0939"),
                name="default-cluster",
                description="Default resource group",
                is_active=True,
                is_public=True,
                created_at=datetime.now(),
                wsproxy_addr="http://proxy.backend.ai:5050",
                wsproxy_api_token="default-token",
                driver="auto",
                driver_opts=cast(JSONString, "{}"),
                scheduler="fifo",
                scheduler_opts=cast(JSONString, "{}"),
                use_host_network=False,
            ),
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
            vfolder=mock_model_vfolder_5,
            mount_destination="/models",
            definition_path="model.yaml",
        ),
        extra_mounts=ExtraVFolderMountConnection(
            edges=[],
            page_info=PageInfo(
                has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
            ),
        ),
        image=Image(
            id=UUID("7be39d9a-a7a6-4101-a0fa-5689ce41f5de"),
            row_id=uuid4(),
            name="cr.backend.ai/inference:latest",
            namespace="cr.backend.ai",
            base_image_name="inference",
            project="default",
            humanized_name="Default Inference Image",
            tag="latest",
            tags=[],
            version="1.0.0",
            registry="cr.backend.ai",
            architecture="x86_64",
            is_local=False,
            digest="sha256:abcdef123456",
            labels=[],
            size_bytes=1000000000,  # type: ignore
            status="available",
            aliases=[],
            permissions=[ImagePermission.READ_ATTRIBUTE],  # type: ignore
            installed=True,
            type=ImageType.COMPUTE,
            resource_limits=[],
            supported_accelerators=[],
        ),
        created_at=datetime.now(),
    )
    return AddModelRevisionPayload(revision=revision)
