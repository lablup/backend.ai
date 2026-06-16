"""AppConfig (merged view) GraphQL scope input types."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.app_config.request import AppConfigScope
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Scope for the scoped merged-view AppConfig query. "
            "`userIds` are OR'd; raises an error when empty."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AppConfigScope",
)
class AppConfigScopeGQL(PydanticInputMixin[AppConfigScope]):
    user_ids: list[UUID] = gql_field(
        description="Target user UUIDs to scope the merged-view search to (OR'd).",
    )
