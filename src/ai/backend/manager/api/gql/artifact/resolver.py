from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

import strawberry
from strawberry import ID, UNSET, Info

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.common.dto.manager.v2.artifact.request import (
    AdminSearchArtifactRevisionsInput,
    AdminSearchArtifactsGQLInput,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    UpdateArtifactInput as UpdateArtifactInputDTO,
)
from ai.backend.manager.api.gql.base import (
    encode_cursor,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
    gql_subscription,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.artifact.types import ArtifactAvailability
from ai.backend.manager.defs import ARTIFACT_MAX_SCAN_LIMIT
from ai.backend.manager.errors.artifact import (
    ArtifactImportDelegationError,
    ArtifactScanLimitExceededError,
)

from .types import (
    ApproveArtifactInput,
    ApproveArtifactPayload,
    Artifact,
    ArtifactConnection,
    ArtifactEdge,
    ArtifactFilter,
    ArtifactImportProgressUpdatedPayload,
    ArtifactOrderBy,
    ArtifactRevision,
    ArtifactRevisionConnection,
    ArtifactRevisionEdge,
    ArtifactRevisionFilter,
    ArtifactRevisionImportTask,
    ArtifactRevisionOrderBy,
    ArtifactStatusChangedInput,
    ArtifactStatusChangedPayload,
    CancelArtifactInput,
    CancelImportArtifactPayload,
    CleanupArtifactRevisionsInput,
    CleanupArtifactRevisionsPayload,
    DelegateImportArtifactsInput,
    DelegateImportArtifactsPayload,
    DelegateScanArtifactsInput,
    DelegateScanArtifactsPayload,
    DeleteArtifactsInput,
    DeleteArtifactsPayload,
    ImportArtifactsInput,
    ImportArtifactsOptionsGQL,
    ImportArtifactsPayload,
    RejectArtifactInput,
    RejectArtifactPayload,
    RestoreArtifactsInput,
    RestoreArtifactsPayload,
    ScanArtifactModelsInput,
    ScanArtifactModelsPayload,
    ScanArtifactsInput,
    ScanArtifactsPayload,
    UpdateArtifactInput,
    UpdateArtifactPayload,
    get_registry_url,
    make_artifact_revision_from_node,
    to_artifact_gql_node,
)


# Query Fields
@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Query artifacts with optional filtering, ordering, and pagination. Returns artifacts that are available in the system, discovered through scanning external registries like HuggingFace or Reservoir. By default, only shows ALIVE (non-deleted) artifacts. Use filters to narrow down results by type, name, registry, or availability. Supports cursor-based pagination for efficient browsing of large datasets.",
    )
)  # type: ignore[misc]
async def artifacts(
    info: Info[StrawberryGQLContext],
    filter: ArtifactFilter | None = None,
    order_by: list[ArtifactOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ArtifactConnection | None:
    if filter is None:
        filter = ArtifactFilter(availability=[ArtifactAvailability.ALIVE])
    pydantic_filter = filter.to_pydantic() if filter is not None else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by is not None else None

    search_input = AdminSearchArtifactsGQLInput(
        filter=pydantic_filter,
        order=pydantic_order,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    payload = await info.context.adapters.artifact.admin_search_gql(search_input)

    data_loaders = info.context.data_loaders
    edges = []
    for item in payload.items:
        registry_url = await get_registry_url(data_loaders, item.registry_id, item.registry_type)
        source_url = await get_registry_url(
            data_loaders, item.source_registry_id, item.source_registry_type
        )
        artifact = Artifact.from_pydantic(to_artifact_gql_node(item, registry_url, source_url))
        cursor = encode_cursor(item.id)
        edges.append(ArtifactEdge(node=artifact, cursor=cursor))

    page_info = strawberry.relay.PageInfo(
        has_next_page=payload.has_next_page,
        has_previous_page=payload.has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

    return ArtifactConnection(
        count=payload.total_count,
        edges=edges,
        page_info=page_info,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Retrieve a specific artifact by its ID. Returns detailed information about the artifact including its metadata, registry information, and availability status.",
    )
)  # type: ignore[misc]
async def artifact(id: ID, info: Info[StrawberryGQLContext]) -> Artifact | None:
    artifact_id = UUID(id)
    artifact_node = await info.context.adapters.artifact.get(artifact_id)

    data_loaders = info.context.data_loaders
    registry_url = await get_registry_url(
        data_loaders, artifact_node.registry_id, artifact_node.registry_type
    )
    source_url = await get_registry_url(
        data_loaders,
        artifact_node.source_registry_id,
        artifact_node.source_registry_type,
    )

    return Artifact.from_pydantic(to_artifact_gql_node(artifact_node, registry_url, source_url))


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Query artifact revisions with optional filtering, ordering, and pagination. Returns specific versions/revisions of artifacts. Each revision represents a specific version of an artifact with its own status, file data, and metadata. Use filters to find revisions by status, version, or artifact ID. Supports cursor-based pagination for efficient browsing.",
    )
)  # type: ignore[misc]
async def artifact_revisions(
    info: Info[StrawberryGQLContext],
    filter: ArtifactRevisionFilter | None = None,
    order_by: list[ArtifactRevisionOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ArtifactRevisionConnection | None:
    pydantic_filter = filter.to_pydantic() if filter is not None else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by is not None else None

    search_input = AdminSearchArtifactRevisionsInput(
        filter=pydantic_filter,
        order=pydantic_order,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    payload = await info.context.adapters.artifact.search_revisions_gql(search_input)

    edges = []
    for item in payload.items:
        revision = make_artifact_revision_from_node(item)
        cursor = encode_cursor(item.id)
        edges.append(ArtifactRevisionEdge(node=revision, cursor=cursor))

    page_info = strawberry.relay.PageInfo(
        has_next_page=payload.has_next_page,
        has_previous_page=payload.has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

    return ArtifactRevisionConnection(
        count=payload.total_count,
        edges=edges,
        page_info=page_info,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Retrieve a specific artifact revision by its ID. Returns detailed information about the revision including its status, version, file size, and README content.",
    )
)  # type: ignore[misc]
async def artifact_revision(id: ID, info: Info[StrawberryGQLContext]) -> ArtifactRevision | None:
    revision_node = await info.context.adapters.artifact.get_revision(UUID(id))
    return make_artifact_revision_from_node(revision_node)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Scan external registries to discover available artifacts. Searches HuggingFace or Reservoir registries for artifacts matching the specified criteria and registers them in the system with SCANNED status. The artifacts become available for import but are not downloaded until explicitly imported. This is the first step in the artifact workflow: Scan → Import → Use",
    )
)  # type: ignore[misc]
async def scan_artifacts(
    input: ScanArtifactsInput, info: Info[StrawberryGQLContext]
) -> ScanArtifactsPayload:
    if input.limit > ARTIFACT_MAX_SCAN_LIMIT:
        raise ArtifactScanLimitExceededError(f"Limit cannot exceed {ARTIFACT_MAX_SCAN_LIMIT}")

    results = await info.context.adapters.artifact.scan(
        artifact_type=input.artifact_type,
        registry_id=UUID(input.registry_id) if input.registry_id else None,
        limit=input.limit,
        # TODO: Move this huggingface_registries config if needed
        order=ModelSortKey.DOWNLOADS,
        search=input.search,
    )

    data_loaders = info.context.data_loaders

    artifacts = []
    for item in results:
        registry_url = await get_registry_url(data_loaders, item.registry_id, item.registry_type)
        source_url = await get_registry_url(
            data_loaders, item.source_registry_id, item.source_registry_type
        )
        artifacts.append(
            Artifact.from_pydantic(to_artifact_gql_node(item, registry_url, source_url))
        )
    return ScanArtifactsPayload(artifacts=artifacts)


# Mutations
@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Import scanned artifact revisions from external registries. Downloads the actual files for the specified artifact revisions, transitioning them from SCANNED → PULLING → VERIFYING → AVAILABLE status. Returns background tasks that can be monitored for import progress. Once AVAILABLE, artifacts can be used by users in their sessions",
    )
)  # type: ignore[misc]
async def import_artifacts(
    input: ImportArtifactsInput, info: Info[StrawberryGQLContext]
) -> ImportArtifactsPayload:
    imported_artifacts = []
    tasks = []
    vfolder_id = UUID(input.vfolder_id) if input.vfolder_id else None
    # When using VFolderStorage (vfolder_id provided), store at root path
    storage_prefix = "/" if vfolder_id else None
    options = input.options or ImportArtifactsOptionsGQL()
    force = options.force
    for revision_id in input.artifact_revision_ids:
        revision_node, task_id = await info.context.adapters.artifact.import_revision(
            artifact_revision_id=UUID(revision_id),
            vfolder_id=vfolder_id,
            storage_prefix=storage_prefix,
            force=force,
        )
        artifact_revision = make_artifact_revision_from_node(revision_node)
        imported_artifacts.append(artifact_revision)
        tasks.append(
            ArtifactRevisionImportTask(
                task_id=ID(str(task_id)),
                artifact_revision=artifact_revision,
            )
        )

    edges = [
        ArtifactRevisionEdge(node=artifact, cursor=encode_cursor(artifact.id))
        for artifact in imported_artifacts
    ]

    artifacts_connection = ArtifactRevisionConnection(
        count=len(imported_artifacts),
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )

    return ImportArtifactsPayload(artifact_revisions=artifacts_connection, tasks=tasks)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Triggers artifact scanning on a remote reservoir registry. This mutation instructs a reservoir-type registry to initiate a scan of artifacts from its associated remote reservoir registry source. The scan process will discover and catalog artifacts available in the remote reservoir, making them accessible through the local reservoir registry. Requirements: - The delegator registry must be of type 'reservoir' - The delegator reservoir registry must have a valid remote registry configuration",
    )
)  # type: ignore[misc]
async def delegate_scan_artifacts(
    input: DelegateScanArtifactsInput, info: Info[StrawberryGQLContext]
) -> DelegateScanArtifactsPayload:
    if input.limit > ARTIFACT_MAX_SCAN_LIMIT:
        raise ArtifactScanLimitExceededError(f"Limit cannot exceed {ARTIFACT_MAX_SCAN_LIMIT}")

    delegator_reservoir_id = (
        UUID(input.delegator_reservoir_id) if input.delegator_reservoir_id else None
    )

    results = await info.context.adapters.artifact.delegate_scan(
        delegator_reservoir_id=delegator_reservoir_id,
        delegatee_target=input.delegatee_target.to_pydantic() if input.delegatee_target else None,
        artifact_type=input.artifact_type,
        limit=input.limit,
        order=ModelSortKey.DOWNLOADS,
        search=input.search,
    )

    data_loaders = info.context.data_loaders

    artifacts = []
    for item in results:
        registry_url = await get_registry_url(data_loaders, item.registry_id, item.registry_type)
        source_url = await get_registry_url(
            data_loaders, item.source_registry_id, item.source_registry_type
        )
        artifacts.append(
            Artifact.from_pydantic(to_artifact_gql_node(item, registry_url, source_url))
        )
    return DelegateScanArtifactsPayload(artifacts=artifacts)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Trigger import of artifact revisions from a remote reservoir registry. This mutation instructs a reservoir-type registry to import specific artifact revisions that were previously discovered during a scan from its remote registry. Note that this operation does not import the artifacts directly into the local registry, but only into the delegator reservoir's storage. Requirements: - The delegator registry must be of type 'reservoir' - The delegator registry must have a valid remote registry configuration",
    )
)  # type: ignore[misc]
async def delegate_import_artifacts(
    input: DelegateImportArtifactsInput, info: Info[StrawberryGQLContext]
) -> DelegateImportArtifactsPayload:
    tasks = []

    options = input.options or ImportArtifactsOptionsGQL()
    force = options.force
    revision_nodes, task_ids = await info.context.adapters.artifact.delegate_import_batch(
        delegator_reservoir_id=UUID(input.delegator_reservoir_id)
        if input.delegator_reservoir_id
        else None,
        delegatee_target=input.delegatee_target.to_pydantic() if input.delegatee_target else None,
        artifact_type=input.artifact_type,
        artifact_revision_ids=[UUID(revision_id) for revision_id in input.artifact_revision_ids],
        force=force,
    )
    artifact_revisions = [make_artifact_revision_from_node(node) for node in revision_nodes]
    imported_artifacts = list(artifact_revisions)

    if len(artifact_revisions) != len(task_ids):
        raise ArtifactImportDelegationError(
            "Mismatch between artifact revisions and task IDs returned"
        )

    for task_uuid, artifact_revision in zip(task_ids, artifact_revisions, strict=True):
        task_id = ID(str(task_uuid)) if task_uuid is not None else None
        tasks.append(
            ArtifactRevisionImportTask(
                task_id=task_id,
                artifact_revision=artifact_revision,
            )
        )

    edges = [
        ArtifactRevisionEdge(node=artifact, cursor=encode_cursor(artifact.id))
        for artifact in imported_artifacts
    ]

    artifacts_connection = ArtifactRevisionConnection(
        count=len(imported_artifacts),
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )

    return DelegateImportArtifactsPayload(artifact_revisions=artifacts_connection, tasks=tasks)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Update artifact metadata properties. Modifies artifact metadata such as readonly status and description. This operation does not affect the actual artifact files or revisions",
    )
)  # type: ignore[misc]
async def update_artifact(
    input: UpdateArtifactInput, info: Info[StrawberryGQLContext]
) -> UpdateArtifactPayload:
    pydantic_input = UpdateArtifactInputDTO(
        readonly=input.readonly if input.readonly is not UNSET else None,
        description=input.description if input.description is not UNSET else SENTINEL,
    )
    payload = await info.context.adapters.artifact.update(pydantic_input, UUID(input.artifact_id))

    data_loaders = info.context.data_loaders
    artifact_node = payload.artifact

    registry_url = await get_registry_url(
        data_loaders, artifact_node.registry_id, artifact_node.registry_type
    )
    source_url = await get_registry_url(
        data_loaders, artifact_node.source_registry_id, artifact_node.source_registry_type
    )

    return UpdateArtifactPayload(
        artifact=Artifact.from_pydantic(
            to_artifact_gql_node(artifact_node, registry_url, source_url)
        )
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Clean up stored artifact revision data to free storage space. Removes the downloaded files for the specified artifact revisions and transitions them back to SCANNED status. The metadata remains, allowing the artifacts to be re-imported later if needed. Use this operation to manage storage usage by removing unused artifacts",
    )
)  # type: ignore[misc]
async def cleanup_artifact_revisions(
    input: CleanupArtifactRevisionsInput, info: Info[StrawberryGQLContext]
) -> CleanupArtifactRevisionsPayload:
    cleaned_artifact_revisions: list[ArtifactRevision] = []
    # TODO: Refactor with asyncio.gather()
    pydantic_input = input.to_pydantic()
    for artifact_revision_id in pydantic_input.artifact_revision_ids:
        revision_node = await info.context.adapters.artifact.cleanup_revision(artifact_revision_id)
        cleaned_artifact_revisions.append(make_artifact_revision_from_node(revision_node))

    edges = [
        ArtifactRevisionEdge(node=revision, cursor=encode_cursor(revision.id))
        for revision in cleaned_artifact_revisions
    ]

    artifacts_connection = ArtifactRevisionConnection(
        count=len(cleaned_artifact_revisions),
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )

    return CleanupArtifactRevisionsPayload(artifact_revisions=artifacts_connection)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Soft-delete artifacts from the system. Marks artifacts as deleted without permanently removing them. Deleted artifacts can be restored using the restore_artifacts mutation",
    )
)  # type: ignore[misc]
async def delete_artifacts(
    input: DeleteArtifactsInput, info: Info[StrawberryGQLContext]
) -> DeleteArtifactsPayload:
    pydantic_input = input.to_pydantic()
    payload = await info.context.adapters.artifact.delete(pydantic_input)

    data_loaders = info.context.data_loaders

    artifacts = []
    for item in payload.artifacts:
        registry_url = await get_registry_url(data_loaders, item.registry_id, item.registry_type)
        source_url = await get_registry_url(
            data_loaders, item.source_registry_id, item.source_registry_type
        )
        artifacts.append(
            Artifact.from_pydantic(to_artifact_gql_node(item, registry_url, source_url))
        )

    return DeleteArtifactsPayload(artifacts=artifacts)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Restore previously deleted artifacts. Reverses the soft-delete operation, making the artifacts available again for use in the system",
    )
)  # type: ignore[misc]
async def restore_artifacts(
    input: RestoreArtifactsInput, info: Info[StrawberryGQLContext]
) -> RestoreArtifactsPayload:
    artifact_node_list = await info.context.adapters.artifact.restore(
        artifact_ids=[UUID(id) for id in input.artifact_ids],
    )

    data_loaders = info.context.data_loaders

    artifacts = []
    for item in artifact_node_list:
        registry_url = await get_registry_url(data_loaders, item.registry_id, item.registry_type)
        source_url = await get_registry_url(
            data_loaders, item.source_registry_id, item.source_registry_type
        )
        artifacts.append(
            Artifact.from_pydantic(to_artifact_gql_node(item, registry_url, source_url))
        )

    return RestoreArtifactsPayload(artifacts=artifacts)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Cancel an in-progress artifact import operation. Stops the download process for the specified artifact revision and reverts its status back to SCANNED. The partially downloaded data is cleaned up",
    )
)  # type: ignore[misc]
async def cancel_import_artifact(
    input: CancelArtifactInput, info: Info[StrawberryGQLContext]
) -> CancelImportArtifactPayload:
    # TODO: Cancel actual import bgtask
    pydantic_input = input.to_pydantic()
    revision_node = await info.context.adapters.artifact.cancel_import(
        pydantic_input.artifact_revision_id
    )
    return CancelImportArtifactPayload(
        artifact_revision=make_artifact_revision_from_node(revision_node)
    )


# TODO: Make this available when only having super-admin privileges
@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Approve an artifact revision for general use. Admin-only operation to approve artifact revisions, typically used in environments with approval workflows for artifact deployment",
    )
)  # type: ignore[misc]
async def approve_artifact_revision(
    input: ApproveArtifactInput, info: Info[StrawberryGQLContext]
) -> ApproveArtifactPayload:
    revision_node = await info.context.adapters.artifact.approve_revision(
        UUID(input.artifact_revision_id)
    )
    return ApproveArtifactPayload(artifact_revision=make_artifact_revision_from_node(revision_node))


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Reject an artifact revision, preventing its use. Admin-only operation to reject artifact revisions, typically used in environments with approval workflows for artifact deployment",
    )
)  # type: ignore[misc]
async def reject_artifact_revision(
    input: RejectArtifactInput, info: Info[StrawberryGQLContext]
) -> RejectArtifactPayload:
    revision_node = await info.context.adapters.artifact.reject_revision(
        UUID(input.artifact_revision_id)
    )
    return RejectArtifactPayload(artifact_revision=make_artifact_revision_from_node(revision_node))


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Perform detailed scanning of specific models. Unlike the general scan_artifacts operation, this performs immediate detailed scanning of specified models including README content and file sizes. Returns artifact revisions with complete metadata ready for use",
    )
)  # type: ignore[misc]
async def scan_artifact_models(
    input: ScanArtifactModelsInput, info: Info[StrawberryGQLContext]
) -> ScanArtifactModelsPayload:
    results = await info.context.adapters.artifact.retrieve_models(
        models=[m.to_pydantic() for m in input.models],
        registry_id=input.registry_id,
    )

    edges = []
    for data in results:
        edges.extend([
            ArtifactRevisionEdge(
                node=ArtifactRevision.from_pydantic(revision),
                cursor=encode_cursor(revision.id),
            )
            for revision in data.revisions
        ])

    artifacts_connection = ArtifactRevisionConnection(
        count=len(edges),
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )

    return ScanArtifactModelsPayload(artifact_revision=artifacts_connection)


# Subscriptions
@gql_subscription(  # type: ignore[misc]
    BackendAIGQLMeta(
        added_version="25.14.0",
        description=(
            "Subscribe to real-time artifact status change notifications. "
            "Receives updates when artifact revision statuses change during import, "
            "cleanup, or other operations."
        ),
    )
)
async def artifact_status_changed(
    input: ArtifactStatusChangedInput,
) -> AsyncGenerator[ArtifactStatusChangedPayload, None]:
    # TODO: Implement actual subscription logic using pub/sub system
    raise NotImplementedError("Subscription not implemented")
    yield  # type: ignore[unreachable]  # Makes this an async generator


@gql_subscription(  # type: ignore[misc]
    BackendAIGQLMeta(
        added_version="25.14.0",
        description=(
            "Subscribe to real-time artifact import progress updates. "
            "Receives progress notifications during artifact import operations, "
            "including percentage completed and current status."
        ),
    )
)
async def artifact_import_progress_updated(
    artifact_revision_id: ID,
) -> AsyncGenerator[ArtifactImportProgressUpdatedPayload, None]:
    # TODO: Implement actual subscription logic using pub/sub system
    raise NotImplementedError("Subscription not implemented")
    yield  # type: ignore[unreachable]  # Makes this an async generator
