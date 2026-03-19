from typing import Any
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID, PageInfo

from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql_legacy.gql_relay import AsyncNode
from ai.backend.manager.data.deployment.types import ExtraVFolderMountData


@strawberry.federation.type(keys=["id"], name="VirtualFolderNode", extend=True)
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
    _vfolder_id: strawberry.Private[UUID]

    @strawberry.field
    async def vfolder(self, info: Info[StrawberryGQLContext]) -> VFolder:
        vfolder_global_id = AsyncNode.to_global_id("VirtualFolderNode", str(self._vfolder_id))
        return VFolder(id=ID(vfolder_global_id))

    @classmethod
    def from_dataclass(cls, data: ExtraVFolderMountData) -> "ExtraVFolderMount":
        return cls(
            # TODO: fix id generation logic
            id=ID(f"{data.vfolder_id}:{data.mount_destination}"),
            mount_destination=data.mount_destination,
            _vfolder_id=data.vfolder_id,
        )


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

    @classmethod
    def from_dataclass(
        cls, mounts_data: list[ExtraVFolderMountData]
    ) -> "ExtraVFolderMountConnection":
        nodes = [ExtraVFolderMount.from_dataclass(data) for data in mounts_data]
        edges = [Edge(node=node, cursor=str(node.id)) for node in nodes]
        page_info = PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        )

        return cls(count=len(nodes), edges=edges, page_info=page_info)
