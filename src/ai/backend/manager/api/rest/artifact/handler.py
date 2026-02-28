"""Artifact handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``PathParam``, ``ProcessorsCtx``) are automatically
extracted by ``_wrap_api_handler`` and responses are returned as
``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.storage.request import GetVerificationResultReq
from ai.backend.common.dto.storage.response import GetVerificationResultResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import ArtifactRevisionResponseData
from ai.backend.manager.dto.request import (
    ApproveArtifactRevisionReq,
    CancelImportArtifactReq,
    CleanupArtifactsReq,
    GetArtifactRevisionReadmeReq,
    GetDownloadProgressReqPathParam,
    ImportArtifactsReq,
    RejectArtifactRevisionReq,
    UpdateArtifactReqBodyParam,
    UpdateArtifactReqPathParam,
)
from ai.backend.manager.dto.response import (
    ApproveArtifactRevisionResponse,
    ArtifactRevisionImportTask,
    CancelImportArtifactResponse,
    CleanupArtifactsResponse,
    GetArtifactRevisionReadmeResponse,
    GetDownloadProgressResponse,
    ImportArtifactsResponse,
    RejectArtifactRevisionResponse,
    UpdateArtifactResponse,
)
from ai.backend.manager.services.artifact.actions.update import UpdateArtifactAction
from ai.backend.manager.services.artifact_revision.actions.approve import (
    ApproveArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.cancel_import import (
    CancelImportAction,
)
from ai.backend.manager.services.artifact_revision.actions.cleanup import (
    CleanupArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.get_download_progress import (
    GetDownloadProgressAction,
)
from ai.backend.manager.services.artifact_revision.actions.get_readme import (
    GetArtifactRevisionReadmeAction,
)
from ai.backend.manager.services.artifact_revision.actions.get_verification_result import (
    GetArtifactRevisionVerificationResultAction,
)
from ai.backend.manager.services.artifact_revision.actions.import_revision import (
    ImportArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.reject import (
    RejectArtifactRevisionAction,
)

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactHandler:
    """Artifact API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors | None = None) -> None:
        self._processors_ref = processors

    def bind_processors(self, processors: Processors) -> None:
        """Late-bind processors for backward-compatible create_app() usage."""
        self._processors_ref = processors

    @property
    def _processors(self) -> Processors:
        if self._processors_ref is None:
            raise RuntimeError(
                "Processors not bound. Pass processors= to __init__ or call bind_processors()."
            )
        return self._processors_ref

    async def cleanup_artifacts(
        self,
        body: BodyParam[CleanupArtifactsReq],
    ) -> APIResponse:
        """
        Clean up stored artifact revision data to free storage space.

        Removes the downloaded files for the specified artifact revisions and
        transitions them back to SCANNED status. The metadata remains, allowing
        the artifacts to be re-imported later if needed.

        Use this operation to manage storage usage by removing unused artifacts.
        """
        processors = self._processors
        cleaned_revisions = []

        # Process each artifact revision sequentially
        # TODO: Optimize with asyncio.gather() for parallel processing
        for artifact_revision_id in body.parsed.artifact_revision_ids:
            action_result = await processors.artifact_revision.cleanup.wait_for_complete(
                CleanupArtifactRevisionAction(
                    artifact_revision_id=artifact_revision_id,
                )
            )
            cleaned_revisions.append(action_result.result)

        resp = CleanupArtifactsResponse(
            artifact_revisions=[
                ArtifactRevisionResponseData.from_revision_data(revision)
                for revision in cleaned_revisions
            ],
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def cancel_import_artifact(
        self,
        body: BodyParam[CancelImportArtifactReq],
    ) -> APIResponse:
        """
        Cancel an in-progress artifact import operation.

        Stops the download process for the specified artifact revision and
        reverts its status back to SCANNED. The partially downloaded data is cleaned up.
        """
        processors = self._processors
        action_result = await processors.artifact_revision.cancel_import.wait_for_complete(
            CancelImportAction(
                artifact_revision_id=body.parsed.artifact_revision_id,
            )
        )

        resp = CancelImportArtifactResponse(
            artifact_revision=ArtifactRevisionResponseData.from_revision_data(action_result.result),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def approve_artifact_revision(
        self,
        path: PathParam[ApproveArtifactRevisionReq],
    ) -> APIResponse:
        """
        Approve an artifact revision for general use.

        Admin-only operation to approve artifact revisions, typically used
        in environments with approval workflows for artifact deployment.
        """
        processors = self._processors
        action_result = await processors.artifact_revision.approve.wait_for_complete(
            ApproveArtifactRevisionAction(
                artifact_revision_id=path.parsed.artifact_revision_id,
            )
        )

        resp = ApproveArtifactRevisionResponse(
            artifact_revision=ArtifactRevisionResponseData.from_revision_data(action_result.result),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def reject_artifact_revision(
        self,
        path: PathParam[RejectArtifactRevisionReq],
    ) -> APIResponse:
        """
        Reject an artifact revision, preventing its use.

        Admin-only operation to reject artifact revisions, typically used
        in environments with approval workflows for artifact deployment.
        """
        processors = self._processors
        action_result = await processors.artifact_revision.reject.wait_for_complete(
            RejectArtifactRevisionAction(
                artifact_revision_id=path.parsed.artifact_revision_id,
            )
        )

        resp = RejectArtifactRevisionResponse(
            artifact_revision=ArtifactRevisionResponseData.from_revision_data(action_result.result),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def import_artifacts(
        self,
        body: BodyParam[ImportArtifactsReq],
    ) -> APIResponse:
        """
        Import scanned artifact revisions from external registries.

        Downloads the actual files for the specified artifact revisions, transitioning
        them from SCANNED -> PULLING -> PULLED -> AVAILABLE status.

        Returns background tasks that can be monitored for import progress.
        Once AVAILABLE, artifacts can be used by users in their sessions.
        """
        processors = self._processors
        imported_revisions = []
        tasks = []

        # Process each artifact revision sequentially
        # TODO: Optimize with asyncio.gather() for parallel processing
        force = body.parsed.options.force if body.parsed.options else False
        for artifact_revision_id in body.parsed.artifact_revision_ids:
            # When using VFolderStorage (vfolder_id provided), store at root path
            storage_prefix = "/" if body.parsed.vfolder_id else None
            action_result = await processors.artifact_revision.import_revision.wait_for_complete(
                ImportArtifactRevisionAction(
                    artifact_revision_id=artifact_revision_id,
                    vfolder_id=body.parsed.vfolder_id,
                    storage_prefix=storage_prefix,
                    force=force,
                )
            )
            imported_revisions.append(action_result.result)
            tasks.append(
                ArtifactRevisionImportTask(
                    task_id=str(action_result.task_id),
                    artifact_revision=ArtifactRevisionResponseData.from_revision_data(
                        action_result.result
                    ),
                )
            )

        resp = ImportArtifactsResponse(tasks=tasks)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def update_artifact(
        self,
        path: PathParam[UpdateArtifactReqPathParam],
        body: BodyParam[UpdateArtifactReqBodyParam],
    ) -> APIResponse:
        """
        Update artifact metadata properties.

        Modifies artifact metadata such as readonly status and description.
        This operation does not affect the actual artifact files or revisions.
        """
        processors = self._processors
        action_result = await processors.artifact.update.wait_for_complete(
            UpdateArtifactAction(
                updater=body.parsed.to_updater(path.parsed.artifact_id),
            )
        )

        resp = UpdateArtifactResponse(
            artifact=action_result.result,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_artifact_revision_readme(
        self,
        path: PathParam[GetArtifactRevisionReadmeReq],
    ) -> APIResponse:
        """
        Retrieve the README content for a specific artifact revision.

        Returns the README documentation associated with the artifact revision,
        which typically contains usage instructions and model information.
        """
        processors = self._processors
        action_result = await processors.artifact_revision.get_readme.wait_for_complete(
            GetArtifactRevisionReadmeAction(
                artifact_revision_id=path.parsed.artifact_revision_id,
            )
        )

        resp = GetArtifactRevisionReadmeResponse(
            readme=action_result.readme_data.readme,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_artifact_revision_verification_result(
        self,
        path: PathParam[GetVerificationResultReq],
    ) -> APIResponse:
        """
        Retrieve the verification result for a specific artifact revision.

        Returns the verification result data associated with the artifact revision,
        which contains results from all verifiers that have been run on the artifact.
        """
        processors = self._processors
        action_result = (
            await processors.artifact_revision.get_verification_result.wait_for_complete(
                GetArtifactRevisionVerificationResultAction(
                    artifact_revision_id=path.parsed.artifact_revision_id,
                )
            )
        )

        resp = GetVerificationResultResponse(
            verification_result=action_result.verification_result,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_download_progress(
        self,
        path: PathParam[GetDownloadProgressReqPathParam],
    ) -> APIResponse:
        """
        Retrieve download progress for an artifact revision.

        Returns detailed download progress information including artifact-level
        and file-level progress data for the specified artifact revision.
        Supports both local and remote download progress when delegation is enabled.
        """
        processors = self._processors
        action_result = await processors.artifact_revision.get_download_progress.wait_for_complete(
            GetDownloadProgressAction(
                artifact_revision_id=path.parsed.artifact_revision_id,
            )
        )

        resp = GetDownloadProgressResponse(
            download_progress=action_result.download_progress,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
