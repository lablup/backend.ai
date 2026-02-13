from __future__ import annotations

import uuid
from functools import lru_cache

import strawberry
from strawberry import Info

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.services.artifact.actions.get import GetArtifactAction
from ai.backend.manager.services.artifact.actions.search import SearchArtifactsAction
from ai.backend.manager.services.artifact_revision.actions.get import GetArtifactRevisionAction
from ai.backend.manager.services.artifact_revision.actions.search import (
    SearchArtifactRevisionsAction,
)

from .types import (
    Artifact,
    ArtifactConnection,
    ArtifactEdge,
    ArtifactFilter,
    ArtifactOrderBy,
    ArtifactRevision,
    ArtifactRevisionConnection,
    ArtifactRevisionEdge,
    ArtifactRevisionFilter,
    ArtifactRevisionOrderBy,
)


@lru_cache(maxsize=1)
def _get_artifact_revision_pagination_spec() -> PaginationSpec:
    """Get pagination spec for ArtifactRevision queries."""
    return PaginationSpec(
        forward_order=ArtifactRevisionRow.id.asc(),
        backward_order=ArtifactRevisionRow.id.desc(),
        forward_condition_factory=lambda cursor_value: lambda: ArtifactRevisionRow.id
        > cursor_value,
        backward_condition_factory=lambda cursor_value: lambda: ArtifactRevisionRow.id
        < cursor_value,
        tiebreaker_order=ArtifactRevisionRow.id.asc(),
    )


@lru_cache(maxsize=1)
def _get_artifact_pagination_spec() -> PaginationSpec:
    """Get pagination spec for Artifact queries."""
    return PaginationSpec(
        forward_order=ArtifactRow.id.asc(),
        backward_order=ArtifactRow.id.desc(),
        forward_condition_factory=lambda cursor_value: lambda: ArtifactRow.id > cursor_value,
        backward_condition_factory=lambda cursor_value: lambda: ArtifactRow.id < cursor_value,
        tiebreaker_order=ArtifactRow.id.asc(),
    )


async def get_registry_url(
    data_loaders: DataLoaders,
    registry_id: uuid.UUID,
    registry_type: ArtifactRegistryType,
) -> str:
    """Get the URL for a registry based on its type."""
    match registry_type:
        case ArtifactRegistryType.HUGGINGFACE:
            hf_registry = await data_loaders.huggingface_registry_loader.load(registry_id)
            if hf_registry is None:
                raise ArtifactRegistryNotFoundError(f"HuggingFace registry {registry_id} not found")
            return hf_registry.url
        case ArtifactRegistryType.RESERVOIR:
            reservoir_registry = await data_loaders.reservoir_registry_loader.load(registry_id)
            if reservoir_registry is None:
                raise ArtifactRegistryNotFoundError(f"Reservoir registry {registry_id} not found")
            return reservoir_registry.endpoint
    raise ArtifactRegistryNotFoundError(f"Unknown registry type: {registry_type}")


async def fetch_artifact_revisions(
    info: Info[StrawberryGQLContext],
    filter: ArtifactRevisionFilter | None = None,
    order_by: list[ArtifactRevisionOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> ArtifactRevisionConnection:
    """Fetch artifact revisions with optional filtering, ordering, and pagination.

    Args:
        info: GraphQL context info
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
        base_conditions: Additional conditions to prepend (e.g., artifact_id filter)
    """
    # Build querier using adapter
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_artifact_revision_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    # Get artifact revisions using list action
    action_result = (
        await info.context.processors.artifact_revision.search_revision.wait_for_complete(
            SearchArtifactRevisionsAction(querier=querier)
        )
    )

    # Build GraphQL connection response
    edges = []
    for revision_data in action_result.data:
        revision = ArtifactRevision.from_dataclass(revision_data)
        cursor = encode_cursor(revision_data.id)
        edges.append(ArtifactRevisionEdge(node=revision, cursor=cursor))

    page_info = strawberry.relay.PageInfo(
        has_next_page=action_result.has_next_page,
        has_previous_page=action_result.has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

    return ArtifactRevisionConnection(
        count=action_result.total_count,
        edges=edges,
        page_info=page_info,
    )


async def fetch_artifacts(
    info: Info[StrawberryGQLContext],
    filter: ArtifactFilter | None,
    order_by: list[ArtifactOrderBy] | None,
    before: str | None,
    after: str | None,
    first: int | None,
    last: int | None,
    limit: int | None,
    offset: int | None,
) -> ArtifactConnection:
    """
    Fetch artifacts with optional filtering, ordering, and pagination.
    """
    # Build querier using adapter
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_artifact_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    # Get artifacts using list action
    action_result = await info.context.processors.artifact.search_artifacts.wait_for_complete(
        SearchArtifactsAction(querier=querier)
    )

    # Build GraphQL connection response
    data_loaders = info.context.data_loaders
    edges = []
    for artifact_data in action_result.data:
        registry_url = await get_registry_url(
            data_loaders, artifact_data.registry_id, artifact_data.registry_type
        )
        source_url = await get_registry_url(
            data_loaders, artifact_data.source_registry_id, artifact_data.source_registry_type
        )
        artifact = Artifact.from_dataclass(
            artifact_data, registry_url=registry_url, source_url=source_url
        )
        cursor = encode_cursor(artifact_data.id)
        edges.append(ArtifactEdge(node=artifact, cursor=cursor))

    page_info = strawberry.relay.PageInfo(
        has_next_page=action_result.has_next_page,
        has_previous_page=action_result.has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

    return ArtifactConnection(
        count=action_result.total_count,
        edges=edges,
        page_info=page_info,
    )


async def fetch_artifact(
    info: Info[StrawberryGQLContext],
    artifact_id: uuid.UUID,
) -> Artifact | None:
    """
    Fetch a specific artifact by its ID.
    """
    action_result = await info.context.processors.artifact.get.wait_for_complete(
        GetArtifactAction(
            artifact_id=artifact_id,
        )
    )

    data_loaders = info.context.data_loaders
    registry_url = await get_registry_url(
        data_loaders, action_result.result.registry_id, action_result.result.registry_type
    )
    source_url = await get_registry_url(
        data_loaders,
        action_result.result.source_registry_id,
        action_result.result.source_registry_type,
    )

    return Artifact.from_dataclass(action_result.result, registry_url, source_url)


async def fetch_artifact_revision(
    info: Info[StrawberryGQLContext],
    artifact_revision_id: uuid.UUID,
) -> ArtifactRevision | None:
    """
    Fetch a specific artifact revision by its ID.
    """
    action_result = await info.context.processors.artifact_revision.get.wait_for_complete(
        GetArtifactRevisionAction(
            artifact_revision_id=artifact_revision_id,
        )
    )

    return ArtifactRevision.from_dataclass(action_result.revision)
