import logging

from pydantic import TypeAdapter

from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.common.dto.manager.response import (
    ArtifactInstalledStoragesResponse,
    GetPresignedDownloadURLResponse,
)
from ai.backend.common.dto.storage.request import PullObjectReq
from ai.backend.common.events.event_types.artifact_registry.anycast import (
    DoScanArtifactRegistryEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.client.manager_client import ManagerFacingClient
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.reservoir.repository import ReservoirRegistryRepository
from ai.backend.manager.services.artifact.actions.scan import ScanArtifactsAction
from ai.backend.manager.services.processors import Processors

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactRegistryEventHandler:
    _processors: Processors
    _artifact_repository: ArtifactRepository
    _artifact_registry_repository: ArtifactRegistryRepository
    _reservoir_registry_repository: ReservoirRegistryRepository
    _object_storage_repository: ObjectStorageRepository
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        processors: Processors,
        artifact_repository: ArtifactRepository,
        artifact_registry_repository: ArtifactRegistryRepository,
        reservoir_registry_repository: ReservoirRegistryRepository,
        object_storage_repository: ObjectStorageRepository,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._processors = processors
        self._artifact_repository = artifact_repository
        self._artifact_registry_repository = artifact_registry_repository
        self._reservoir_registry_repository = reservoir_registry_repository
        self._object_storage_repository = object_storage_repository
        self._storage_manager = storage_manager

    async def handle_artifact_registry_scan(
        self, context: None, source: AgentId, event: DoScanArtifactRegistryEvent
    ) -> None:
        print("Handling artifact registry scan event")
        registries = await self._artifact_registry_repository.list_artifact_registry_data()
        object_storages = await self._object_storage_repository.list_object_storages()

        # For now, we just pick first storage's first bucket
        storage = object_storages[0]
        storage_namespaces = await self._object_storage_repository.get_buckets(storage.id)
        storage_namespace = storage_namespaces[0]

        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)

        for registry in registries:
            if registry.type != ArtifactRegistryType.RESERVOIR:
                continue

            self._artifact_registry_repository.get_artifact_registry_data

            scan_result = await self._processors.artifact.scan.wait_for_complete(
                ScanArtifactsAction(
                    registry_id=registry.registry_id,
                    storage_namespace_id=storage_namespace.id,
                    order=ModelSortKey.DOWNLOADS,
                    # Ignored in reservoir types
                    limit=-1,
                    search=None,
                )
            )

            artifacts = scan_result.result
            registry_data = (
                await self._reservoir_registry_repository.get_reservoir_registry_data_by_id(
                    registry.registry_id
                )
            )

            remote_reservoir_client = ManagerFacingClient(registry_data=registry_data)

            for artifact in artifacts:
                # 우선 아티팩트 리비전이 설치된 위치를 한 요청을 통해 얻고...
                client_resp = await remote_reservoir_client.request(
                    "GET",
                    "/artifacts/installed-storages",
                )
                RespTypeAdapter = TypeAdapter(ArtifactInstalledStoragesResponse)
                parsed = RespTypeAdapter.validate_python(client_resp)
                installed_storage_mapping = parsed.installed_storages

                for revision in artifact.revisions:
                    storage_namespace_id = installed_storage_mapping[revision.id]

                    # 매니저를 통해 download url을 얻고..
                    client_resp = await remote_reservoir_client.request(
                        "GET",
                        "/object-storages/presigned/download",
                        json={
                            "artifact_revision_id": revision.id,
                            # TODO: 이제 이거 같이 전달할 필요 X 뺄 것.
                            "storage_namespace_id": storage_namespace_id,
                            "key": ".",
                        },
                    )

                    RespTypeAdapter = TypeAdapter(GetPresignedDownloadURLResponse)
                    parsed = RespTypeAdapter.validate_python(client_resp)
                    presigned_url = parsed.presigned_url

                    try:
                        # pull 요청.
                        await storage_proxy_client.pull_s3_file(
                            storage.name,
                            storage_namespace.bucket,
                            PullObjectReq(url=presigned_url, key="."),
                        )
                    except Exception:
                        log.error("Failed to pull S3 file")
                        raise
