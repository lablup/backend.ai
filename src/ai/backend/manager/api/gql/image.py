"""
Federated Image (ImageNode) type with full field definitions for Strawberry GraphQL.
"""

from decimal import Decimal
from typing import Self
from uuid import UUID, uuid4

import strawberry
from strawberry.federation.schema_directives import Shareable
from strawberry.relay import Node, NodeID

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.rbac.permission_defs import (
    ImagePermission,
)
from ai.backend.manager.services.image.actions.get_image_by_id import GetImageByIdAction

from .base import BigInt, ImagePermissionValueField


@strawberry.type(directives=[Shareable()])
class KVPair:
    key: str
    value: str


@strawberry.type(directives=[Shareable()])
class ResourceLimit:
    key: str
    min: str
    max: str


@strawberry.type(name="ImageDetail")
class Image(Node):
    id: NodeID[str]

    row_id: UUID
    name: str
    namespace: str
    base_image_name: str
    project: str
    humanized_name: str
    tag: str
    tags: list[KVPair]
    version: str
    registry: str
    architecture: str
    is_local: bool
    digest: str
    labels: list[KVPair]
    size_bytes: BigInt
    status: str
    resource_limits: list[ResourceLimit]
    supported_accelerators: list[str]
    aliases: list[str]

    permissions: list[ImagePermissionValueField]
    installed: bool
    type: ImageType

    @classmethod
    async def from_row(cls, ctx: StrawberryGQLContext, row: ImageRow) -> Self:
        # hide_agents = False if is_superadmin else ctx.config_provider.config.manager.hide_agents
        _installed_agents = await ctx.valkey_image.get_agents_for_image(row.name)
        installed_agents: list[str] = list(_installed_agents)
        image_ref = row.image_ref
        version, ptag_set = image_ref.tag_set
        return cls(
            id=row.id,
            row_id=row.id,
            name=row.image,
            namespace=row.image,
            base_image_name=image_ref.name,
            project=row.project,
            humanized_name=row.image,
            tag=row.tag,
            tags=[KVPair(key=k, value=v) for k, v in ptag_set.items()],
            version=version,
            registry=row.registry,
            architecture=row.architecture,
            is_local=row.is_local,
            digest=row.trimmed_digest or "",
            labels=[KVPair(key=k, value=v) for k, v in row.labels.items()],
            aliases=[alias_row.alias for alias_row in row.aliases],
            size_bytes=row.size_bytes,
            status=row.status,
            resource_limits=[
                ResourceLimit(
                    key=k,
                    min=v.get("min", Decimal(0)),
                    max=v.get("max", Decimal("Infinity")),
                )
                for k, v in row.resources.items()
            ],
            supported_accelerators=(row.accelerators or "").split(","),
            installed=len(installed_agents) > 0,
            # Need to be fixed
            permissions=[],
            type=ImageType(row.type),
        )

    @classmethod
    async def load_by_id(cls, ctx: StrawberryGQLContext, image_id: UUID) -> "Image":
        action_result = await ctx.processors.image.get_image_by_id.wait_for_complete(
            GetImageByIdAction(image_id=image_id)
        )

        return await Image.from_row(ctx, ImageRow.from_dataclass(action_result.image))


mock_image_1: Image = Image(
    id="7609ac08-d5e0-410a-a045-10c42119ed21",
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
)

mock_image_2: Image = Image(
    id="18c39ba3-e9c4-4353-9892-115e557b60a7",
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
)

mock_image_3: Image = Image(
    id="7b6ffbda-a0f4-48da-b589-b9889d33e5e9",
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
)

mock_image_4 = Image(
    id="3e52a88d-5ad1-4f72-83d0-d372a23b2a76",
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
)

mock_image_5 = Image(
    id="7be39d9a-a7a6-4101-a0fa-5689ce41f5de",
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
)
