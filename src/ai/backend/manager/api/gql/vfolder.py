"""
Federated VFolder (VirtualFolderNode) type with full field definitions for Strawberry GraphQL.
"""

from datetime import datetime
from uuid import UUID

import strawberry
from strawberry.relay import Node, NodeID

from ai.backend.manager.api.gql.base import (
    BigInt,
    VFolderPermissionValueField,
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
