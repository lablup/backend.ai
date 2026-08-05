"""GraphQL query resolvers for the merged app config view."""

from __future__ import annotations

from typing import Annotated

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.app_config.request import (
    MyGetAppConfigsInput,
    PublicGetAppConfigsInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_root_field
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .types import AppConfigGQL


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Read the acting user's merged config for each of the given names — public, the "
            "caller's domain, and the caller's own fragments deep-merged by allow-list rank. "
            "One entry per requested name, in request order; a name nothing visible "
            "contributes to yields an empty merge."
        ),
    )
)  # type: ignore[misc]
async def my_app_configs(
    info: Info[StrawberryGQLContext],
    config_names: Annotated[
        list[str],
        strawberry.argument(description="Config names to read merges for."),
    ],
) -> list[AppConfigGQL]:
    payload = await info.context.adapters.app_config.my_get_app_configs(
        MyGetAppConfigsInput(config_names=config_names)
    )
    return [AppConfigGQL.from_pydantic(node) for node in payload.app_configs]


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Read the merged config for each of the given names from public fragments only. "
            "Served by the `public` subgraph without authentication, for pre-login clients that "
            "need config before they have credentials."
        ),
    )
)  # type: ignore[misc]
async def public_app_configs(
    info: Info[StrawberryGQLContext],
    config_names: Annotated[
        list[str],
        strawberry.argument(description="Config names to read merges for."),
    ],
) -> list[AppConfigGQL]:
    payload = await info.context.adapters.app_config.public_get_app_configs(
        PublicGetAppConfigsInput(config_names=config_names)
    )
    return [AppConfigGQL.from_pydantic(node) for node in payload.app_configs]
