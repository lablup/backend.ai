from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.common.dto.storage.request import DeleteObjectReq, HuggingFaceImportModelsReq
from ai.backend.common.exception import ArtifactDeletionBadRequestError, ArtifactDeletionError
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.artifact.types import ArtifactStatus
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.services.artifact_revision.actions.approve import (
    ApproveArtifactRevisionAction,
    ApproveArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.associate_with_storage import (
    AssociateWithStorageAction,
    AssociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.cancel_import import (
    CancelImportAction,
    CancelImportActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.delete import (
    DeleteArtifactRevisionAction,
    DeleteArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.disassociate_with_storage import (
    DisassociateWithStorageAction,
    DisassociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.get import (
    GetArtifactRevisionAction,
    GetArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.import_revision import (
    ImportArtifactRevisionAction,
    ImportArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.list import (
    ListArtifactRevisionsAction,
    ListArtifactRevisionsActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.reject import (
    RejectArtifactRevisionAction,
    RejectArtifactRevisionActionResult,
)


class ArtifactRevisionService:
    _artifact_repository: ArtifactRepository
    _object_storage_repository: ObjectStorageRepository
    _huggingface_registry_repository: HuggingFaceRepository
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        object_storage_repository: ObjectStorageRepository,
        huggingface_registry_repository: HuggingFaceRepository,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._object_storage_repository = object_storage_repository
        self._huggingface_registry_repository = huggingface_registry_repository
        self._storage_manager = storage_manager

    async def get(self, action: GetArtifactRevisionAction) -> GetArtifactRevisionActionResult:
        revision = await self._artifact_repository.get_artifact_revision_by_id(
            action.artifact_revision_id
        )
        return GetArtifactRevisionActionResult(revision=revision)

    async def list_revision(
        self, action: ListArtifactRevisionsAction
    ) -> ListArtifactRevisionsActionResult:
        (
            artifacts_data,
            total_count,
        ) = await self._artifact_repository.list_artifact_revisions_paginated(
            pagination=action.pagination,
            ordering=action.ordering,
            filters=action.filters,
        )
        return ListArtifactRevisionsActionResult(data=artifacts_data, total_count=total_count)

    async def approve(
        self, action: ApproveArtifactRevisionAction
    ) -> ApproveArtifactRevisionActionResult:
        result = await self._artifact_repository.approve_artifact(action.artifact_revision_id)
        return ApproveArtifactRevisionActionResult(result=result)

    async def reject(
        self, action: RejectArtifactRevisionAction
    ) -> RejectArtifactRevisionActionResult:
        result = await self._artifact_repository.reject_artifact(action.artifact_revision_id)
        return RejectArtifactRevisionActionResult(result=result)

    async def associate_with_storage(
        self, action: AssociateWithStorageAction
    ) -> AssociateWithStorageActionResult:
        result = await self._artifact_repository.associate_artifact_with_storage(
            action.artifact_revision_id, action.storage_namespace_id, action.storage_type
        )
        return AssociateWithStorageActionResult(result=result)

    async def disassociate_with_storage(
        self, action: DisassociateWithStorageAction
    ) -> DisassociateWithStorageActionResult:
        result = await self._artifact_repository.disassociate_artifact_with_storage(
            action.artifact_revision_id, action.storage_namespace_id
        )
        return DisassociateWithStorageActionResult(result=result)

    async def cancel_import(self, action: CancelImportAction) -> CancelImportActionResult:
        revision_data = await self._artifact_repository.get_artifact_revision_by_id(
            action.artifact_revision_id
        )
        await self._artifact_repository.reset_artifact_revision_status(revision_data.id)
        return CancelImportActionResult(artifact_revision_id=revision_data.id)

    async def import_revision(
        self, action: ImportArtifactRevisionAction
    ) -> ImportArtifactRevisionActionResult:
        revision_data = await self._artifact_repository.get_artifact_revision_by_id(
            action.artifact_revision_id
        )
        artifact = await self._artifact_repository.get_artifact_by_id(revision_data.artifact_id)
        await self._artifact_repository.update_artifact_revision_status(
            artifact.id, ArtifactStatus.PULLING
        )
        storage = await self._object_storage_repository.get_by_namespace_id(
            action.storage_namespace_id
        )
        storage_namespace = await self._object_storage_repository.get_storage_namespace(
            action.storage_namespace_id
        )

        registry_data = (
            await self._huggingface_registry_repository.get_registry_data_by_artifact_id(
                artifact.id
            )
        )

        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)
        result = await storage_proxy_client.import_huggingface_models(
            HuggingFaceImportModelsReq(
                models=[ModelTarget(model_id=artifact.name, revision=revision_data.version)],
                registry_name=registry_data.name,
                storage_name=storage.name,
                bucket_name=storage_namespace.bucket,
            )
        )

        await self.associate_with_storage(
            AssociateWithStorageAction(
                revision_data.id, storage_namespace.id, ArtifactStorageType.OBJECT_STORAGE
            )
        )

        # TODO: Improve event-based state structure with heartbeat-based structure
        return ImportArtifactRevisionActionResult(result=revision_data, task_id=result.task_id)

    async def delete(
        self, action: DeleteArtifactRevisionAction
    ) -> DeleteArtifactRevisionActionResult:
        revision_data = await self._artifact_repository.get_artifact_revision_by_id(
            action.artifact_revision_id
        )

        if revision_data.status in [ArtifactStatus.SCANNED, ArtifactStatus.PULLING]:
            raise ArtifactDeletionBadRequestError(
                "Artifact revision status not ready to be deleted"
            )

        artifact_data = await self._artifact_repository.get_artifact_by_id(
            revision_data.artifact_id
        )

        result = await self._artifact_repository.reset_artifact_revision_status(revision_data.id)
        storage_data = await self._object_storage_repository.get_by_namespace_id(
            action.storage_namespace_id
        )
        storage_namespace = await self._object_storage_repository.get_storage_namespace(
            action.storage_namespace_id
        )
        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage_data.host)

        key = f"{artifact_data.name}/{revision_data.version}"

        try:
            await storage_proxy_client.delete_s3_file(
                storage_name=storage_data.name,
                bucket_name=storage_namespace.bucket,
                req=DeleteObjectReq(
                    key=key,
                ),
            )
        except Exception as e:
            raise ArtifactDeletionError("Failed to delete artifact from storage") from e

        await self.disassociate_with_storage(
            DisassociateWithStorageAction(
                artifact_revision_id=revision_data.id,
                storage_namespace_id=storage_namespace.id,
            )
        )

        return DeleteArtifactRevisionActionResult(artifact_revision_id=result)
