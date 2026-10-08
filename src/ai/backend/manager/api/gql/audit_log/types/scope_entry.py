"""AuditLog scope entry GraphQL types: the scopes one audit log recorded."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.dto.manager.v2.audit_log.request import (
    AuditLogScopeFilter,
    AuditLogScopeOrder,
)
from ai.backend.common.dto.manager.v2.audit_log.response import AuditLogScopeEntryNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.audit_log.types.node import AuditLogV2GQL
    from ai.backend.manager.api.gql.rbac.types.entity_node import EntityNodeGQL

__all__ = (
    "AuditLogScopeEntryConnectionGQL",
    "AuditLogScopeEntryEdgeGQL",
    "AuditLogScopeEntryFilterGQL",
    "AuditLogScopeEntryGQL",
    "AuditLogScopeEntryOrderByGQL",
    "AuditLogScopeEntryOrderFieldGQL",
)


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A scope the operation an audit log entry records covered.",
    ),
    name="AuditLogScopeEntry",
)
class AuditLogScopeEntryGQL(PydanticNodeMixin[AuditLogScopeEntryNode]):
    id: NodeID[str] = gql_field(description="Audit log scope entry ID (UUID).")
    field_id: UUID = gql_field(description="UUID of the audit log scope record.")
    audit_log_id: UUID = gql_field(description="UUID of the audit log the scope belongs to.")
    scope_type: str = gql_field(description="Entity type of the scope.")
    scope_id: UUID = gql_field(description="ID of the scope entity.")

    @gql_field(description="The scope entity. Null when it no longer exists.")  # type: ignore[misc]
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
        return await info.context.data_loaders.entity_node_loader.load(
            RuntimeEntityID(EntityType(self.scope_type), self.scope_id)
        )

    @gql_field(description="The audit log the scope belongs to.")  # type: ignore[misc]
    async def audit_log(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            AuditLogV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.audit_log.types.node"),
        ]
        | None
    ):
        return await info.context.data_loaders.audit_log_loader.load(AuditLogID(self.audit_log_id))


AuditLogScopeEntryEdgeGQL = Edge[AuditLogScopeEntryGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Connection type for the scopes of an audit log.",
    ),
    name="AuditLogScopeEntryConnection",
)
class AuditLogScopeEntryConnectionGQL(Connection[AuditLogScopeEntryGQL]):
    count: int = gql_field(description="Total number of scopes matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for the scopes of an audit log.",
    ),
    name="AuditLogScopeEntryFilter",
)
class AuditLogScopeEntryFilterGQL(PydanticInputMixin[AuditLogScopeFilter]):
    scope_type: StringFilter | None = gql_field(description="Scope type filter.", default=None)
    scope_id: UUIDFilter | None = gql_field(description="Scope ID filter.", default=None)


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering the scopes of an audit log.",
    ),
    name="AuditLogScopeEntryOrderField",
)
class AuditLogScopeEntryOrderFieldGQL(StrEnum):
    SCOPE_TYPE = "scope_type"
    SCOPE_ID = "scope_id"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Ordering specification for the scopes of an audit log.",
    ),
    name="AuditLogScopeEntryOrderBy",
)
class AuditLogScopeEntryOrderByGQL(PydanticInputMixin[AuditLogScopeOrder]):
    field: AuditLogScopeEntryOrderFieldGQL = gql_field(description="Field to order by.")
    direction: OrderDirection = gql_field(
        description="Order direction.", default=OrderDirection.ASC
    )
