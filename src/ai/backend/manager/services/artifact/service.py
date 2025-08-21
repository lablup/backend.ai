from ai.backend.common.dto.storage.request import (
    HuggingFaceScanModelsReq,
)
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.services.artifact.actions.get import (
    GetArtifactAction,
    GetArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.get_revisions import (
    GetArtifactRevisionsAction,
    GetArtifactRevisionsActionResult,
)
from ai.backend.manager.services.artifact.actions.list import (
    ListArtifactsAction,
    ListArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.scan import (
    ScanArtifactsAction,
    ScanArtifactsActionResult,
)


class ArtifactService:
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

    async def scan(self, action: ScanArtifactsAction) -> ScanArtifactsActionResult:
        storage = await self._object_storage_repository.get_by_id(action.storage_id)
        registry_data = await self._huggingface_registry_repository.get_registry_data_by_id(
            action.registry_id
        )
        # TODO: Abstract remote registry client layer (scan, import)
        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)

        scan_result = await storage_proxy_client.scan_huggingface_models(
            HuggingFaceScanModelsReq(
                registry_name=registry_data.name,
                limit=action.limit,
                order=action.order,
                search=action.search,
            )
        )

        # TODO: Mark artifacts which should be re-imported (updated from remote registry)?
        scanned_models = await self._artifact_repository.upsert_huggingface_model_artifacts(
            scan_result.models,
            registry_id=registry_data.id,
        )

        return ScanArtifactsActionResult(result=scanned_models)

    async def import_(self, action: ImportArtifactAction) -> ImportArtifactActionResult:
        artifact = await self._artifact_repository.get_artifact_by_id(action.artifact_id)
        await self._artifact_repository.update_artifact_revision_status(
            action.artifact_id, ArtifactStatus.PULLING
        )
        revision_row = await self._artifact_repository.get_artifact_revision(
            action.artifact_id, action.artifact_version
        )

        storage = await self._object_storage_repository.get_by_id(action.storage_id)
        registry_data = (
            await self._huggingface_registry_repository.get_registry_data_by_artifact_id(
                artifact.id
            )
        )

        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)
        result = await storage_proxy_client.import_huggingface_models(
            HuggingFaceImportModelsReq(
                models=[ModelTarget(model_id=artifact.name, revision=action.artifact_version)],
                registry_name=registry_data.name,
                storage_name=storage.name,
                bucket_name=action.bucket_name,
            )
        )

        await self.associate_with_storage(AssociateWithStorageAction(artifact.id, storage.id))
        await self._artifact_repository.update_artifact_revision_status(
            revision_row.id, ArtifactStatus.PULLED
        )

        # TODO: Add verify step
        await self._artifact_repository.update_artifact_revision_status(
            revision_row.id, ArtifactStatus.VERIFYING
        )
        await self._artifact_repository.update_artifact_revision_status(
            revision_row.id, ArtifactStatus.VERIFIED
        )
        return ImportArtifactActionResult(result=artifact, task_id=result.task_id)

    async def import_batch(self, action: ImportArtifactAction) -> ImportArtifactActionResult:
        raise NotImplementedError

    async def associate_with_storage(
        self, action: AssociateWithStorageAction
    ) -> AssociateWithStorageActionResult:
        result = await self._artifact_repository.associate_artifact_with_storage(
            action.artifact_id, action.storage_id
        )
        return AssociateWithStorageActionResult(result=result)

    async def disassociate_with_storage(
        self, action: DisassociateWithStorageAction
    ) -> DisassociateWithStorageActionResult:
        result = await self._artifact_repository.disassociate_artifact_with_storage(
            action.artifact_id, action.storage_id
        )
        return DisassociateWithStorageActionResult(result=result)

    async def authorize(self, action: AuthorizeArtifactAction) -> AuthorizeArtifactActionResult:
        artifact_data = await self._artifact_repository.get_artifact_by_id(action.artifact_id)
        if artifact_data.status != ArtifactStatus.VERIFIED:
            raise ArtifactNotVerified()

        result = await self._artifact_repository.approve_artifact(action.artifact_id)
        return AuthorizeArtifactActionResult(result=result)

    async def unauthorize(
        self, action: UnauthorizeArtifactAction
    ) -> UnauthorizeArtifactActionResult:
        # TODO: Should we reset the artifact row's status to SCANNED?
        result = await self._artifact_repository.disapprove_artifact(action.artifact_id)
        return UnauthorizeArtifactActionResult(result=result)

    async def delete(self, action: DeleteArtifactAction) -> DeleteArtifactActionResult:
        artifact_row = await self._artifact_repository.get_artifact_by_id(action.artifact_id)
        revision_row = await self._artifact_repository.get_artifact_revision(
            action.artifact_id, action.artifact_version
        )

        if revision_row.status in [ArtifactStatus.SCANNED, ArtifactStatus.PULLING]:
            raise ArtifactDeletionBadRequestError(
                "Artifact revision status not ready to be deleted"
            )

        result = await self._artifact_repository.reset_artifact_revision_status(revision_row.id)
        storage_data = await self._object_storage_repository.get_by_id(action.storage_id)
        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage_data.host)

        key = f"{artifact_row.name}/{action.artifact_version}"

        try:
            await storage_proxy_client.delete_s3_file(
                storage_name=storage_data.name,
                bucket_name=action.bucket_name,
                req=DeleteObjectReq(
                    key=key,
                ),
            )
        except Exception as e:
            raise ArtifactDeletionError("Failed to delete artifact from storage") from e

        return DeleteArtifactActionResult(artifact_id=result)

    async def cancel_import(self, action: CancelImportAction) -> CancelImportActionResult:
        revision_row = await self._artifact_repository.get_artifact_revision(
            action.artifact_id, action.artifact_version
        )

        artifact_id = await self._artifact_repository.reset_artifact_revision_status(
            revision_row.id
        )
        return CancelImportActionResult(artifact_id=artifact_id)

    async def get(self, action: GetArtifactAction) -> GetArtifactActionResult:
        artifact = await self._artifact_repository.get_artifact_by_id(action.artifact_id)
        return GetArtifactActionResult(result=artifact)

    async def list(self, action: ListArtifactsAction) -> ListArtifactsActionResult:
        artifacts_data, total_count = await self._artifact_repository.list_artifacts_paginated(
            pagination=action.pagination,
            ordering=action.ordering,
            filters=action.filters,
        )
        return ListArtifactsActionResult(data=artifacts_data, total_count=total_count)

    async def get_revisions(
        self, action: GetArtifactRevisionsAction
    ) -> GetArtifactRevisionsActionResult:
        revisions = await self._artifact_repository.list_artifact_revisions(action.artifact_id)
        return GetArtifactRevisionsActionResult(revisions=revisions)
