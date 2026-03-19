"""AuditLog GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.audit_log.response import AuditLogNode
from ai.backend.common.dto.manager.v2.audit_log.types import AuditLogStatus as AuditLogStatusDTO
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.audit_log.types import AuditLogData

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL


@strawberry.enum(
    name="AuditLogStatus",
    description="Status of an audit log entry.",
)
class AuditLogStatusGQL(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    UNKNOWN = "unknown"
    RUNNING = "running"

    @classmethod
    def from_internal(cls, status: OperationStatus) -> AuditLogStatusGQL:
        match status:
            case OperationStatus.SUCCESS:
                return cls.SUCCESS
            case OperationStatus.ERROR:
                return cls.ERROR
            case OperationStatus.UNKNOWN:
                return cls.UNKNOWN
            case OperationStatus.RUNNING:
                return cls.RUNNING
            case _:
                raise ValueError(f"Unhandled OperationStatus: {status!r}")


@strawberry.type(
    name="AuditLogV2",
    description="Represents an audit log entry tracking system operations.",
)
class AuditLogV2GQL(PydanticNodeMixin):
    id: NodeID[str] = strawberry.field(
        description="Unique identifier of the audit log entry (UUID)."
    )

    _triggered_by: strawberry.Private[str | None]

    action_id: UUID = strawberry.field(description="UUID of the action that generated this log.")
    entity_type: str = strawberry.field(description="Type of entity this log relates to.")
    operation: str = strawberry.field(
        description="Operation performed (create, update, delete, etc.)."
    )
    entity_id: str | None = strawberry.field(
        description="ID of the affected entity, if applicable."
    )
    created_at: datetime = strawberry.field(description="Timestamp when the audit log was created.")
    request_id: str | None = strawberry.field(
        description="Request ID that triggered this operation."
    )
    triggered_by: str | None = strawberry.field(
        description="UUID string of the user who triggered the action."
    )
    description: str = strawberry.field(description="Human-readable description of the operation.")
    duration: str | None = strawberry.field(
        description="Duration of the operation as a string representation."
    )
    status: AuditLogStatusGQL = strawberry.field(description="Status of the operation.")

    @strawberry.field(  # type: ignore[misc]
        description="The user who triggered this audit log entry, resolved from triggered_by UUID."
    )
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
        from ai.backend.manager.api.gql.user.types.node import UserV2GQL

        if self._triggered_by is None:
            return None
        try:
            user_uuid = UUID(self._triggered_by)
        except ValueError:
            return None
        user_data = await info.context.data_loaders.user_loader.load(user_uuid)
        if user_data is None:
            return None
        return UserV2GQL.from_data(user_data)

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
        return [cls.from_data(data) if data is not None else None for data in results]

    @classmethod
    def from_data(cls, data: AuditLogData) -> Self:
        return cls(
            id=ID(str(data.id)),
            _triggered_by=data.triggered_by,
            action_id=data.action_id,
            entity_type=data.entity_type,
            operation=data.operation,
            entity_id=data.entity_id,
            created_at=data.created_at,
            request_id=data.request_id,
            triggered_by=data.triggered_by,
            description=data.description,
            duration=str(data.duration) if data.duration is not None else None,
            status=AuditLogStatusGQL.from_internal(data.status),
        )

    @classmethod
    def from_node(cls, node: AuditLogNode) -> Self:
        return cls(
            id=ID(str(node.id)),
            _triggered_by=node.triggered_by,
            action_id=node.action_id,
            entity_type=node.entity_type,
            operation=node.operation,
            entity_id=node.entity_id,
            created_at=node.created_at,
            request_id=node.request_id,
            triggered_by=node.triggered_by,
            description=node.description,
            duration=node.duration,
            status=AuditLogStatusGQL(AuditLogStatusDTO(node.status).value),
        )


AuditLogV2EdgeGQL = Edge[AuditLogV2GQL]


@strawberry.type(
    name="AuditLogV2Connection",
    description="Connection type for paginated audit log results.",
)
class AuditLogV2ConnectionGQL(Connection[AuditLogV2GQL]):
    count: int = strawberry.field(
        description="Total number of audit log entries matching the query."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
