from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

import strawberry
from strawberry import Info, relay
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo
from strawberry.relay.types import NodeIterableType

from ai.backend.manager.api.gql.base import (
    BigInt,
    VFolderPermissionValueField,
)
from ai.backend.manager.models.rbac.permission_defs import (
    VFolderPermission,
)


@strawberry.type
class VFolder(Node):
    id: NodeID

    row_id: UUID
    host: str
    quota_scope_id: str
    name: str
    user: UUID
    user_email: str
    group: UUID
    group_name: str
    creator: str
    unmanaged_path: str
    usage_mode: str
    permission: str
    ownership_type: str
    max_files: int
    max_size: BigInt
    created_at: datetime
    last_used: datetime

    num_files: int
    cur_size: BigInt
    cloneable: bool
    status: str

    permissions: list[VFolderPermissionValueField]


@strawberry.type
class ExtraVFolderMount(relay.Node):
    id: NodeID
    mount_destination: str
    vfolder: VFolder


ExtraVFolderMountEdge = Edge[ExtraVFolderMount]


@strawberry.type(description="Added in 25.13.0")
class ExtraVFolderMountConnection(Connection[ExtraVFolderMount]):
    @strawberry.field
    def count(self) -> int:
        return 0

    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[ExtraVFolderMount],
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


mock_model_vfolder_1 = VFolder(
    id=UUID("79b7e9e2-37d0-4238-936d-8078f417f383"),
    row_id=uuid4(),
    name="llama-3-8b-model",
    host="storage-01",
    quota_scope_id="default",
    user=uuid4(),
    user_email="user@example.com",
    group=uuid4(),
    group_name="default",
    creator="admin",
    unmanaged_path="",
    usage_mode="model",
    permission="read-only",
    ownership_type="user",
    max_files=1000,
    max_size=50000,  # type: ignore
    created_at=datetime.now() - timedelta(days=30),
    last_used=datetime.now() - timedelta(days=1),
    num_files=10,
    cur_size=45000,  # type: ignore
    cloneable=True,
    status="ready",
    permissions=[VFolderPermission.READ_CONTENT],  # type: ignore
)

mock_model_vfolder_2 = VFolder(
    id=UUID("870b9bac-a9b5-4b5b-a8f2-e78ef727f2c3"),
    row_id=uuid4(),
    name="llama-3-8b-model-v1.1",
    host="storage-02",
    quota_scope_id="default",
    user=uuid4(),
    user_email="user2@example.com",
    group=uuid4(),
    group_name="research",
    creator="admin",
    unmanaged_path="",
    usage_mode="model",
    permission="read-only",
    ownership_type="group",
    max_files=2000,
    max_size=75000,  # type: ignore
    created_at=datetime.now() - timedelta(days=20),
    last_used=datetime.now() - timedelta(hours=12),
    num_files=15,
    cur_size=70000,  # type: ignore
    cloneable=True,
    status="ready",
    permissions=[VFolderPermission.READ_CONTENT],  # type: ignore
)

mock_model_vfolder_3 = VFolder(
    id=UUID("039022f8-c0ed-47e6-9223-cbb1bddd4bd3"),
    row_id=uuid4(),
    name="mistral-7b-model",
    host="storage-03",
    quota_scope_id="default",
    user=uuid4(),
    user_email="user3@example.com",
    group=uuid4(),
    group_name="default",
    creator="admin",
    unmanaged_path="",
    usage_mode="model",
    permission="read-write",
    ownership_type="user",
    max_files=500,
    max_size=25000,  # type: ignore
    created_at=datetime.now() - timedelta(days=7),
    last_used=datetime.now() - timedelta(hours=6),
    num_files=5,
    cur_size=20000,  # type: ignore
    cloneable=True,
    status="ready",
    permissions=[VFolderPermission.READ_CONTENT, VFolderPermission.WRITE_CONTENT],  # type: ignore
)

mock_model_vfolder_4 = VFolder(
    id=UUID("544bd43d-0e3d-4656-a14e-42c185708d8f"),
    row_id=uuid4(),
    name="model-vfolder",
    host="storage-default",
    quota_scope_id="default",
    user=uuid4(),
    user_email="default@example.com",
    group=uuid4(),
    group_name="default",
    creator="system",
    unmanaged_path="",
    usage_mode="model",
    permission="read-only",
    ownership_type="user",
    max_files=1000,
    max_size=100000,  # type: ignore
    created_at=datetime.now(),
    last_used=datetime.now(),
    num_files=1,
    cur_size=1000,  # type: ignore
    cloneable=False,
    status="ready",
    permissions=[VFolderPermission.READ_CONTENT],  # type: ignore
)

mock_model_vfolder_5 = VFolder(
    id=UUID("53d0182b-74fe-41b3-9c1d-c1674ad53653"),
    row_id=uuid4(),
    name="model-vfolder",
    host="storage-default",
    quota_scope_id="default",
    user=uuid4(),
    user_email="default@example.com",
    group=uuid4(),
    group_name="default",
    creator="system",
    unmanaged_path="",
    usage_mode="model",
    permission="read-only",
    ownership_type="user",
    max_files=1000,
    max_size=100000,  # type: ignore
    created_at=datetime.now(),
    last_used=datetime.now(),
    num_files=1,
    cur_size=1000,  # type: ignore
    cloneable=False,
    status="ready",
    permissions=[VFolderPermission.READ_CONTENT],  # type: ignore
)

mock_extra_mount_1 = ExtraVFolderMount(
    id=uuid4(),
    vfolder=mock_model_vfolder_4,
    mount_destination="/extra_models/model1",
)

mock_extra_mount_2 = ExtraVFolderMount(
    id=uuid4(),
    vfolder=mock_model_vfolder_5,
    mount_destination="/extra_models/model2",
)
