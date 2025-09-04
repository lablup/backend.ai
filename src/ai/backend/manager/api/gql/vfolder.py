from typing import Any
from uuid import uuid4

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID


@strawberry.federation.type(keys=["id"], name="VirtualFolderNode", extend=True)
class VFolder:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> "VFolder":
        return cls(id=id)


mock_vfolder_id = ID("VmlydHVhbEZvbGRlck5vZGU6YmEzMzE5ZGQtMTFmZC00Yjk4LTkzNGMtNjUxYTQ4YTVmMzM0")


@strawberry.type
class ExtraVFolderMount(Node):
    id: NodeID
    mount_destination: str
    vfolder: VFolder


ExtraVFolderMountEdge = Edge[ExtraVFolderMount]


@strawberry.type(description="Added in 25.13.0")
class ExtraVFolderMountConnection(Connection[ExtraVFolderMount]):
    count: int

    def __init__(self, *args, count: int, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.count = count


mock_extra_mount_1 = ExtraVFolderMount(
    id=uuid4(),
    vfolder=VFolder(id=mock_vfolder_id),
    mount_destination="/extra_models/model1",
)

mock_extra_mount_2 = ExtraVFolderMount(
    id=uuid4(),
    vfolder=VFolder(id=mock_vfolder_id),
    mount_destination="/extra_models/model2",
)
