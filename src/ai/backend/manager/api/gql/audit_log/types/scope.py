"""AuditLog GraphQL scope input types."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.audit_log.request import AuditLogScope
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin
from ai.backend.manager.api.gql.rbac.types.scope import EntityTypeScopeGQL


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Scope target for the scoped audit log query. "
            "All items are OR'd; raises an error if every field is empty."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AuditLogScope",
)
class AuditLogScopeGQL(PydanticInputMixin[AuditLogScope]):
    entity: list[EntityTypeScopeGQL] | None = gql_field(
        description="Entity-tagged scope items.",
        default=None,
    )
    triggered_user: list[UUID] | None = gql_field(
        description="Actor UUIDs (matches audit_logs.triggered_by).",
        default=None,
    )
