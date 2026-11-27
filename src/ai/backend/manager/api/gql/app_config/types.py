"""GraphQL types for the merged app config view."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import strawberry
from strawberry.federation.schema_directives import Shareable
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.app_config.response import AppConfigNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
    gql_resolver,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

__all__ = ("AppConfigGQL",)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.9.0",
        description=(
            "The merged config for one config name: every fragment visible to the caller, "
            "deep-merged in ascending allow-list rank order."
        ),
    ),
    model=AppConfigNode,
    name="AppConfig",
    directives=[Shareable()],
)
class AppConfigGQL(PydanticOutputMixin[AppConfigNode]):
    config_name: str = gql_field(description="Config name this view is for.")

    if TYPE_CHECKING:
        # Set by Strawberry's ``from_pydantic``; the resolver below reads the merge from it.
        _original_model: AppConfigNode

    @gql_resolver(
        description=(
            "Every fragment visible to the caller, deep-merged in ascending allow-list rank "
            "order. Empty when nothing visible contributes, or when everything that did was "
            "empty. Read the fragment API for the per-scope values behind it."
        ),
        name="config",
    )
    def config_by_keys(
        self,
        keys: Annotated[
            list[str] | None,
            strawberry.argument(
                description=(
                    f"Added in {NEXT_RELEASE_VERSION}. Only these top-level keys of the merge "
                    "are returned; a key no visible fragment holds is left out. All keys when "
                    "null."
                )
            ),
        ] = None,
    ) -> JSON:
        merged = self._original_model.config
        if keys is None:
            return merged
        return {key: merged[key] for key in keys if key in merged}
