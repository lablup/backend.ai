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
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_input,
)


@strawberry.enum(
    name="AuditLogOrderField",
    description="Fields available for ordering audit logs.",
)
class AuditLogOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    ENTITY_TYPE = "entity_type"
    OPERATION = "operation"
    STATUS = "status"


@gql_pydantic_input(
    BackendAIGQLMeta(description="Ordering specification for audit logs.", added_version="24.09.0"),
    model=AuditLogOrder,
    name="AuditLogOrderBy",
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
