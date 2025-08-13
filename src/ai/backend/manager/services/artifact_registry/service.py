# from ai.backend.common.dto.storage.request import (
#     HuggingFaceScanModelsReq,
# )
# from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
# from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
# from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
# from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
# from ai.backend.manager.services.artifact.actions.scan import (
#     ScanArtifactsAction,
#     ScanArtifactsActionResult,
# )


# # TODO: 허깅페이스 하드 코딩된 부분 인터페이스화, 공통으로 묶어 뺄 것.
# class ArtifactRegistryService:
#     _artifact_repository: ArtifactRepository
#     _object_storage_repository: ObjectStorageRepository
#     _huggingface_repository: HuggingFaceRepository
#     _storage_manager: StorageSessionManager

#     def __init__(
#         self,
#         artifact_repository: ArtifactRepository,
#         object_storage_repository: ObjectStorageRepository,
#         huggingface_repository: HuggingFaceRepository,
#         storage_manager: StorageSessionManager,
#     ) -> None:
#         self._artifact_repository = artifact_repository
#         self._object_storage_repository = object_storage_repository
#         self._huggingface_repository = huggingface_repository
#         self._storage_manager = storage_manager

#     async def scan(self, action: ScanArtifactsAction) -> ScanArtifactsActionResult:
#         storage = await self._object_storage_repository.get_by_id(action.storage_id)
#         registry_data = await self._huggingface_repository.get_registry_data_by_artifact_id(
#             action.registry_id
#         )
#         storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)

#         scan_result = await storage_proxy_client.scan_huggingface_models(
#             HuggingFaceScanModelsReq(
#                 registry_name=registry_data.name,
#                 limit=action.limit,
#                 order=action.order,
#                 search=action.search,
#             )
#         )

#         scanned_models = await self._artifact_repository.insert_huggingface_model_artifacts(
#             scan_result.models, registry_id=registry_data.id, source_registry_id=registry_data.id
#         )

#         return ScanArtifactsActionResult(result=scanned_models)
