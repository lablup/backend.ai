"""VFolder GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.vfolder.response import VFolderNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.vfolder_v2.types.enum import VFolderOperationStatusGQL

from .nested import (
    VFolderAccessControlInfoGQL,
    VFolderMetadataInfoGQL,
    VFolderOwnershipInfoGQL,
)


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Virtual folder entity with structured field groups. "
            "Provides comprehensive vfolder information organized "
            "into logical categories: metadata (descriptive), permission (access control), "
            "and usage (storage statistics). Owner and creator are resolved as Node references."
        ),
    ),
    name="VFolder",
)
class VFolderGQL(PydanticNodeMixin[VFolderNode]):
    """Virtual folder entity with structured field groups."""

    id: NodeID[str] = gql_field(description="Unique identifier of the virtual folder.")
    status: VFolderOperationStatusGQL = gql_field(
        description=(
            "Current operation status. "
            "READY, CLONING, "
            "DELETE_PENDING, DELETE_ONGOING, DELETE_COMPLETE, or DELETE_ERROR."
        )
    )
    host: str = gql_field(
        description="Storage host where the virtual folder is physically located."
    )
    metadata: VFolderMetadataInfoGQL = gql_field(
        description="Descriptive metadata including name, usage mode, quota scope, timestamps, and clone eligibility."
    )
    access_control: VFolderAccessControlInfoGQL = gql_field(
        description="Access control including permission level and ownership type."
    )
    ownership: VFolderOwnershipInfoGQL = gql_field(
        description=(
            "Ownership context including scalar IDs (userId, projectId, creatorEmail) "
            "and full node resolvers (user, project, creator)."
        )
    )
    unmanaged_path: str | None = gql_field(description="Path for unmanaged virtual folders.")

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: None = None,
        node_ids: Iterable[str] | None = None,
        required: bool = False,
    ) -> Iterable[VFolderGQL | None]:
        # Stub: returns None for each requested ID until a data loader is wired in.
        if node_ids is None:
            return []
        return [None for _ in node_ids]


VFolderEdge = Edge[VFolderGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Paginated connection for virtual folder records. "
            "Provides relay-style cursor-based pagination for efficient traversal of vfolder data. "
            "Use 'edges' to access individual records with cursor information, "
            "or 'nodes' for direct data access."
        ),
    )
)
class VFolderConnection(Connection[VFolderGQL]):
    """Paginated connection for virtual folder records."""

    count: int = gql_field(
        description="Total number of virtual folder records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
