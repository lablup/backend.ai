"""AppConfigPolicy GQL output type."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from ai.backend.common.dto.manager.v2.app_config_policy.response import AppConfigPolicyNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Scoped app-config policy (BEP-1052 §1).",
    ),
    model=AppConfigPolicyNode,
    name="AppConfigPolicy",
)
class AppConfigPolicyGQL(PydanticOutputMixin[AppConfigPolicyNode]):
    id: UUID = gql_field(description="Policy row UUID.")
    config_name: str = gql_field(description="Unique, immutable policy name.")
    scope_sources: list[str] = gql_field(
        description="Ordered scope chain (low → high merge priority).",
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime | None = gql_field(description="Last update timestamp.")
