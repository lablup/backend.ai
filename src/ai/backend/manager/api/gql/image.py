"""
Federated Image (ImageNode) type with full field definitions for Strawberry GraphQL.
"""

from uuid import UUID

import strawberry
from strawberry.federation.schema_directives import Shareable
from strawberry.relay import Node, NodeID

from ai.backend.manager.data.image.types import ImageType

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
    id: NodeID  # Inherits from Node

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
