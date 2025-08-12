from ai.backend.common.data.storage.registries.types import HuggingfaceConfig, ModelTarget
from ai.backend.common.dto.storage.request import HuggingFaceImportModelsReq
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.services.artifact.actions.associate_with_storage import (
    AssociateWithStorageAction,
    AssociateWithStorageActionResult,
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


class ArtifactService:
    _artifact_repository: ArtifactRepository
    _object_storage_repository: ObjectStorageRepository
    _huggingface_repository: HuggingFaceRepository
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        object_storage_repository: ObjectStorageRepository,
        huggingface_repository: HuggingFaceRepository,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._object_storage_repository = object_storage_repository
        self._huggingface_repository = huggingface_repository
        self._storage_manager = storage_manager

    async def scan(self, action: ScanArtifactsAction) -> ScanArtifactsActionResult:
        raise NotImplementedError

    async def import_(self, action: ImportArtifactAction) -> ImportArtifactActionResult:
        artifact = await self._artifact_repository.get_artifact_by_id(action.target.artifact_id)
        storage = await self._object_storage_repository.get_by_id(action.target.storage_id)
        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)

        artifact.registry_type

        client_config = HuggingfaceConfig(
            token=storage.token,
            endpoint=storage.endpoint,
        )

        resp = await storage_proxy_client.import_huggingface_model(
            HuggingFaceImportModelsReq(
                models=[ModelTarget(model_id=artifact.name, revision=artifact.version)],
                # bucket=storage.bucket_name,
                # registry_name=storage.registry_name
            )
        )
        raise NotImplementedError

    async def import_batch(self, action: ImportArtifactAction) -> ImportArtifactActionResult:
        storage_proxy_client = self._storage_manager.get_manager_facing_client(action.storage_name)
        # 우선은 DB에서 artifact에 해당하는 model name, version을 가져와야 한다.

        # resp = await storage_proxy_client.import_huggingface_model(HuggingFaceImportModelReq(
        #     model=ModelTarget(),
        #     bucket=action.bucket_name,
        #     artifact_id=action.artifact_id,
        #     storage_name=action.storage_name,
        # ))
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
