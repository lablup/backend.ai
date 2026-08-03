"""GraphQL types for the merged app config view."""

from __future__ import annotations

from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.app_config.response import AppConfigNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

__all__ = ("AppConfigGQL",)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "The merged config for one config name: every fragment visible to the caller, "
            "deep-merged in ascending allow-list rank order."
        ),
    ),
    model=AppConfigNode,
    name="AppConfig",
)
class AppConfigGQL(PydanticOutputMixin[AppConfigNode]):
    config_name: str = gql_field(description="Config name this view is for.")
    # Strawberry surfaces the Pydantic field's description, not this one — keep them in step
    # so the SDL and the DTO cannot drift apart.
    config: JSON = gql_field(
        description=(
            "Every fragment visible to the caller, deep-merged in ascending allow-list rank "
            "order. Empty when nothing visible contributes, or when everything that did was "
            "empty. Read the fragment API for the per-scope values behind it."
        )
    )
