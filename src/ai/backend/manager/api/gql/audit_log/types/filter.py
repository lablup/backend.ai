"""AuditLog GraphQL filter types."""

from __future__ import annotations

from typing import Self

from ai.backend.common.dto.manager.v2.audit_log.request import (
    AuditLogFilter,
    AuditLogStatusFilter,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import DateTimeFilter, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
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
    equals: AuditLogStatusGQL | None = None
    in_: list[AuditLogStatusGQL] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    not_equals: AuditLogStatusGQL | None = gql_field(
        description="Excludes exact status match.", name="notEquals", default=None
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
    entity_id: StringFilter | None = None
    operation: StringFilter | None = None
    status: AuditLogStatusFilterGQL | None = None
    created_at: DateTimeFilter | None = None
    triggered_by: StringFilter | None = None
    acted_as: UUIDFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by acted_as (the effective/acting user UUID).",
        ),
        default=None,
    )

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None
