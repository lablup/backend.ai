"""Domain V2 GraphQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.dto.manager.v2.domain.request import PurgeDomainInput
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.domain_v2.types.mutations import (
    CreateDomainInputGQL,
    DeleteDomainPayloadGQL,
    DomainPayloadGQL,
    PartialBulkDeleteDomainsInputGQL,
    PartialBulkDomainsPayloadGQL,
    PartialBulkRestoreDomainsInputGQL,
    PartialBulkUpdateDomainsInputGQL,
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
        added_version=NEXT_RELEASE_VERSION,
        description="Update a domain. Only provided fields will be updated.",
    )
)
async def update_domain_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: UpdateDomainInputGQL,
) -> DomainPayloadGQL:
    payload = await info.context.adapters.domain.update(DomainID(id), input.to_pydantic())
    return DomainPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Soft-delete a domain.")
)
async def delete_domain_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteDomainPayloadGQL:
    payload = await info.context.adapters.domain.delete(DomainID(id))
    return DeleteDomainPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Restore a soft-deleted domain."
    )
)
async def restore_domain_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> RestoreDomainPayloadGQL:
    payload = await info.context.adapters.domain.restore(DomainID(id))
    return RestoreDomainPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several domains, answering for each one.",
    )
)
async def partial_bulk_update_domains_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkUpdateDomainsInputGQL,
) -> PartialBulkDomainsPayloadGQL:
    payload = await info.context.adapters.domain.partial_bulk_update(input.to_pydantic())
    return PartialBulkDomainsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Soft-delete several domains, answering for each one.",
    )
)
async def partial_bulk_delete_domains_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkDeleteDomainsInputGQL,
) -> PartialBulkDomainsPayloadGQL:
    payload = await info.context.adapters.domain.partial_bulk_delete(input.to_pydantic())
    return PartialBulkDomainsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Restore several soft-deleted domains, answering for each one.",
    )
)
async def partial_bulk_restore_domains_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkRestoreDomainsInputGQL,
) -> PartialBulkDomainsPayloadGQL:
    payload = await info.context.adapters.domain.partial_bulk_restore(input.to_pydantic())
    return PartialBulkDomainsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Update a domain (admin only). Requires superadmin privileges. Only provided fields will be updated.",
    ),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `updateDomainV2`.",
)
async def admin_update_domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
    input: UpdateDomainInputGQL,
) -> DomainPayloadGQL | None:
    """Update a domain."""
    check_admin_only()
    adapter = info.context.adapters.domain
    payload = await adapter.update(await adapter.lookup_name(domain_name), input.to_pydantic())
    return DomainPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Soft-delete a domain (admin only). Requires superadmin privileges.",
    ),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `deleteDomainV2`.",
)
async def admin_delete_domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
) -> DeleteDomainPayloadGQL | None:
    """Soft-delete a domain."""
    check_admin_only()
    adapter = info.context.adapters.domain
    payload = await adapter.delete(await adapter.lookup_name(domain_name))
    return DeleteDomainPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.9.0",
        description="Restore a soft-deleted domain (admin only). Requires superadmin privileges.",
    ),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `restoreDomainV2`.",
)
async def admin_restore_domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
) -> RestoreDomainPayloadGQL | None:
    """Restore a soft-deleted domain."""
    check_admin_only()
    adapter = info.context.adapters.domain
    payload = await adapter.restore(await adapter.lookup_name(domain_name))
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
