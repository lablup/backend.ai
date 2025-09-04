import base64
from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Any, Optional, cast
from uuid import uuid4

import strawberry
from strawberry import ID, Info, relay
from strawberry.relay import Connection, Edge, PageInfo
from strawberry.relay.types import NodeIterableType

from ai.backend.manager.api.gql.base import JSONString, OrderDirection, StringFilter
from ai.backend.manager.api.gql.federated_types import Image, VFolder


@strawberry.type
class ModelMountConfig:
    vfolder: VFolder
    mount_destination: str
    definition_path: str


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

    model_runtime_config: ModelRuntimeConfig
    model_mount_config: ModelMountConfig

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
def _generate_mock_global_id() -> str:
    return base64.b64encode(f"default:{uuid4()}".encode("utf-8")).decode()


mock_model_revision_1 = ModelRevision(
    id=_generate_mock_global_id(),
    name="llama-3-8b-instruct-v1.0",
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
    model_mount_config=ModelMountConfig(
        vfolder=VFolder(id=ID(_generate_mock_global_id())),
        mount_destination="/models",
        definition_path="models/llama-3-8b/config.yaml",
    ),
    image=Image(id=ID(_generate_mock_global_id())),
    created_at=datetime.now() - timedelta(days=10),
)

mock_model_revision_2 = ModelRevision(
    id=_generate_mock_global_id(),
    name="llama-3-8b-instruct-v1.1",
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
    model_mount_config=ModelMountConfig(
        vfolder=VFolder(id=ID(_generate_mock_global_id())),
        mount_destination="/models",
        definition_path="models/llama-3-8b/config.yaml",
    ),
    image=Image(id=ID(_generate_mock_global_id())),
    created_at=datetime.now() - timedelta(days=5),
)

mock_model_revision_3 = ModelRevision(
    id=_generate_mock_global_id(),
    name="mistral-7b-v0.3-initial",
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
    model_mount_config=ModelMountConfig(
        vfolder=VFolder(id=ID(_generate_mock_global_id())),
        mount_destination="/models",
        definition_path="models/mistral-7b/config.yaml",
    ),
    image=Image(id=ID(_generate_mock_global_id())),
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
class ModelRuntimeConfigInput:
    runtime_variant: str
    service_config: Optional[JSONString] = None
    environ: Optional[JSONString] = None


@strawberry.input
class ModelMountConfigInput:
    vfolder_id: ID
    mount_destination: str
    definition_path: str


@strawberry.input
class CreateModelRevisionInput:
    deployment_id: ID
    name: str
    image: ImageInput
    model_runtime_config: ModelRuntimeConfigInput
    model_mount_config: ModelMountConfigInput


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
        id=_generate_mock_global_id(),
        name=input.name,
        model_runtime_config=ModelRuntimeConfig(
            runtime_variant=input.model_runtime_config.runtime_variant,
            service_config=None,
            environ=None,
        ),
        model_mount_config=ModelMountConfig(
            vfolder=VFolder(id=ID(_generate_mock_global_id())),
            mount_destination="/models",
            definition_path="model.yaml",
        ),
        image=Image(id=ID(_generate_mock_global_id())),
        created_at=datetime.now(),
    )
    return CreateModelRevisionPayload(revision=revision)
