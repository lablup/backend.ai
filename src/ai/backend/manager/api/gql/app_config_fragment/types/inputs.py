"""AppConfigFragment GQL natural-key input shared by bulk types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentKeyInput as AppConfigFragmentKeyInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import AppConfigScopeType
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Natural key for an app-config fragment row.",
    ),
    name="AppConfigFragmentKeyInput",
)
class AppConfigFragmentKeyInputGQL(PydanticInputMixin[AppConfigFragmentKeyInputDTO]):
    scope_type: AppConfigScopeType = gql_field(description="Scope type.")
    scope_id: str = gql_field(description="Scope id.")
    name: str = gql_field(description="Policy name.")
