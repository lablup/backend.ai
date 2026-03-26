"""Domain V2 GraphQL mutation resolvers."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.domain.request import DeleteDomainInput, PurgeDomainInput
from ai.backend.common.exception import UnreachableError
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.domain_v2.types.mutations import (
    CreateDomainInputGQL,
    DeleteDomainPayloadGQL,
    DomainPayloadGQL,
    PurgeDomainPayloadGQL,
    UpdateDomainInputGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.data.domain.types import UserInfo


def _get_user_info() -> UserInfo:
    me = current_user()
    if me is None:
        raise UnreachableError("User context is not available after check_admin_only()")
    return UserInfo(
        id=me.user_id,
        role=me.role,
        domain_name=me.domain_name,
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a new domain (admin only). Requires superadmin privileges.",
    )
)  # type: ignore[misc]
async def admin_create_domain_v2(
    info: Info[StrawberryGQLContext],
    input: CreateDomainInputGQL,
) -> DomainPayloadGQL:
    """Create a new domain."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.domain.admin_create(input.to_pydantic(), _get_user_info())
    return DomainPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a domain (admin only). Requires superadmin privileges. Only provided fields will be updated.",
    )
)  # type: ignore[misc]
async def admin_update_domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
    input: UpdateDomainInputGQL,
) -> DomainPayloadGQL:
    """Update a domain."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.domain.admin_update(
        domain_name, input.to_pydantic(), _get_user_info()
    )
    return DomainPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Soft-delete a domain (admin only). Requires superadmin privileges.",
    )
)  # type: ignore[misc]
async def admin_delete_domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
) -> DeleteDomainPayloadGQL:
    """Soft-delete a domain."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.domain.admin_delete(
        DeleteDomainInput(name=domain_name), _get_user_info()
    )
    return DeleteDomainPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently purge a domain and all associated data (admin only). Requires superadmin privileges.",
    )
)  # type: ignore[misc]
async def admin_purge_domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
) -> PurgeDomainPayloadGQL:
    """Permanently purge a domain."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.domain.admin_purge(
        PurgeDomainInput(name=domain_name), _get_user_info()
    )
    return PurgeDomainPayloadGQL.from_pydantic(payload)
