"""AuditLog GraphQL filter types."""

from __future__ import annotations

from typing import Self

from ai.backend.common.dto.manager.v2.audit_log.request import (
    AuditLogFilter,
    AuditLogStatusFilter,
)
from ai.backend.manager.api.gql.base import DateTimeFilter, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

from .node import AuditLogStatusGQL


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for audit log status field.", added_version="24.09.0"),
    name="AuditLogStatusFilter",
)
class AuditLogStatusFilterGQL(PydanticInputMixin[AuditLogStatusFilter]):
    in_: list[AuditLogStatusGQL] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    not_in: list[AuditLogStatusGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter criteria for querying audit logs.", added_version="24.09.0"
    ),
    name="AuditLogFilter",
)
class AuditLogFilterGQL(PydanticInputMixin[AuditLogFilter]):
    entity_type: StringFilter | None = None
    operation: StringFilter | None = None
    status: AuditLogStatusFilterGQL | None = None
    created_at: DateTimeFilter | None = None
    triggered_by: StringFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None
