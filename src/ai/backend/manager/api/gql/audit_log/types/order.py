"""AuditLog GraphQL order types."""

from __future__ import annotations

from enum import StrEnum

import strawberry

from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.types import GQLOrderBy
from ai.backend.manager.repositories.audit_log.options import AuditLogOrders
from ai.backend.manager.repositories.base import QueryOrder


@strawberry.enum(
    name="AuditLogOrderField",
    description="Fields available for ordering audit logs.",
)
class AuditLogOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    ENTITY_TYPE = "entity_type"
    OPERATION = "operation"
    STATUS = "status"


@strawberry.input(
    name="AuditLogOrderBy",
    description="Ordering specification for audit logs.",
)
class AuditLogOrderByGQL(GQLOrderBy):
    field: AuditLogOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case AuditLogOrderFieldGQL.CREATED_AT:
                return AuditLogOrders.created_at(ascending)
            case AuditLogOrderFieldGQL.ENTITY_TYPE:
                return AuditLogOrders.entity_type(ascending)
            case AuditLogOrderFieldGQL.OPERATION:
                return AuditLogOrders.operation(ascending)
            case AuditLogOrderFieldGQL.STATUS:
                return AuditLogOrders.status(ascending)
            case _:
                raise ValueError(f"Unhandled AuditLogOrderFieldGQL value: {self.field!r}")
