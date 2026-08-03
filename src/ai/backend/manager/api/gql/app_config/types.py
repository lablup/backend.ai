"""GraphQL types for the merged app config view."""

from __future__ import annotations

from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.app_config.response import AppConfigNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config_fragment.types import AppConfigFragmentGQL
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
    config_name: str = gql_field(description="Config name this merged view is for.")
    merged_config: JSON = gql_field(
        description=(
            "Deep-merged config in ascending allow-list rank order. Empty when nothing "
            "visible to the caller contributes, or when every contributing fragment was empty."
        )
    )
    fragments: list[AppConfigFragmentGQL] = gql_field(
        description="The fragments that contributed, in ascending allow-list rank order."
    )
