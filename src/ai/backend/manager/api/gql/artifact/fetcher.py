from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Optional

import strawberry
from aiotools import apartial
from strawberry import Info
from strawberry.dataloader import DataLoader

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
from ai.backend.manager.services.artifact.actions.get import GetArtifactAction
from ai.backend.manager.services.artifact.actions.search import SearchArtifactsAction
from ai.backend.manager.services.artifact_revision.actions.get import GetArtifactRevisionAction
from ai.backend.manager.services.artifact_revision.actions.search import (
    SearchArtifactRevisionsAction,
)

from ..artifact_registry_meta import ArtifactRegistryMeta
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
    )


@lru_cache(maxsize=1)
def _get_artifact_pagination_spec() -> PaginationSpec:
    """Get pagination spec for Artifact queries."""
    return PaginationSpec(
        forward_order=ArtifactRow.id.asc(),
        backward_order=ArtifactRow.id.desc(),
        forward_condition_factory=lambda cursor_value: lambda: ArtifactRow.id > cursor_value,
        backward_condition_factory=lambda cursor_value: lambda: ArtifactRow.id < cursor_value,
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
    filter: Optional[ArtifactRevisionFilter],
    order_by: Optional[list[ArtifactRevisionOrderBy]],
    before: Optional[str],
    after: Optional[str],
    first: Optional[int],
    last: Optional[int],
    limit: Optional[int],
    offset: Optional[int],
) -> ArtifactRevisionConnection:
    """
    Fetch artifact revisions with optional filtering, ordering, and pagination.
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
        cursor = to_global_id(ArtifactRevision, revision_data.id)
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
    filter: Optional[ArtifactFilter],
    order_by: Optional[list[ArtifactOrderBy]],
    before: Optional[str],
    after: Optional[str],
    first: Optional[int],
    last: Optional[int],
    limit: Optional[int],
    offset: Optional[int],
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

    registry_meta_loader = DataLoader(
        apartial(ArtifactRegistryMeta.load_by_id, info.context),
    )

    # Build GraphQL connection response
    edges = []
    for artifact_data in action_result.data:
        registry_meta = await registry_meta_loader.load(artifact_data.registry_id)
        source_registry_meta = await registry_meta_loader.load(artifact_data.source_registry_id)
        artifact = Artifact.from_dataclass(
            artifact_data, registry_url=registry_meta.url, source_url=source_registry_meta.url
        )
        cursor = to_global_id(Artifact, artifact_data.id)
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
) -> Optional[Artifact]:
    """
    Fetch a specific artifact by its ID.
    """
    action_result = await info.context.processors.artifact.get.wait_for_complete(
        GetArtifactAction(
            artifact_id=artifact_id,
        )
    )

    registry_meta_loader = DataLoader(
        apartial(ArtifactRegistryMeta.load_by_id, info.context),
    )

    registry_data = await registry_meta_loader.load(action_result.result.registry_id)
    source_registry_data = await registry_meta_loader.load(action_result.result.source_registry_id)

    return Artifact.from_dataclass(
        action_result.result, registry_data.url, source_registry_data.url
    )


async def fetch_artifact_revision(
    info: Info[StrawberryGQLContext],
    artifact_revision_id: uuid.UUID,
) -> Optional[ArtifactRevision]:
    """
    Fetch a specific artifact revision by its ID.
    """
    action_result = await info.context.processors.artifact_revision.get.wait_for_complete(
        GetArtifactRevisionAction(
            artifact_revision_id=artifact_revision_id,
        )
    )

    return ArtifactRevision.from_dataclass(action_result.revision)
