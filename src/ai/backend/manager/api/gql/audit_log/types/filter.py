"""AuditLog GraphQL filter types."""

from __future__ import annotations

import strawberry

from ai.backend.manager.api.gql.base import DateTimeFilter, StringFilter
from ai.backend.manager.api.gql.types import GQLFilter
from ai.backend.manager.repositories.audit_log.options import AuditLogConditions
from ai.backend.manager.repositories.base import QueryCondition

from .node import AuditLogStatusGQL


@strawberry.input(
    name="AuditLogStatusFilter",
    description="Filter for audit log status field.",
)
class AuditLogStatusFilterGQL:
    in_: list[AuditLogStatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[AuditLogStatusGQL] | None = None

    def build_condition(self) -> QueryCondition | None:
        if self.in_:
            return AuditLogConditions.by_status_in(self.in_)
        if self.not_in:
            return AuditLogConditions.by_status_not_in(self.not_in)
        return None


@strawberry.input(
    name="AuditLogFilter",
    description="Filter criteria for querying audit logs.",
)
class AuditLogFilterGQL(GQLFilter):
    entity_type: StringFilter | None = None
    operation: StringFilter | None = None
    status: AuditLogStatusFilterGQL | None = None
    created_at: DateTimeFilter | None = None
    triggered_by: StringFilter | None = None

    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if self.entity_type:
            condition = self.entity_type.build_query_condition(
                contains_factory=AuditLogConditions.by_entity_type_contains,
                equals_factory=AuditLogConditions.by_entity_type_equals,
                starts_with_factory=AuditLogConditions.by_entity_type_starts_with,
                ends_with_factory=AuditLogConditions.by_entity_type_ends_with,
            )
            if condition:
                conditions.append(condition)
        if self.operation:
            condition = self.operation.build_query_condition(
                contains_factory=AuditLogConditions.by_operation_contains,
                equals_factory=AuditLogConditions.by_operation_equals,
                starts_with_factory=AuditLogConditions.by_operation_starts_with,
                ends_with_factory=AuditLogConditions.by_operation_ends_with,
            )
            if condition:
                conditions.append(condition)
        if self.status:
            condition = self.status.build_condition()
            if condition:
                conditions.append(condition)
        if self.created_at:
            condition = self.created_at.build_query_condition(
                before_factory=AuditLogConditions.by_created_at_before,
                after_factory=AuditLogConditions.by_created_at_after,
            )
            if condition:
                conditions.append(condition)
        if self.triggered_by:
            condition = self.triggered_by.build_query_condition(
                contains_factory=AuditLogConditions.by_triggered_by_contains,
                equals_factory=AuditLogConditions.by_triggered_by_equals,
                starts_with_factory=AuditLogConditions.by_triggered_by_starts_with,
                ends_with_factory=AuditLogConditions.by_triggered_by_ends_with,
            )
            if condition:
                conditions.append(condition)
        return conditions
