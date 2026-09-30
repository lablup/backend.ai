"""Domain V2 GraphQL mutation resolvers."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.dto.manager.v2.domain.request import (
    DeleteDomainInput,
    PurgeDomainInput,
    RestoreDomainInput,
)
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
    RestoreDomainPayloadGQL,
    UpdateDomainInputGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Create a new domain (admin only). Requires superadmin privileges.",
    )
)
async def admin_create_domain_v2(
    info: Info[StrawberryGQLContext],
    input: CreateDomainInputGQL,
) -> DomainPayloadGQL | None:
    """Create a new domain."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.domain.create(input.to_pydantic())
    return DomainPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Update a domain (admin only). Requires superadmin privileges. Only provided fields will be updated.",
    )
)
async def admin_update_domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
    input: UpdateDomainInputGQL,
) -> DomainPayloadGQL | None:
    """Update a domain."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.domain.update(domain_name, input.to_pydantic())
    return DomainPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Soft-delete a domain (admin only). Requires superadmin privileges.",
    )
)
async def admin_delete_domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
) -> DeleteDomainPayloadGQL | None:
    """Soft-delete a domain."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.domain.delete(DeleteDomainInput(name=domain_name))
    return DeleteDomainPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Restore a soft-deleted domain (admin only). Requires superadmin privileges.",
    )
)
async def admin_restore_domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
) -> RestoreDomainPayloadGQL | None:
    """Restore a soft-deleted domain."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.domain.restore(RestoreDomainInput(name=domain_name))
    return RestoreDomainPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Permanently purge a domain and all associated data (admin only). Requires superadmin privileges.",
    )
)
async def admin_purge_domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
) -> PurgeDomainPayloadGQL | None:
    """Permanently purge a domain."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.domain.purge(PurgeDomainInput(name=domain_name))
    return PurgeDomainPayloadGQL.from_pydantic(payload)
