"""AuditLog GraphQL order types."""

from __future__ import annotations

from enum import StrEnum

import strawberry

from ai.backend.common.dto.manager.v2.audit_log.request import AuditLogOrder
from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


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
    name="AuditLogOrderBy",
)
class AuditLogOrderByGQL(PydanticInputMixin[AuditLogOrder]):
    field: AuditLogOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC
