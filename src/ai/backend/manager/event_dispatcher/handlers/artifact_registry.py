import logging
from typing import Callable

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.events.event_types.artifact_registry.anycast import (
    DoScanReservoirRegistryEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.artifact.types import (
    ArtifactType,
)
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.errors.artifact_registry import ReservoirConnectionError
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.artifact.actions.scan import ScanArtifactsAction
from ai.backend.manager.services.processors import Processors

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactRegistryEventHandler:
    _processors_factory: Callable[[], Processors]
    _artifact_repository: ArtifactRepository
    _artifact_registry_repository: ArtifactRegistryRepository
    _reservoir_registry_repository: ReservoirRegistryRepository
    _object_storage_repository: ObjectStorageRepository
    _vfs_storage_repository: VFSStorageRepository
    _storage_manager: StorageSessionManager
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        processors_factory: Callable[[], Processors],
        artifact_repository: ArtifactRepository,
        artifact_registry_repository: ArtifactRegistryRepository,
        reservoir_registry_repository: ReservoirRegistryRepository,
        object_storage_repository: ObjectStorageRepository,
        vfs_storage_repository: VFSStorageRepository,
        storage_manager: StorageSessionManager,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._processors_factory = processors_factory
        self._artifact_repository = artifact_repository
        self._artifact_registry_repository = artifact_registry_repository
        self._reservoir_registry_repository = reservoir_registry_repository
        self._object_storage_repository = object_storage_repository
        self._vfs_storage_repository = vfs_storage_repository
        self._storage_manager = storage_manager
        self._config_provider = config_provider

    async def handle_artifact_registry_scan(
        self, context: None, source: AgentId, event: DoScanReservoirRegistryEvent
    ) -> None:
        processors = self._processors_factory()
        registries = await self._artifact_registry_repository.list_artifact_registry_data()

        for registry in registries:
            if registry.type != ArtifactRegistryType.RESERVOIR:
                continue

            try:
                await processors.artifact.scan.wait_for_complete(
                    ScanArtifactsAction(
                        registry_id=registry.registry_id,
                        # TODO: Support other artifact types in the future
                        artifact_type=ArtifactType.MODEL,
                        # Fetch all artifacts without limit
                        limit=None,
                        order=None,
                        search=None,
                    )
                )
                log.info("Completed scanning reservoir registry: {}.", registry.registry_id)
            except ReservoirConnectionError:
                log.warning(
                    "Failed to scan reservoir registry: {}.",
                    registry.registry_id,
                )

    async def _resolve_storage_data(self, storage_name: str) -> ObjectStorageData | VFSStorageData:
        try:
            return await self._object_storage_repository.get_by_name(storage_name)
        except Exception:
            return await self._vfs_storage_repository.get_by_name(storage_name)
