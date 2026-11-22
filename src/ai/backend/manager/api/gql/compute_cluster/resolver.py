"""GraphQL query and mutation resolvers for compute clusters (super admin only)."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.common.dto.manager.v2.compute_cluster.request import SearchComputeClustersInput
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor, to_global_id
from ai.backend.manager.api.gql.compute_cluster.types import (
    ComputeClusterConnectionGQL,
    ComputeClusterEdgeGQL,
    ComputeClusterFilterGQL,
    ComputeClusterGQL,
    ComputeClusterOrderByGQL,
    CreateComputeClusterInputGQL,
    CreateComputeClusterPayloadGQL,
    PurgeComputeClusterPayloadGQL,
    UpdateComputeClusterInputGQL,
    UpdateComputeClusterPayloadGQL,
)
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_mutation, gql_root_field
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single compute cluster by id (super admin only).",
    )
)
async def admin_compute_cluster(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> ComputeClusterGQL | None:
    check_admin_only()
    node = await info.context.adapters.compute_cluster.get(ComputeClusterID(id))
    return ComputeClusterGQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Search compute clusters with filtering, ordering, and pagination (super admin only)."
        ),
    )
)
async def admin_compute_clusters(
    info: Info[StrawberryGQLContext],
    filter: ComputeClusterFilterGQL | None = None,
    order_by: list[ComputeClusterOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ComputeClusterConnectionGQL | None:
    check_admin_only()
    payload = await info.context.adapters.compute_cluster.global_search(
        SearchComputeClustersInput(
            filter=filter.to_pydantic() if filter else None,
            order=[order.to_pydantic() for order in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [ComputeClusterGQL.from_pydantic(item) for item in payload.items]
    edges = [ComputeClusterEdgeGQL(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return ComputeClusterConnectionGQL(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Register a compute cluster (super admin only).",
    )
)
async def admin_create_compute_cluster(
    info: Info[StrawberryGQLContext],
    input: CreateComputeClusterInputGQL,
) -> CreateComputeClusterPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.compute_cluster.create(input.to_pydantic())
    return CreateComputeClusterPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a compute cluster; only provided fields change (super admin only).",
    )
)
async def admin_update_compute_cluster(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: UpdateComputeClusterInputGQL,
) -> UpdateComputeClusterPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.compute_cluster.update(
        ComputeClusterID(id), input.to_pydantic()
    )
    return UpdateComputeClusterPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove a compute cluster (super admin only).",
    )
)
async def admin_purge_compute_cluster(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeComputeClusterPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.compute_cluster.purge(ComputeClusterID(id))
    return PurgeComputeClusterPayloadGQL.from_pydantic(
        payload, extra={"purged_id": to_global_id(ComputeClusterGQL, payload.entity_id)}
    )
