from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
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
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._storage_manager = storage_manager

    async def scan(self, action: ScanArtifactsAction) -> ScanArtifactsActionResult:
        raise NotImplementedError

    async def import_(self, action: ImportArtifactAction) -> ImportArtifactActionResult:
        storage_proxy_client = self._storage_manager.get_manager_facing_client(action.storage_name)
        # 우선은 DB에서 artifact에 해당하는 model name, version을 가져와야 한다.

        # resp = await storage_proxy_client.import_huggingface_model(HuggingFaceImportModelReq(
        #     model=ModelTarget(),
        #     bucket=action.bucket_name,
        #     artifact_id=action.artifact_id,
        #     storage_name=action.storage_name,
        # ))
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
