"""AuditLog GraphQL filter types."""

from __future__ import annotations

from typing import Self

import strawberry

from ai.backend.common.dto.manager.v2.audit_log.request import (
    AuditLogFilter,
    AuditLogStatusFilter,
)
from ai.backend.common.dto.manager.v2.audit_log.types import AuditLogStatus
from ai.backend.manager.api.gql.base import DateTimeFilter, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_input,
)

from .node import AuditLogStatusGQL


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for audit log status field.", added_version="24.09.0"),
    model=AuditLogStatusFilter,
    name="AuditLogStatusFilter",
)
class AuditLogStatusFilterGQL:
    in_: list[AuditLogStatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[AuditLogStatusGQL] | None = None

    def to_pydantic(self) -> AuditLogStatusFilter:
        return AuditLogStatusFilter(
            in_=[AuditLogStatus(s) for s in self.in_] if self.in_ else None,
            not_in=[AuditLogStatus(s) for s in self.not_in] if self.not_in else None,
        )


@strawberry.input(
    name="AuditLogFilter",
    description="Added in 24.09.0. Filter criteria for querying audit logs.",
)
class AuditLogFilterGQL:
    entity_type: StringFilter | None = None
    operation: StringFilter | None = None
    status: AuditLogStatusFilterGQL | None = None
    created_at: DateTimeFilter | None = None
    triggered_by: StringFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None

    def to_pydantic(self) -> AuditLogFilter:
        return AuditLogFilter(
            entity_type=self.entity_type.to_pydantic() if self.entity_type else None,
            operation=self.operation.to_pydantic() if self.operation else None,
            status=self.status.to_pydantic() if self.status else None,
            created_at=self.created_at.to_pydantic() if self.created_at else None,
            triggered_by=self.triggered_by.to_pydantic() if self.triggered_by else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )
