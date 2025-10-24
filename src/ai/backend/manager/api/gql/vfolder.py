from typing import Any
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.deployment.types import ExtraVFolderMountData
from ai.backend.manager.models.gql_relay import AsyncNode


@strawberry.federation.type(keys=["id"], name="VirtualFolderNode", extend=True)
class VFolder:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> "VFolder":
        return cls(id=id)


@strawberry.type
class ExtraVFolderMount(Node):
    id: NodeID[str]
    mount_destination: str
    _vfolder_id: strawberry.Private[UUID]

    @strawberry.field
    async def vfolder(self, info: Info[StrawberryGQLContext]) -> VFolder:
        vfolder_global_id = AsyncNode.to_global_id("VirtualFolderNode", self._vfolder_id)
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


@strawberry.type(description="Added in 25.16.0")
class ExtraVFolderMountConnection(Connection[ExtraVFolderMount]):
    count: int

    def __init__(self, *args, count: int, **kwargs: Any):
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
