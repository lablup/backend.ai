import logging
import uuid
from typing import Callable

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.dto.storage.request import ReservoirImportModelsReq
from ai.backend.common.events.event_types.artifact_registry.anycast import (
    DoPullReservoirRegistryEvent,
    DoScanReservoirRegistryEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.artifact.types import (
    ArtifactDataWithRevisions,
    ArtifactRemoteStatus,
    ArtifactStatus,
)
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.errors.artifact_registry import ReservoirConnectionError
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact.types import (
    ArtifactRemoteStatusFilter,
    ArtifactRemoteStatusFilterType,
    ArtifactRevisionFilterOptions,
    ArtifactStatusFilter,
    ArtifactStatusFilterType,
)
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.artifact.actions.scan import ScanArtifactsAction
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.types import PaginationOptions

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
                        # Ignored in reservoir types
                        artifact_type=None,
                        order=None,
                        search=None,
                        limit=None,
                    )
                )
                log.info("Completed scanning reservoir registry: {}.", registry.registry_id)
            except ReservoirConnectionError:
                log.warning(
                    "Failed to scan reservoir registry: {}.",
                    registry.registry_id,
                )

    async def handle_artifact_registry_pull(
        self, context: None, source: AgentId, event: DoPullReservoirRegistryEvent
    ) -> None:
        """
        Handle periodic pulling of artifacts from remote reservoir storage to local storage.
        """

        reservoir_config = self._config_provider.config.reservoir
        storage = await self._resolve_storage_data(reservoir_config.storage_name)
        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)

        # Get all reservoir registries
        registries = await self._artifact_registry_repository.list_artifact_registry_data()

        for registry in registries:
            if registry.type != ArtifactRegistryType.RESERVOIR:
                continue

            try:
                # Query for artifact revisions that need to be pulled
                revision_filters = ArtifactRevisionFilterOptions(
                    status_filter=ArtifactStatusFilter(
                        type=ArtifactStatusFilterType.EQUALS, values=[ArtifactStatus.SCANNED]
                    ),
                    remote_status_filter=ArtifactRemoteStatusFilter(
                        type=ArtifactRemoteStatusFilterType.EQUALS,
                        values=[ArtifactRemoteStatus.AVAILABLE],
                    ),
                )

                (
                    revisions_to_pull,
                    _,
                ) = await self._artifact_repository.list_artifact_revisions_paginated(
                    pagination=PaginationOptions(),
                    filters=revision_filters,
                )

                if not revisions_to_pull:
                    continue

                log.info(
                    "Found {} artifact revisions to pull from reservoir registry: {}",
                    len(revisions_to_pull),
                    registry.registry_id,
                )

                # Get the reservoir registry data to get the correct registry name
                reservoir_registry_data = (
                    await self._reservoir_registry_repository.get_reservoir_registry_data_by_id(
                        registry.registry_id
                    )
                )

                # Group revisions by artifact to batch import
                artifacts_to_pull: dict[uuid.UUID, ArtifactDataWithRevisions] = {}
                for revision in revisions_to_pull:
                    await self._artifact_repository.update_artifact_revision_status(
                        revision.id, ArtifactStatus.PULLING
                    )

                    artifact = await self._artifact_repository.get_artifact_by_id(
                        revision.artifact_id
                    )
                    if artifact.id not in artifacts_to_pull:
                        artifacts_to_pull[artifact.id] = ArtifactDataWithRevisions.from_dataclasses(
                            artifact_data=artifact, revisions=[]
                        )
                    artifacts_to_pull[artifact.id].revisions.append(revision)

                # Call /import API on storage proxy for artifacts that need pulling
                for artifact_data in artifacts_to_pull.values():
                    try:
                        # ArtifactDataWithRevisions provides direct access to artifact and revisions
                        # Create models list from artifact revisions
                        models: list[ModelTarget] = []
                        for revision in artifact_data.revisions:
                            models.append(
                                ModelTarget(
                                    model_id=artifact_data.name,
                                    revision=revision.version,
                                )
                            )

                        import_req = ReservoirImportModelsReq(
                            models=models,
                            registry_name=reservoir_registry_data.name,
                            storage_name=reservoir_config.storage_name,
                            storage_step_mappings=reservoir_config.storage_step_selection,
                        )

                        # Call storage proxy import API
                        import_response = await storage_proxy_client.import_reservoir_models(
                            import_req
                        )

                        log.info(
                            "Triggered import for artifact {} with {} revisions (task_id: {})",
                            artifact_data.name,
                            len(models),
                            import_response.task_id,
                        )

                    except Exception as e:
                        log.error(
                            "Failed to trigger import for artifact {} with revisions {}: {}",
                            artifact_data.name,
                            [rev.version for rev in artifact_data.revisions],
                            e,
                        )

            except Exception as e:
                log.error(
                    "Failed to pull artifacts from reservoir registry {}: {}",
                    registry.registry_id,
                    e,
                )

    async def _resolve_storage_data(self, storage_name: str) -> ObjectStorageData | VFSStorageData:
        try:
            return await self._object_storage_repository.get_by_name(storage_name)
        except Exception:
            return await self._vfs_storage_repository.get_by_name(storage_name)
