"""AuditLog GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, cast, override
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID, PageInfo

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.audit_log.request import SearchAuditLogScopesInput
from ai.backend.common.dto.manager.v2.audit_log.response import AuditLogNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.audit_log.types.scope_entry import (
    AuditLogScopeEntryConnectionGQL,
    AuditLogScopeEntryEdgeGQL,
    AuditLogScopeEntryFilterGQL,
    AuditLogScopeEntryGQL,
    AuditLogScopeEntryOrderByGQL,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.rbac.types.entity_node import EntityNodeGQL
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL


_ENTITY_ID_DEPRECATION = (
    f"Deprecated since {NEXT_RELEASE_VERSION}. Use `targetEntityId`, which carries the id as "
    "a UUID."
)


@gql_enum(
    BackendAIGQLMeta(added_version="26.3.0", description="Status of an audit log entry."),
    name="AuditLogStatus",
)
class AuditLogStatusGQL(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    UNKNOWN = "unknown"
    RUNNING = "running"
    DENIED = "denied"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Shape of the action that wrote an audit log entry.",
    ),
    name="AuditLogActionKind",
)
class AuditLogActionKindGQL(StrEnum):
    SINGLE_ENTITY = "single_entity"
    BULK = "bulk"
    SCOPE = "scope"
    RELATION = "relation"
    MEMBERSHIP = "membership"
    GLOBAL = "global"
    LOOKUP = "lookup"


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Represents an audit log entry tracking system operations.",
    ),
    name="AuditLogV2",
)
class AuditLogV2GQL(PydanticNodeMixin[AuditLogNode]):
    id: NodeID[str] = gql_field(description="Unique identifier of the audit log entry (UUID).")
    field_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="UUID of the audit log record.",
        ),
    )

    action_id: UUID = gql_field(description="UUID of the action that generated this log.")
    action_name: str = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Name of the action that wrote this log.",
        ),
    )
    action_kind: AuditLogActionKindGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "Shape of the action that wrote this log. "
                "Null for a log written before the action kind was recorded."
            ),
        ),
        default=None,
    )
    lookup_kind: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=("Kind of natural key a lookup action read. Null for other action kinds."),
        ),
        default=None,
    )
    lookup_key: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Natural key a lookup action read. Null for other action kinds.",
        ),
        default=None,
    )
    entity_type: str | None = gql_field(
        description=(
            "Type of entity this log relates to. Null for an operation that names "
            "scopes and no entity kind, such as linking two entities."
        )
    )
    operation: str = gql_field(description="Operation performed (create, update, delete, etc.).")
    entity_id: str | None = gql_field(
        description="ID of the affected entity, if applicable.",
        deprecation_reason=_ENTITY_ID_DEPRECATION,
    )
    target_entity_id: UUID | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="ID of the affected entity, if applicable.",
        ),
        default=None,
    )
    created_at: datetime = gql_field(description="Timestamp when the audit log was created.")
    request_id: str | None = gql_field(description="Request ID that triggered this operation.")
    triggered_by: str | None = gql_field(
        description="UUID string of the user who triggered the action."
    )
    acted_as: UUID | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.8.0",
            description=(
                "UUID of the effective (acting) user the action ran as. "
                "Differs from triggered_by only while a super admin is impersonating a target."
            ),
        ),
        default=None,
    )
    description: str = gql_field(description="Human-readable description of the operation.")
    duration: str | None = gql_field(
        description="Duration of the operation as a string representation."
    )
    status: AuditLogStatusGQL = gql_field(description="Status of the operation.")
    client_ip: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "IP address of the request that produced this record, masked per the client "
                "IP masking policy. Null when the policy records none, or when the address "
                "was unavailable or unusable."
            ),
        )
    )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "The entity the logged operation acted on. Null when the log names no entity, "
                "or when the recorded id does not name one that still exists."
            ),
        )
    )  # type: ignore[misc]
    async def entity(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            EntityNodeGQL,
            strawberry.lazy("ai.backend.manager.api.gql.rbac.types.entity_node"),
        ]
        | None
    ):
        if self.entity_type is None or self.target_entity_id is None:
            return None
        return await info.context.data_loaders.entity_node_loader.load(
            RuntimeEntityID(EntityType(self.entity_type), self.target_entity_id)
        )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "The scopes the logged operation covered. Empty for an action kind that "
                "records no scope."
            ),
        )
    )  # type: ignore[misc]
    async def scopes(
        self,
        info: Info[StrawberryGQLContext],
        filter: AuditLogScopeEntryFilterGQL | None = None,
        order_by: list[AuditLogScopeEntryOrderByGQL] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AuditLogScopeEntryConnectionGQL:
        payload = await info.context.adapters.audit_log.search_scopes(
            AuditLogID(self.field_id),
            SearchAuditLogScopesInput(
                filter=filter.to_pydantic() if filter else None,
                order=[o.to_pydantic() for o in order_by] if order_by else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        edges = [
            AuditLogScopeEntryEdgeGQL(
                node=AuditLogScopeEntryGQL.from_pydantic(item),
                cursor=encode_cursor(str(item.id)),
            )
            for item in payload.items
        ]
        return AuditLogScopeEntryConnectionGQL(
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )

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
        user_data = await info.context.data_loaders.user_loader.load(UserID(user_uuid))
        if user_data is None:
            return None
        return user_data

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.8.0",
            description=(
                "The effective (acting) user the action ran as, resolved from acted_as UUID. "
                "Differs from user only while a super admin is impersonating a target."
            ),
        )
    )  # type: ignore[misc]
    async def actor(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            UserV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        if self.acted_as is None:
            return None
        user_data = await info.context.data_loaders.user_loader.load(UserID(self.acted_as))
        if user_data is None:
            return None
        return user_data

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.audit_log_loader.load_many([
            AuditLogID(UUID(nid)) for nid in node_ids
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
