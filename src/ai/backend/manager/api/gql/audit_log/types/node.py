"""AuditLog GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, cast
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.audit_log.response import AuditLogNode
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL


@gql_enum(
    BackendAIGQLMeta(added_version="26.3.0", description="Status of an audit log entry."),
    name="AuditLogStatus",
)
class AuditLogStatusGQL(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    UNKNOWN = "unknown"
    RUNNING = "running"


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Represents an audit log entry tracking system operations.",
    ),
    name="AuditLogV2",
)
class AuditLogV2GQL(PydanticNodeMixin[AuditLogNode]):
    id: NodeID[str] = gql_field(description="Unique identifier of the audit log entry (UUID).")

    action_id: UUID = gql_field(description="UUID of the action that generated this log.")
    entity_type: str = gql_field(description="Type of entity this log relates to.")
    operation: str = gql_field(description="Operation performed (create, update, delete, etc.).")
    entity_id: str | None = gql_field(description="ID of the affected entity, if applicable.")
    created_at: datetime = gql_field(description="Timestamp when the audit log was created.")
    request_id: str | None = gql_field(description="Request ID that triggered this operation.")
    triggered_by: str | None = gql_field(
        description="UUID string of the user who triggered the action."
    )
    description: str = gql_field(description="Human-readable description of the operation.")
    duration: str | None = gql_field(
        description="Duration of the operation as a string representation."
    )
    status: AuditLogStatusGQL = gql_field(description="Status of the operation.")

    @gql_field(
        description="The user who triggered this audit log entry, resolved from triggered_by UUID."
    )  # type: ignore[misc]
    async def user(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            UserV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        if self.triggered_by is None:
            return None
        try:
            user_uuid = UUID(self.triggered_by)
        except ValueError:
            return None
        user_data = await info.context.data_loaders.user_loader.load(user_uuid)
        if user_data is None:
            return None
        return user_data

    @classmethod
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.audit_log_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


AuditLogV2EdgeGQL = Edge[AuditLogV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Connection type for paginated audit log results.",
    ),
    name="AuditLogV2Connection",
)
class AuditLogV2ConnectionGQL(Connection[AuditLogV2GQL]):
    count: int = gql_field(description="Total number of audit log entries matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
