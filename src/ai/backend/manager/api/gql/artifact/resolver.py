from __future__ import annotations

import uuid
from typing import AsyncGenerator, Optional

import strawberry
from strawberry import ID, Info

from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.manager.api.gql.base import (
    to_global_id,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.artifact.types import ArtifactAvailability
from ai.backend.manager.defs import ARTIFACT_MAX_SCAN_LIMIT
from ai.backend.manager.errors.artifact import (
    ArtifactImportDelegationError,
    ArtifactScanLimitExceededError,
)
from ai.backend.manager.repositories.artifact.updaters import ArtifactUpdaterSpec
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact.actions.delegate_scan import DelegateScanArtifactsAction
from ai.backend.manager.services.artifact.actions.delete_multi import DeleteArtifactsAction
from ai.backend.manager.services.artifact.actions.restore_multi import RestoreArtifactsAction
from ai.backend.manager.services.artifact.actions.retrieve_model_multi import RetrieveModelsAction
from ai.backend.manager.services.artifact.actions.scan import ScanArtifactsAction
from ai.backend.manager.services.artifact.actions.update import UpdateArtifactAction
from ai.backend.manager.services.artifact_revision.actions.approve import (
    ApproveArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.cancel_import import CancelImportAction
from ai.backend.manager.services.artifact_revision.actions.cleanup import (
    CleanupArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.delegate_import_revision_batch import (
    DelegateImportArtifactRevisionBatchAction,
)
from ai.backend.manager.services.artifact_revision.actions.import_revision import (
    ImportArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.reject import (
    RejectArtifactRevisionAction,
)
from ai.backend.manager.types import TriState

from .fetcher import (
    fetch_artifact,
    fetch_artifact_revision,
    fetch_artifact_revisions,
    fetch_artifacts,
    get_registry_url,
)
from .types import (
    ApproveArtifactInput,
    ApproveArtifactPayload,
    Artifact,
    ArtifactConnection,
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
)


# Query Fields
@strawberry.field(
    description=dedent_strip("""
    Added in 25.14.0.

    Query artifacts with optional filtering, ordering, and pagination.

    Returns artifacts that are available in the system, discovered through scanning
    external registries like HuggingFace or Reservoir. By default, only shows
    ALIVE (non-deleted) artifacts.

    Use filters to narrow down results by type, name, registry, or availability.
    Supports cursor-based pagination for efficient browsing of large datasets.
    """)
)
async def artifacts(
    info: Info[StrawberryGQLContext],
    filter: Optional[ArtifactFilter] = ArtifactFilter(availability=[ArtifactAvailability.ALIVE]),
    order_by: Optional[list[ArtifactOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ArtifactConnection:
    return await fetch_artifacts(
        info,
        filter,
        order_by,
        before,
        after,
        first,
        last,
        limit,
        offset,
    )


@strawberry.field(
    description=dedent_strip("""
    Added in 25.14.0.

    Retrieve a specific artifact by its ID.

    Returns detailed information about the artifact including its metadata,
    registry information, and availability status.
    """)
)
async def artifact(id: ID, info: Info[StrawberryGQLContext]) -> Optional[Artifact]:
    return await fetch_artifact(info, uuid.UUID(id))


@strawberry.field(
    description=dedent_strip("""
    Added in 25.14.0.

    Query artifact revisions with optional filtering, ordering, and pagination.

    Returns specific versions/revisions of artifacts. Each revision represents
    a specific version of an artifact with its own status, file data, and metadata.

    Use filters to find revisions by status, version, or artifact ID.
    Supports cursor-based pagination for efficient browsing.
    """)
)
async def artifact_revisions(
    info: Info[StrawberryGQLContext],
    filter: Optional[ArtifactRevisionFilter] = None,
    order_by: Optional[list[ArtifactRevisionOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ArtifactRevisionConnection:
    return await fetch_artifact_revisions(
        info,
        filter,
        order_by,
        before,
        after,
        first,
        last,
        limit,
        offset,
    )


@strawberry.field(
    description=dedent_strip("""
    Added in 25.14.0.

    Retrieve a specific artifact revision by its ID.

    Returns detailed information about the revision including its status,
    version, file size, and README content.
    """)
)
async def artifact_revision(id: ID, info: Info[StrawberryGQLContext]) -> Optional[ArtifactRevision]:
    return await fetch_artifact_revision(info, uuid.UUID(id))


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.14.0.

    Scan external registries to discover available artifacts.

    Searches HuggingFace or Reservoir registries for artifacts matching the specified
    criteria and registers them in the system with SCANNED status. The artifacts
    become available for import but are not downloaded until explicitly imported.

    This is the first step in the artifact workflow: Scan → Import → Use.
    """)
)
async def scan_artifacts(
    input: ScanArtifactsInput, info: Info[StrawberryGQLContext]
) -> ScanArtifactsPayload:
    if input.limit > ARTIFACT_MAX_SCAN_LIMIT:
        raise ArtifactScanLimitExceededError(f"Limit cannot exceed {ARTIFACT_MAX_SCAN_LIMIT}")

    action_result = await info.context.processors.artifact.scan.wait_for_complete(
        ScanArtifactsAction(
            artifact_type=input.artifact_type,
            registry_id=uuid.UUID(input.registry_id) if input.registry_id else None,
            limit=input.limit,
            # TODO: Move this huggingface_registries config if needed
            order=ModelSortKey.DOWNLOADS,
            search=input.search,
        )
    )

    data_loaders = info.context.data_loaders

    artifacts = []
    for item in action_result.result:
        registry_url = await get_registry_url(data_loaders, item.registry_id, item.registry_type)
        source_url = await get_registry_url(
            data_loaders, item.source_registry_id, item.source_registry_type
        )
        artifacts.append(Artifact.from_dataclass(item, registry_url, source_url))
    return ScanArtifactsPayload(artifacts=artifacts)


# Mutations
@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.14.0.

    Import scanned artifact revisions from external registries.

    Downloads the actual files for the specified artifact revisions, transitioning
    them from SCANNED → PULLING → VERIFYING → AVAILABLE status.

    Returns background tasks that can be monitored for import progress.
    Once AVAILABLE, artifacts can be used by users in their sessions.
    """)
)
async def import_artifacts(
    input: ImportArtifactsInput, info: Info[StrawberryGQLContext]
) -> ImportArtifactsPayload:
    imported_artifacts = []
    tasks = []
    for revision_id in input.artifact_revision_ids:
        action_result = (
            await info.context.processors.artifact_revision.import_revision.wait_for_complete(
                ImportArtifactRevisionAction(
                    artifact_revision_id=uuid.UUID(revision_id),
                )
            )
        )
        artifact_revision = ArtifactRevision.from_dataclass(action_result.result)
        imported_artifacts.append(artifact_revision)
        tasks.append(
            ArtifactRevisionImportTask(
                task_id=ID(str(action_result.task_id)),
                artifact_revision=artifact_revision,
            )
        )

    edges = [
        ArtifactRevisionEdge(node=artifact, cursor=to_global_id(ArtifactRevisionEdge, artifact.id))
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


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.15.0.

    Triggers artifact scanning on a remote reservoir registry.

    This mutation instructs a reservoir-type registry to initiate a scan of artifacts
    from its associated remote reservoir registry source. The scan process will discover and
    catalog artifacts available in the remote reservoir, making them accessible
    through the local reservoir registry.

    Requirements:
    - The delegator registry must be of type 'reservoir'
    - The delegator reservoir registry must have a valid remote registry configuration
""")
)
async def delegate_scan_artifacts(
    input: DelegateScanArtifactsInput, info: Info[StrawberryGQLContext]
) -> DelegateScanArtifactsPayload:
    if input.limit > ARTIFACT_MAX_SCAN_LIMIT:
        raise ArtifactScanLimitExceededError(f"Limit cannot exceed {ARTIFACT_MAX_SCAN_LIMIT}")

    delegator_reservoir_id = (
        uuid.UUID(input.delegator_reservoir_id) if input.delegator_reservoir_id else None
    )

    action_result = await info.context.processors.artifact.delegate_scan.wait_for_complete(
        DelegateScanArtifactsAction(
            delegator_reservoir_id=delegator_reservoir_id,
            delegatee_target=input.delegatee_target.to_dataclass()
            if input.delegatee_target
            else None,
            artifact_type=input.artifact_type,
            limit=input.limit,
            order=ModelSortKey.DOWNLOADS,
            search=input.search,
        )
    )

    data_loaders = info.context.data_loaders

    artifacts = []
    for item in action_result.result:
        registry_url = await get_registry_url(data_loaders, item.registry_id, item.registry_type)
        source_url = await get_registry_url(
            data_loaders, item.source_registry_id, item.source_registry_type
        )
        artifacts.append(Artifact.from_dataclass(item, registry_url, source_url))
    return DelegateScanArtifactsPayload(artifacts=artifacts)


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.15.0.

    Trigger import of artifact revisions from a remote reservoir registry.

    This mutation instructs a reservoir-type registry to import specific artifact revisions
    that were previously discovered during a scan from its remote registry.
    Note that this operation does not import the artifacts directly into the local registry, but only into the delegator reservoir's storage.

    Requirements:
    - The delegator registry must be of type 'reservoir'
    - The delegator registry must have a valid remote registry configuration
""")
)
async def delegate_import_artifacts(
    input: DelegateImportArtifactsInput, info: Info[StrawberryGQLContext]
) -> DelegateImportArtifactsPayload:
    imported_artifacts = []
    tasks = []

    action_result = await info.context.processors.artifact_revision.delegate_import_revision_batch.wait_for_complete(
        DelegateImportArtifactRevisionBatchAction(
            delegator_reservoir_id=uuid.UUID(input.delegator_reservoir_id)
            if input.delegator_reservoir_id
            else None,
            delegatee_target=input.delegatee_target.to_dataclass()
            if input.delegatee_target
            else None,
            artifact_type=input.artifact_type,
            artifact_revision_ids=[
                uuid.UUID(revision_id) for revision_id in input.artifact_revision_ids
            ],
        )
    )
    artifact_revisions = [
        ArtifactRevision.from_dataclass(result) for result in action_result.result
    ]
    imported_artifacts.extend(artifact_revisions)

    if len(artifact_revisions) != len(action_result.task_ids):
        raise ArtifactImportDelegationError(
            "Mismatch between artifact revisions and task IDs returned"
        )

    for task_uuid, artifact_revision in zip(
        action_result.task_ids, artifact_revisions, strict=True
    ):
        task_id = ID(str(task_uuid)) if task_uuid is not None else None
        tasks.append(
            ArtifactRevisionImportTask(
                task_id=task_id,
                artifact_revision=artifact_revision,
            )
        )

    edges = [
        ArtifactRevisionEdge(node=artifact, cursor=to_global_id(ArtifactRevisionEdge, artifact.id))
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


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.14.0.

    Update artifact metadata properties.

    Modifies artifact metadata such as readonly status and description.
    This operation does not affect the actual artifact files or revisions.
    """)
)
async def update_artifact(
    input: UpdateArtifactInput, info: Info[StrawberryGQLContext]
) -> UpdateArtifactPayload:
    action_result = await info.context.processors.artifact.update.wait_for_complete(
        UpdateArtifactAction(
            updater=Updater(
                spec=ArtifactUpdaterSpec(
                    readonly=TriState.from_graphql(input.readonly),
                    description=TriState.from_graphql(input.description),
                ),
                pk_value=uuid.UUID(input.artifact_id),
            ),
        )
    )

    artifact = action_result.result
    data_loaders = info.context.data_loaders

    registry_url = await get_registry_url(
        data_loaders, artifact.registry_id, artifact.registry_type
    )
    source_url = await get_registry_url(
        data_loaders, artifact.source_registry_id, artifact.source_registry_type
    )

    return UpdateArtifactPayload(
        artifact=Artifact.from_dataclass(artifact, registry_url=registry_url, source_url=source_url)
    )


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.14.0.

    Clean up stored artifact revision data to free storage space.

    Removes the downloaded files for the specified artifact revisions and
    transitions them back to SCANNED status. The metadata remains, allowing
    the artifacts to be re-imported later if needed.

    Use this operation to manage storage usage by removing unused artifacts.
    """)
)
async def cleanup_artifact_revisions(
    input: CleanupArtifactRevisionsInput, info: Info[StrawberryGQLContext]
) -> CleanupArtifactRevisionsPayload:
    cleaned_artifact_revisions: list[ArtifactRevision] = []
    # TODO: Refactor with asyncio.gather()
    for artifact_revision_id in input.artifact_revision_ids:
        action_result = await info.context.processors.artifact_revision.cleanup.wait_for_complete(
            CleanupArtifactRevisionAction(
                artifact_revision_id=uuid.UUID(artifact_revision_id),
            )
        )
        cleaned_artifact_revisions.append(ArtifactRevision.from_dataclass(action_result.result))

    edges = [
        ArtifactRevisionEdge(node=revision, cursor=to_global_id(ArtifactRevisionEdge, revision.id))
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


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.15.0.

    Soft-delete artifacts from the system.

    Marks artifacts as deleted without permanently removing them.
    Deleted artifacts can be restored using the restore_artifacts mutation.
    """)
)
async def delete_artifacts(
    input: DeleteArtifactsInput, info: Info[StrawberryGQLContext]
) -> DeleteArtifactsPayload:
    action_result = await info.context.processors.artifact.delete_artifacts.wait_for_complete(
        DeleteArtifactsAction(
            artifact_ids=[uuid.UUID(id) for id in input.artifact_ids],
        )
    )

    data_loaders = info.context.data_loaders

    artifacts = []
    for item in action_result.artifacts:
        registry_url = await get_registry_url(data_loaders, item.registry_id, item.registry_type)
        source_url = await get_registry_url(
            data_loaders, item.source_registry_id, item.source_registry_type
        )
        artifacts.append(Artifact.from_dataclass(item, registry_url, source_url))

    return DeleteArtifactsPayload(artifacts=artifacts)


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.15.0.

    Restore previously deleted artifacts.

    Reverses the soft-delete operation, making the artifacts available again
    for use in the system.
    """)
)
async def restore_artifacts(
    input: RestoreArtifactsInput, info: Info[StrawberryGQLContext]
) -> RestoreArtifactsPayload:
    action_result = await info.context.processors.artifact.restore_artifacts.wait_for_complete(
        RestoreArtifactsAction(
            artifact_ids=[uuid.UUID(id) for id in input.artifact_ids],
        )
    )

    data_loaders = info.context.data_loaders

    artifacts = []
    for item in action_result.artifacts:
        registry_url = await get_registry_url(data_loaders, item.registry_id, item.registry_type)
        source_url = await get_registry_url(
            data_loaders, item.source_registry_id, item.source_registry_type
        )
        artifacts.append(Artifact.from_dataclass(item, registry_url, source_url))

    return RestoreArtifactsPayload(artifacts=artifacts)


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.14.0.

    Cancel an in-progress artifact import operation.

    Stops the download process for the specified artifact revision and
    reverts its status back to SCANNED. The partially downloaded data is cleaned up.
    """)
)
async def cancel_import_artifact(
    input: CancelArtifactInput, info: Info[StrawberryGQLContext]
) -> CancelImportArtifactPayload:
    # TODO: Cancel actual import bgtask
    action_result = await info.context.processors.artifact_revision.cancel_import.wait_for_complete(
        CancelImportAction(
            artifact_revision_id=uuid.UUID(input.artifact_revision_id),
        )
    )
    return CancelImportArtifactPayload(
        artifact_revision=ArtifactRevision.from_dataclass(action_result.result)
    )


# TODO: Make this available when only having super-admin privileges
@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.14.0.

    Approve an artifact revision for general use.

    Admin-only operation to approve artifact revisions, typically used
    in environments with approval workflows for artifact deployment.
    """)
)
async def approve_artifact_revision(
    input: ApproveArtifactInput, info: Info[StrawberryGQLContext]
) -> ApproveArtifactPayload:
    action_result = await info.context.processors.artifact_revision.approve.wait_for_complete(
        ApproveArtifactRevisionAction(
            artifact_revision_id=uuid.UUID(input.artifact_revision_id),
        )
    )

    return ApproveArtifactPayload(
        artifact_revision=ArtifactRevision.from_dataclass(action_result.result)
    )


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.14.0.

    Reject an artifact revision, preventing its use.

    Admin-only operation to reject artifact revisions, typically used
    in environments with approval workflows for artifact deployment.
    """)
)
async def reject_artifact_revision(
    input: RejectArtifactInput, info: Info[StrawberryGQLContext]
) -> RejectArtifactPayload:
    action_result = await info.context.processors.artifact_revision.reject.wait_for_complete(
        RejectArtifactRevisionAction(
            artifact_revision_id=uuid.UUID(input.artifact_revision_id),
        )
    )

    return RejectArtifactPayload(
        artifact_revision=ArtifactRevision.from_dataclass(action_result.result)
    )


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.14.0.

    Perform detailed scanning of specific models.

    Unlike the general scan_artifacts operation, this performs immediate detailed
    scanning of specified models including README content and file sizes.
    Returns artifact revisions with complete metadata ready for use.
    """)
)
async def scan_artifact_models(
    input: ScanArtifactModelsInput, info: Info[StrawberryGQLContext]
) -> ScanArtifactModelsPayload:
    action_result = await info.context.processors.artifact.retrieve_models.wait_for_complete(
        RetrieveModelsAction(
            models=[m.to_dataclass() for m in input.models], registry_id=input.registry_id
        )
    )

    edges = []
    for data in action_result.result:
        edges.extend([
            ArtifactRevisionEdge(
                node=ArtifactRevision.from_dataclass(revision),
                cursor=to_global_id(ArtifactRevision, revision.id),
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
@strawberry.subscription(
    description=dedent_strip("""
    Added in 25.14.0.

    Subscribe to real-time artifact status change notifications.

    Receives updates when artifact revision statuses change during import,
    cleanup, or other operations. Useful for building reactive UIs that
    show live progress of artifact operations.
    """)
)
async def artifact_status_changed(
    input: ArtifactStatusChangedInput,
) -> AsyncGenerator[ArtifactStatusChangedPayload, None]:
    # Mock implementation
    # In real implementation, this would yield artifacts when status changes
    if False:  # Placeholder to make this a generator
        yield ArtifactStatusChangedPayload(artifact=Artifact())


@strawberry.subscription(
    description=dedent_strip("""
    Added in 25.14.0.

    Subscribe to real-time artifact import progress updates.

    Receives progress notifications during artifact import operations,
    including percentage completed and current status. Useful for displaying
    progress bars and real-time import status to users.
    """)
)
async def artifact_import_progress_updated(
    artifact_revision_id: ID,
) -> AsyncGenerator[ArtifactImportProgressUpdatedPayload, None]:
    # Mock implementation
    # In real implementation, this would yield progress updates
    if False:  # Placeholder to make this a generator
        yield ArtifactImportProgressUpdatedPayload()
