"""AuditLog GraphQL order types."""

from __future__ import annotations

from enum import StrEnum

import strawberry

from ai.backend.common.dto.manager.v2.audit_log.request import AuditLogOrder
from ai.backend.common.dto.manager.v2.audit_log.types import (
    AuditLogOrderField,
)
from ai.backend.common.dto.manager.v2.audit_log.types import (
    OrderDirection as OrderDirectionDTO,
)
from ai.backend.manager.api.gql.base import OrderDirection


@strawberry.enum(
    name="AuditLogOrderField",
    description="Fields available for ordering audit logs.",
)
class AuditLogOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    ENTITY_TYPE = "entity_type"
    OPERATION = "operation"
    STATUS = "status"


@strawberry.experimental.pydantic.input(
    model=AuditLogOrder,
    name="AuditLogOrderBy",
    description="Ordering specification for audit logs.",
)
class AuditLogOrderByGQL:
    field: AuditLogOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_pydantic(self) -> AuditLogOrder:
        ascending = self.direction == OrderDirection.ASC
        return AuditLogOrder(
            field=AuditLogOrderField(self.field),
            direction=OrderDirectionDTO.ASC if ascending else OrderDirectionDTO.DESC,
        )
