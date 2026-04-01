"""GraphQL query resolvers for resource group system."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from strawberry import Info
from strawberry.relay import Connection, Edge, PageInfo

from ai.backend.common.dto.manager.v2.resource_group.request import AdminSearchResourceGroupsInput
from ai.backend.common.dto.manager.v2.resource_group.response import DeleteResourceGroupPayload
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

from .types import (
    AllowedDomainsPayloadGQL,
    AllowedProjectsPayloadGQL,
    AllowedResourceGroupsPayloadGQL,
    CreateResourceGroupInputGQL,
    CreateResourceGroupPayloadGQL,
    DeleteResourceGroupPayloadGQL,
    ResourceGroupFilterGQL,
    ResourceGroupGQL,
    ResourceGroupOrderByGQL,
    UpdateAllowedDomainsForResourceGroupInputGQL,
    UpdateAllowedProjectsForResourceGroupInputGQL,
    UpdateAllowedResourceGroupsForDomainInputGQL,
    UpdateAllowedResourceGroupsForProjectInputGQL,
    UpdateResourceGroupFairShareSpecInput,
    UpdateResourceGroupFairShareSpecPayload,
    UpdateResourceGroupInput,
    UpdateResourceGroupPayload,
)

# Connection types

ResourceGroupEdge = Edge[ResourceGroupGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Resource group connection",
    )
)
class ResourceGroupConnection(Connection[ResourceGroupGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Query fields


@gql_root_field(
    BackendAIGQLMeta(added_version="26.2.0", description="List resource groups (admin only)")
)  # type: ignore[misc]
async def admin_resource_groups(
    info: Info[StrawberryGQLContext],
    filter: ResourceGroupFilterGQL | None = None,
    order_by: list[ResourceGroupOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ResourceGroupConnection | None:
    check_admin_only()

    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.resource_group.search(
        AdminSearchResourceGroupsInput(
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

    nodes = [ResourceGroupGQL.from_pydantic(data) for data in payload.items]
    edges = [ResourceGroupEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ResourceGroupConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@gql_root_field(
    BackendAIGQLMeta(added_version="26.2.0", description="List resource groups"),
    deprecation_reason="Use admin_resource_groups instead. This API will be removed after v26.3.0. See BEP-1041 for migration guide.",
)  # type: ignore[misc]
async def resource_groups(
    info: Info[StrawberryGQLContext],
    filter: ResourceGroupFilterGQL | None = None,
    order_by: list[ResourceGroupOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ResourceGroupConnection | None:
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.resource_group.search(
        AdminSearchResourceGroupsInput(
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

    nodes = [ResourceGroupGQL.from_pydantic(data) for data in payload.items]
    edges = [ResourceGroupEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ResourceGroupConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


# Mutation fields


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Update fair share configuration for a resource group (admin only). Only provided fields are updated; others retain their existing values. Resource weights are validated against capacity - only resource types available in the scaling group's capacity can be specified.",
    )
)  # type: ignore[misc]
async def admin_update_resource_group_fair_share_spec(
    info: Info[StrawberryGQLContext],
    input: UpdateResourceGroupFairShareSpecInput,
) -> UpdateResourceGroupFairShareSpecPayload:
    """Update fair share spec with partial update and validation."""
    check_admin_only()

    dto = input.to_pydantic()
    payload_dto = await info.context.adapters.resource_group.update_fair_share_spec(dto)

    return UpdateResourceGroupFairShareSpecPayload.from_pydantic(payload_dto)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Update fair share configuration for a resource group (superadmin only). Only provided fields are updated; others retain their existing values. Resource weights are validated against capacity - only resource types available in the scaling group's capacity can be specified.",
    ),
    deprecation_reason=(
        "Use admin_update_resource_group_fair_share_spec instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)  # type: ignore[misc]
async def update_resource_group_fair_share_spec(
    info: Info[StrawberryGQLContext],
    input: UpdateResourceGroupFairShareSpecInput,
) -> UpdateResourceGroupFairShareSpecPayload:
    """Update fair share spec with partial update and validation."""
    dto = input.to_pydantic()
    payload_dto = await info.context.adapters.resource_group.update_fair_share_spec(dto)

    return UpdateResourceGroupFairShareSpecPayload.from_pydantic(payload_dto)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Update resource group configuration (admin only). Only provided fields are updated; others retain their existing values. Supports all configuration fields except fair_share (use separate mutation).",
    )
)  # type: ignore[misc]
async def admin_update_resource_group(
    info: Info[StrawberryGQLContext],
    input: UpdateResourceGroupInput,
) -> UpdateResourceGroupPayload:
    """Update resource group configuration with partial update."""
    check_admin_only()

    dto = input.to_pydantic()
    payload_dto = await info.context.adapters.resource_group.update_config(dto)

    return UpdateResourceGroupPayload.from_pydantic(payload_dto)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single resource group by name (admin only).",
    )
)  # type: ignore[misc]
async def admin_resource_group_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> ResourceGroupGQL | None:
    check_admin_only()
    node = await info.context.adapters.resource_group.get(name)
    return ResourceGroupGQL.from_pydantic(node)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a new resource group (admin only).",
    )
)  # type: ignore[misc]
async def admin_create_resource_group_v2(
    info: Info[StrawberryGQLContext],
    input: CreateResourceGroupInputGQL,
) -> CreateResourceGroupPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_group.create(input.to_pydantic())
    return CreateResourceGroupPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete a resource group (admin only).",
    )
)  # type: ignore[misc]
async def admin_delete_resource_group_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> DeleteResourceGroupPayloadGQL:
    check_admin_only()
    result = await info.context.adapters.resource_group.purge(name)
    payload = DeleteResourceGroupPayload(id=result.id)
    return DeleteResourceGroupPayloadGQL.from_pydantic(payload)


# Allow / Disallow queries


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get allowed resource groups for a domain (admin only).",
    )
)  # type: ignore[misc]
async def admin_allowed_resource_groups_for_domain_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
) -> AllowedResourceGroupsPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_group.get_allowed_resource_groups_for_domain(
        domain_name
    )
    return AllowedResourceGroupsPayloadGQL.from_pydantic(payload)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get allowed resource groups for a project (admin only).",
    )
)  # type: ignore[misc]
async def admin_allowed_resource_groups_for_project_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> AllowedResourceGroupsPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_group.get_allowed_resource_groups_for_project(
        project_id
    )
    return AllowedResourceGroupsPayloadGQL.from_pydantic(payload)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get allowed domains for a resource group (admin only).",
    )
)  # type: ignore[misc]
async def admin_allowed_domains_for_resource_group_v2(
    info: Info[StrawberryGQLContext],
    resource_group_name: str,
) -> AllowedDomainsPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_group.get_allowed_domains_for_resource_group(
        resource_group_name
    )
    return AllowedDomainsPayloadGQL.from_pydantic(payload)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get allowed projects for a resource group (admin only).",
    )
)  # type: ignore[misc]
async def admin_allowed_projects_for_resource_group_v2(
    info: Info[StrawberryGQLContext],
    resource_group_name: str,
) -> AllowedProjectsPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_group.get_allowed_projects_for_resource_group(
        resource_group_name
    )
    return AllowedProjectsPayloadGQL.from_pydantic(payload)


# Allow / Disallow mutations


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update allowed resource groups for a domain (admin only).",
    )
)  # type: ignore[misc]
async def admin_update_allowed_resource_groups_for_domain_v2(
    info: Info[StrawberryGQLContext],
    input: UpdateAllowedResourceGroupsForDomainInputGQL,
) -> AllowedResourceGroupsPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_group.update_allowed_resource_groups_for_domain(
        input.to_pydantic()
    )
    return AllowedResourceGroupsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update allowed resource groups for a project (admin only).",
    )
)  # type: ignore[misc]
async def admin_update_allowed_resource_groups_for_project_v2(
    info: Info[StrawberryGQLContext],
    input: UpdateAllowedResourceGroupsForProjectInputGQL,
) -> AllowedResourceGroupsPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_group.update_allowed_resource_groups_for_project(
        input.to_pydantic()
    )
    return AllowedResourceGroupsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update allowed domains for a resource group (admin only).",
    )
)  # type: ignore[misc]
async def admin_update_allowed_domains_for_resource_group_v2(
    info: Info[StrawberryGQLContext],
    input: UpdateAllowedDomainsForResourceGroupInputGQL,
) -> AllowedDomainsPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_group.update_allowed_domains_for_resource_group(
        input.to_pydantic()
    )
    return AllowedDomainsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update allowed projects for a resource group (admin only).",
    )
)  # type: ignore[misc]
async def admin_update_allowed_projects_for_resource_group_v2(
    info: Info[StrawberryGQLContext],
    input: UpdateAllowedProjectsForResourceGroupInputGQL,
) -> AllowedProjectsPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_group.update_allowed_projects_for_resource_group(
        input.to_pydantic()
    )
    return AllowedProjectsPayloadGQL.from_pydantic(payload)
