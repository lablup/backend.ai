from typing import Any

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_federation_type,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql_legacy.gql_relay import AsyncNode


@gql_federation_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Federation stub for legacy VirtualFolderNode.",
    ),
    name="VirtualFolderNode",
    keys=["id"],
    extend=True,
)
class VFolder:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> "VFolder":
        return cls(id=id)


@gql_node_type(
    BackendAIGQLMeta(
        added_version="24.3.0",
        description="Represents a virtual folder mount in a deployment.",
    ),
)
class ExtraVFolderMount(PydanticNodeMixin[Any]):
    id: NodeID[str]
    mount_destination: str
    vfolder_id: ID

    @gql_field(description="The vfolder of this entity.")  # type: ignore[misc]
    async def vfolder(self, info: Info[StrawberryGQLContext]) -> VFolder:
        vfolder_global_id = AsyncNode.to_global_id("VirtualFolderNode", str(self.vfolder_id))
        return VFolder(id=ID(vfolder_global_id))


ExtraVFolderMountEdge = Edge[ExtraVFolderMount]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Connection type for paginated virtual folder mount results.",
    ),
)
class ExtraVFolderMountConnection(Connection[ExtraVFolderMount]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
