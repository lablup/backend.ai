from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.dto.storage.request import (
    HuggingFaceImportModelsReq,
    HuggingFaceScanModelsReq,
)
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.services.artifact.actions.associate_with_storage import (
    AssociateWithStorageAction,
    AssociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact.actions.authorize import (
    AuthorizeArtifactAction,
    AuthorizeArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.cancel_import import (
    CancelImportAction,
    CancelImportActionResult,
)
from ai.backend.manager.services.artifact.actions.delete import (
    DeleteArtifactAction,
    DeleteArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.disassociate_with_storage import (
    DisassociateWithStorageAction,
    DisassociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact.actions.import_ import (
    ImportArtifactAction,
    ImportArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.scan import (
    ScanArtifactsAction,
    ScanArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.unauthorize import (
    UnauthorizeArtifactAction,
    UnauthorizeArtifactActionResult,
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
        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)

        scan_result = await storage_proxy_client.scan_huggingface_models(
            HuggingFaceScanModelsReq(
                registry_name=registry_data.name,
                limit=action.limit,
                order=action.order,
                search=action.search,
            )
        )

        scanned_models = await self._artifact_repository.insert_huggingface_model_artifacts(
            scan_result.models, registry_id=registry_data.id, source_registry_id=registry_data.id
        )

        return ScanArtifactsActionResult(result=scanned_models)

    async def import_(self, action: ImportArtifactAction) -> ImportArtifactActionResult:
        artifact = await self._artifact_repository.get_artifact_by_id(action.artifact_id)
        storage = await self._object_storage_repository.get_by_id(action.storage_id)
        registry_data = (
            await self._huggingface_registry_repository.get_registry_data_by_artifact_id(
                artifact.id
            )
        )

        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)
        result = await storage_proxy_client.import_huggingface_models(
            HuggingFaceImportModelsReq(
                models=[ModelTarget(model_id=artifact.name, revision=artifact.version)],
                registry_name=registry_data.name,
                storage_name=storage.name,
                bucket_name=action.bucket_name,
            )
        )

        await self.associate_with_storage(AssociateWithStorageAction(artifact.id, storage.id))
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
        result = await self._artifact_repository.authorize_artifact(action.artifact_id)
        return AuthorizeArtifactActionResult(result=result)

    async def unauthorize(
        self, action: UnauthorizeArtifactAction
    ) -> UnauthorizeArtifactActionResult:
        result = await self._artifact_repository.unauthorize_artifact(action.artifact_id)
        return UnauthorizeArtifactActionResult(result=result)

    async def delete(self, action: DeleteArtifactAction) -> DeleteArtifactActionResult:
        result = await self._artifact_repository.delete_artifact(action.artifact_id)
        return DeleteArtifactActionResult(artifact_id=result)

    async def cancel_import(self, action: CancelImportAction) -> CancelImportActionResult:
        artifact_id = await self._artifact_repository.cancel_import_artifact(action.artifact_id)
        return CancelImportActionResult(artifact_id=artifact_id)
