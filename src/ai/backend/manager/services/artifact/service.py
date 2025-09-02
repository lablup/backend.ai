import asyncio
import logging

from aiohttp.client_exceptions import ClientConnectorError
from pydantic import TypeAdapter

from ai.backend.common.dto.storage.request import (
    HuggingFaceScanModelsReq,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.client.artifact_registry.reservoir_client import ReservoirRegistryClient
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.artifact.types import (
    ArtifactDataWithRevisions,
    ArtifactRegistryType,
)
from ai.backend.manager.dto.request import SearchArtifactsReq
from ai.backend.manager.dto.response import SearchArtifactsResponse
from ai.backend.manager.errors.artifact_registry import (
    ArtifactRegistryBadScanRequestError,
    ReservoirConnectionError,
)
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
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
from ai.backend.manager.services.artifact.actions.list_with_revisions import (
    ListArtifactsWithRevisionsAction,
    ListArtifactsWithRevisionsActionResult,
)
from ai.backend.manager.services.artifact.actions.scan import (
    ScanArtifactsAction,
    ScanArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.update import (
    UpdateArtifactAction,
    UpdateArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.upsert_multi import (
    UpsertArtifactsAction,
    UpsertArtifactsActionResult,
)
from ai.backend.manager.types import OffsetBasedPaginationOptions, PaginationOptions

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactService:
    _artifact_repository: ArtifactRepository
    _artifact_registry_repository: ArtifactRegistryRepository
    _object_storage_repository: ObjectStorageRepository
    _huggingface_registry_repository: HuggingFaceRepository
    _reservoir_registry_repository: ReservoirRegistryRepository
    _storage_manager: StorageSessionManager
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        artifact_registry_repository: ArtifactRegistryRepository,
        object_storage_repository: ObjectStorageRepository,
        huggingface_registry_repository: HuggingFaceRepository,
        reservoir_registry_repository: ReservoirRegistryRepository,
        storage_manager: StorageSessionManager,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._artifact_registry_repository = artifact_registry_repository
        self._object_storage_repository = object_storage_repository
        self._huggingface_registry_repository = huggingface_registry_repository
        self._reservoir_registry_repository = reservoir_registry_repository
        self._storage_manager = storage_manager
        self._config_provider = config_provider

    async def scan(self, action: ScanArtifactsAction) -> ScanArtifactsActionResult:
        reservoir_config = self._config_provider.config.reservoir
        storage = await self._object_storage_repository.get_by_name(reservoir_config.storage_name)

        # TODO: Abstract remote registry client layer (scan, import)
        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)
        registry_id = action.registry_id
        registry_type = await self._artifact_registry_repository.get_artifact_registry_type(
            registry_id
        )
        scanned_models = []

        match registry_type:
            case ArtifactRegistryType.HUGGINGFACE:
                registry_data = await self._huggingface_registry_repository.get_registry_data_by_id(
                    action.registry_id
                )
                storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)

                if not (action.limit and action.order):
                    raise ArtifactRegistryBadScanRequestError()

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
            case ArtifactRegistryType.RESERVOIR:
                registry_data = (
                    await self._reservoir_registry_repository.get_reservoir_registry_data_by_id(
                        action.registry_id
                    )
                )
                remote_reservoir_client = ReservoirRegistryClient(registry_data=registry_data)

                # TODO: Apply client_decorator instead of retrying here
                offset = 0
                limit = 10
                all_artifacts: list[ArtifactDataWithRevisions] = []
                MAX_RETRIES = 3

                while True:
                    retry_count = 0
                    client_resp = None

                    while retry_count < MAX_RETRIES:
                        try:
                            req = SearchArtifactsReq(
                                pagination=PaginationOptions(
                                    offset=OffsetBasedPaginationOptions(offset=offset, limit=limit)
                                )
                            )
                            client_resp = await remote_reservoir_client.search_artifacts(req)
                            break
                        except ClientConnectorError as e:
                            retry_count += 1
                            log.warning(
                                "Cannot connect to reservoir registry: {} (attempt {}/{}). Error: {}",
                                registry_data.endpoint,
                                retry_count,
                                MAX_RETRIES,
                                e,
                            )
                            if retry_count < MAX_RETRIES:
                                await asyncio.sleep(1)

                    if client_resp is None:
                        log.warning(
                            "Failed to connect to reservoir registry after {} attempts: {}",
                            MAX_RETRIES,
                            registry_data.endpoint,
                        )
                        raise ReservoirConnectionError()

                    RespTypeAdapter = TypeAdapter(SearchArtifactsResponse)
                    parsed = RespTypeAdapter.validate_python(client_resp)

                    if not parsed.artifacts:
                        break

                    all_artifacts.extend(parsed.artifacts)

                    if len(parsed.artifacts) < limit:
                        break

                    offset += limit

                if all_artifacts:
                    for artifact_data in all_artifacts:
                        # Override registry information
                        artifact_data.artifact.registry_id = registry_id
                        artifact_data.artifact.registry_type = ArtifactRegistryType.RESERVOIR

                    upsert_result = await self.upsert_artifacts_with_revisions(
                        UpsertArtifactsAction(data=all_artifacts)
                    )
                    scanned_models = upsert_result.result

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

    async def list_with_revisions(
        self, action: ListArtifactsWithRevisionsAction
    ) -> ListArtifactsWithRevisionsActionResult:
        (
            artifacts_data,
            total_count,
        ) = await self._artifact_repository.list_artifacts_with_revisions_paginated(
            pagination=action.pagination,
            ordering=action.ordering,
            filters=action.filters,
        )
        return ListArtifactsWithRevisionsActionResult(data=artifacts_data, total_count=total_count)

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

    async def upsert_artifacts_with_revisions(
        self, action: UpsertArtifactsAction
    ) -> UpsertArtifactsActionResult:
        result_data: list[ArtifactDataWithRevisions] = []

        for artifact_with_revisions in action.data:
            # Upsert artifact first
            upserted_artifacts = await self._artifact_repository.upsert_artifacts([
                artifact_with_revisions.artifact
            ])
            upserted_artifact = upserted_artifacts[0]

            # Upsert revisions for this artifact
            upserted_revisions = await self._artifact_repository.upsert_artifact_revisions(
                artifact_with_revisions.revisions
            )

            # Combine into ArtifactDataWithRevisions
            result_data.append(
                ArtifactDataWithRevisions(artifact=upserted_artifact, revisions=upserted_revisions)
            )

        return UpsertArtifactsActionResult(result=result_data)
