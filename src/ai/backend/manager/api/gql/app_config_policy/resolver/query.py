"""AppConfigPolicy GQL query resolvers."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    SearchAppConfigPoliciesInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config_policy.types import (
    AppConfigPolicyFilterGQL,
    AppConfigPolicyGQL,
    AppConfigPolicyOrderByGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Get a single app-config policy by `config_name`. Available to any authenticated user."
        ),
    )
)  # type: ignore[misc]
async def app_config_policy(
    info: Info[StrawberryGQLContext],
    config_name: str,
) -> AppConfigPolicyGQL | None:
    payload = await info.context.adapters.app_config_policy.get(config_name)
    if payload.item is None:
        return None
    return AppConfigPolicyGQL.from_pydantic(payload.item)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "List app-config policies with filtering and pagination. Available to any "
            "authenticated user."
        ),
    )
)  # type: ignore[misc]
async def app_config_policies(
    info: Info[StrawberryGQLContext],
    filter: AppConfigPolicyFilterGQL | None = None,
    order_by: list[AppConfigPolicyOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[AppConfigPolicyGQL]:
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.app_config_policy.search(
        SearchAppConfigPoliciesInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    return [AppConfigPolicyGQL.from_pydantic(node) for node in payload.items]
