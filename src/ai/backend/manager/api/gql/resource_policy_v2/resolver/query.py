"""Resource Policy V2 GraphQL query resolvers."""

from __future__ import annotations

import strawberry
from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.resource_policy.request import (
    AdminSearchKeypairResourcePoliciesInput,
    AdminSearchProjectResourcePoliciesInput,
    AdminSearchUserResourcePoliciesInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.resource_policy_v2.types.filters import (
    KeypairResourcePolicyV2Filter,
    KeypairResourcePolicyV2OrderBy,
    ProjectResourcePolicyV2Filter,
    ProjectResourcePolicyV2OrderBy,
    UserResourcePolicyV2Filter,
    UserResourcePolicyV2OrderBy,
)
from ai.backend.manager.api.gql.resource_policy_v2.types.node import (
    KeypairResourcePolicyV2Connection,
    KeypairResourcePolicyV2GQL,
    ProjectResourcePolicyV2Connection,
    ProjectResourcePolicyV2GQL,
    UserResourcePolicyV2Connection,
    UserResourcePolicyV2GQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

# ── Keypair Resource Policy Queries ──


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single keypair resource policy by name (admin only).",
    )
)  # type: ignore[misc]
async def admin_keypair_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> KeypairResourcePolicyV2GQL | None:
    check_admin_only()
    node = await info.context.adapters.resource_policy.admin_get_keypair_resource_policy(name)
    return KeypairResourcePolicyV2GQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List all keypair resource policies with pagination (admin only).",
    )
)  # type: ignore[misc]
async def admin_keypair_resource_policies_v2(
    info: Info[StrawberryGQLContext],
    filter: KeypairResourcePolicyV2Filter | None = None,
    order_by: list[KeypairResourcePolicyV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> KeypairResourcePolicyV2Connection | None:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_search_keypair_resource_policies(
        AdminSearchKeypairResourcePoliciesInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [KeypairResourcePolicyV2GQL.from_pydantic(item) for item in payload.items]
    edges = [strawberry.relay.Edge(node=n, cursor=encode_cursor(str(n.id))) for n in nodes]
    return KeypairResourcePolicyV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get the current user's keypair resource policy.",
    )
)  # type: ignore[misc]
async def my_keypair_resource_policy_v2(
    info: Info[StrawberryGQLContext],
) -> KeypairResourcePolicyV2GQL | None:
    node = await info.context.adapters.resource_policy.get_my_keypair_resource_policy()
    return KeypairResourcePolicyV2GQL.from_pydantic(node)


# ── User Resource Policy Queries ──


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single user resource policy by name (admin only).",
    )
)  # type: ignore[misc]
async def admin_user_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> UserResourcePolicyV2GQL | None:
    check_admin_only()
    node = await info.context.adapters.resource_policy.admin_get_user_resource_policy(name)
    return UserResourcePolicyV2GQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List all user resource policies with pagination (admin only).",
    )
)  # type: ignore[misc]
async def admin_user_resource_policies_v2(
    info: Info[StrawberryGQLContext],
    filter: UserResourcePolicyV2Filter | None = None,
    order_by: list[UserResourcePolicyV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserResourcePolicyV2Connection | None:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_search_user_resource_policies(
        AdminSearchUserResourcePoliciesInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [UserResourcePolicyV2GQL.from_pydantic(item) for item in payload.items]
    edges = [strawberry.relay.Edge(node=n, cursor=encode_cursor(str(n.id))) for n in nodes]
    return UserResourcePolicyV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get the current user's user resource policy.",
    )
)  # type: ignore[misc]
async def my_user_resource_policy_v2(
    info: Info[StrawberryGQLContext],
) -> UserResourcePolicyV2GQL | None:
    node = await info.context.adapters.resource_policy.get_my_user_resource_policy()
    return UserResourcePolicyV2GQL.from_pydantic(node)


# ── Project Resource Policy Queries ──


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single project resource policy by name (admin only).",
    )
)  # type: ignore[misc]
async def admin_project_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> ProjectResourcePolicyV2GQL | None:
    check_admin_only()
    node = await info.context.adapters.resource_policy.admin_get_project_resource_policy(name)
    return ProjectResourcePolicyV2GQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List all project resource policies with pagination (admin only).",
    )
)  # type: ignore[misc]
async def admin_project_resource_policies_v2(
    info: Info[StrawberryGQLContext],
    filter: ProjectResourcePolicyV2Filter | None = None,
    order_by: list[ProjectResourcePolicyV2OrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectResourcePolicyV2Connection | None:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_search_project_resource_policies(
        AdminSearchProjectResourcePoliciesInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [ProjectResourcePolicyV2GQL.from_pydantic(item) for item in payload.items]
    edges = [strawberry.relay.Edge(node=n, cursor=encode_cursor(str(n.id))) for n in nodes]
    return ProjectResourcePolicyV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )
