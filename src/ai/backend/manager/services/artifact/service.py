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
from ai.backend.manager.services.artifact.actions.update import (
    UpdateArtifactAction,
    UpdateArtifactActionResult,
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
        storage = await self._object_storage_repository.get_by_namespace_id(
            action.storage_namespace_id
        )
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

    async def update(self, action: UpdateArtifactAction) -> UpdateArtifactActionResult:
        updated_artifact = await self._artifact_repository.update_artifact(
            action.artifact_id, action.modifier
        )
        return UpdateArtifactActionResult(result=updated_artifact)
