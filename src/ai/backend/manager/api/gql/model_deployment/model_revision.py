from datetime import datetime
from enum import Enum, StrEnum
from typing import Annotated, Any, Optional, cast

import strawberry
from strawberry import ID, Info, relay
from strawberry.relay import Connection, PageInfo
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


# Service Config Union Types
@strawberry.type
class vLLMServiceConfig:
    max_model_length: int
    parallelism: Optional[JSONString] = None
    extra_cli_parameters: Optional[str] = None


@strawberry.type
class SGLangServiceConfig:
    config: JSONString


@strawberry.type
class NVIDIAServiceConfig:
    config: JSONString


@strawberry.type
class MOJOServiceConfig:
    config: JSONString


@strawberry.type
class RawServiceConfig:
    config: JSONString
    extra_cli_parameters: Optional[str] = None


ServiceConfig = Annotated[
    vLLMServiceConfig
    | SGLangServiceConfig
    | NVIDIAServiceConfig
    | MOJOServiceConfig
    | RawServiceConfig,
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

    error_data: Optional[JSONString] = None
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
        return cls(
            edges=[],
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
    return []


@strawberry.field
async def revision(id: ID) -> Optional[ModelRevision]:
    """Get a specific revision by ID."""
    return None


@strawberry.mutation
async def create_model_revision(input: CreateModelRevisionInput) -> CreateModelRevisionPayload:
    """Create a new model revision."""
    revision = ModelRevision(
        id=ID(f"rev-new-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
        name=f"New Model Revision {datetime.now()}",
        cluster_config=ClusterConfig(
            mode=ClusterMode.SINGLE_NODE,
            size=1,
        ),
        resource_config=ResourceConfig(
            resource_group=ResourceGroup(id=ID("rg-id")),
            resource_slots=cast(
                JSONString,
                '{"cpu": 1, "mem": "1G", "extra": {"gpu_type": "A100", "storage": "100GB"}}',
            ),
            resource_opts=cast(
                JSONString,
                '{"shmem": , "extra": {"network": "high_bandwidth", "priority": "high"}}',
            ),
        ),
        model_runtime_config=ModelRuntimeConfig(
            runtime_variant="vllm", service_config=None, environ=None
        ),
        model_vfolder_config=ModelVFolderConfig(
            vfolder=VFolder(id=ID("vf-id")),
            mount_destination="/models",
            definition_path="model.yaml",
        ),
        mounts=[],
        image=Image(id=ID("image-id")),
        error_data=None,
        created_at=datetime.now(),
    )
    return CreateModelRevisionPayload(revision=revision)
