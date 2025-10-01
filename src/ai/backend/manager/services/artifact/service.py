import asyncio
import logging
import uuid
from typing import Optional

from aiohttp.client_exceptions import ClientConnectorError
from pydantic import TypeAdapter

from ai.backend.common.dto.storage.request import (
    HuggingFaceRetrieveModelReqPathParam,
    HuggingFaceRetrieveModelReqQueryParam,
    HuggingFaceRetrieveModelsReq,
    HuggingFaceScanModelsReq,
    HuggingFaceScanModelsSyncReq,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.client.artifact_registry.reservoir_client import ReservoirRegistryClient
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.artifact.types import (
    ArtifactDataWithRevisions,
    ArtifactRegistryType,
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactRevisionReadme,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.dto.request import (
    DelegateScanArtifactsReq,
    SearchArtifactsReq,
)
from ai.backend.manager.dto.response import (
    DelegateScanArtifactsResponse,
    SearchArtifactsResponse,
)
from ai.backend.manager.errors.artifact_registry import (
    ArtifactRegistryBadScanRequestError,
    RemoteReservoirScanError,
    ReservoirConnectionError,
)
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.services.artifact.actions.delegate_scan import (
    DelegateScanArtifactsAction,
    DelegateScanArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.delete_multi import (
    DeleteArtifactsAction,
    DeleteArtifactsActionResult,
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
from ai.backend.manager.services.artifact.actions.restore_multi import (
    RestoreArtifactsAction,
    RestoreArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.retrieve_model import (
    RetrieveModelAction,
    RetrieveModelActionResult,
)
from ai.backend.manager.services.artifact.actions.retrieve_model_multi import (
    RetrieveModelsAction,
    RetrieveModelsActionResult,
)
from ai.backend.manager.services.artifact.actions.scan import (
    ScanArtifactsAction,
    ScanArtifactsActionResult,
)
from ai.backend.manager.services.artifact.actions.scan_sync import (
    ScanArtifactsSyncAction,
    ScanArtifactsSyncActionResult,
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

        registry_meta = await self._resolve_artifact_registry_meta(
            action.artifact_type, action.registry_id
        )
        registry_type = registry_meta.type
        registry_id = registry_meta.registry_id

        scanned_models = []

        match registry_type:
            case ArtifactRegistryType.HUGGINGFACE:
                registry_data = await self._huggingface_registry_repository.get_registry_data_by_id(
                    registry_id
                )
                storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)

                if not (action.limit and action.order):
                    raise ArtifactRegistryBadScanRequestError(
                        "Invalid scan request, one of `limit` or `order` argument required"
                    )

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
                        registry_id
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

                    # Convert response data back to full data with readme
                    for response_artifact in parsed.artifacts:
                        # Convert response revisions back to full revisions
                        full_revisions = []
                        for response_revision in response_artifact.revisions:
                            # Get readme for this revision from reservoir
                            try:
                                readme_resp = await remote_reservoir_client.get_readme(
                                    response_revision.id
                                )
                                readme = readme_resp.readme
                            except Exception as e:
                                log.warning(
                                    "Failed to fetch readme for artifact {} revision {}: {}",
                                    response_revision.artifact_id,
                                    response_revision.version,
                                    e,
                                )
                                readme = None

                            # Create full revision data with readme
                            full_revision = ArtifactRevisionData(
                                id=response_revision.id,
                                artifact_id=response_revision.artifact_id,
                                version=response_revision.version,
                                readme=readme,
                                size=response_revision.size,
                                status=response_revision.status,
                                remote_status=None,
                                created_at=response_revision.created_at,
                                updated_at=response_revision.updated_at,
                            )
                            full_revisions.append(full_revision)

                        # Create full artifact data
                        full_artifact = ArtifactDataWithRevisions(
                            id=response_artifact.id,
                            name=response_artifact.name,
                            type=response_artifact.type,
                            description=response_artifact.description,
                            registry_id=response_artifact.registry_id,
                            source_registry_id=response_artifact.source_registry_id,
                            registry_type=response_artifact.registry_type,
                            source_registry_type=response_artifact.source_registry_type,
                            scanned_at=response_artifact.scanned_at,
                            updated_at=response_artifact.updated_at,
                            readonly=response_artifact.readonly,
                            availability=response_artifact.availability,
                            revisions=full_revisions,
                        )
                        all_artifacts.append(full_artifact)

                    if len(parsed.artifacts) < limit:
                        break

                    offset += limit

                if all_artifacts:
                    for artifact_data in all_artifacts:
                        # Override registry information
                        artifact_data.registry_id = registry_id
                        artifact_data.registry_type = ArtifactRegistryType.RESERVOIR

                    upsert_result = await self.upsert_artifacts_with_revisions(
                        UpsertArtifactsAction(data=all_artifacts)
                    )
                    scanned_models = upsert_result.result

        return ScanArtifactsActionResult(result=scanned_models)

    # TODO: Remove code duplication with scan by adding an appropriate abstraction layer.
    async def scan_sync(self, action: ScanArtifactsSyncAction) -> ScanArtifactsSyncActionResult:
        """
        This action scans and returns all metadata, including readme, size, and other information
        """
        reservoir_config = self._config_provider.config.reservoir
        storage = await self._object_storage_repository.get_by_name(reservoir_config.storage_name)

        # TODO: Abstract remote registry client layer (scan, import)
        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)

        registry_meta = await self._resolve_artifact_registry_meta(
            action.artifact_type, action.registry_id
        )
        registry_type = registry_meta.type
        registry_id = registry_meta.registry_id

        scanned_models = []

        match registry_type:
            case ArtifactRegistryType.HUGGINGFACE:
                registry_data = await self._huggingface_registry_repository.get_registry_data_by_id(
                    registry_id
                )
                storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)

                if not (action.limit and action.order):
                    raise ArtifactRegistryBadScanRequestError(
                        "Invalid scan request, one of `limit` or `order` argument required"
                    )

                scan_result = await storage_proxy_client.scan_huggingface_models_sync(
                    HuggingFaceScanModelsSyncReq(
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
                        registry_id
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

                    # Convert response data back to full data with readme
                    for response_artifact in parsed.artifacts:
                        # Convert response revisions back to full revisions
                        full_revisions = []
                        for response_revision in response_artifact.revisions:
                            # Get readme for this revision from reservoir
                            try:
                                readme_resp = await remote_reservoir_client.get_readme(
                                    response_revision.id
                                )
                                readme = readme_resp.readme
                            except Exception as e:
                                log.warning(
                                    "Failed to fetch readme for artifact {} revision {}: {}",
                                    response_revision.artifact_id,
                                    response_revision.version,
                                    e,
                                )
                                readme = None

                            # Create full revision data with readme
                            full_revision = ArtifactRevisionData(
                                id=response_revision.id,
                                artifact_id=response_revision.artifact_id,
                                version=response_revision.version,
                                readme=readme,
                                size=response_revision.size,
                                status=response_revision.status,
                                remote_status=None,
                                created_at=response_revision.created_at,
                                updated_at=response_revision.updated_at,
                            )
                            full_revisions.append(full_revision)

                        # Create full artifact data
                        full_artifact = ArtifactDataWithRevisions(
                            id=response_artifact.id,
                            name=response_artifact.name,
                            type=response_artifact.type,
                            description=response_artifact.description,
                            registry_id=response_artifact.registry_id,
                            source_registry_id=response_artifact.source_registry_id,
                            registry_type=response_artifact.registry_type,
                            source_registry_type=response_artifact.source_registry_type,
                            scanned_at=response_artifact.scanned_at,
                            updated_at=response_artifact.updated_at,
                            readonly=response_artifact.readonly,
                            availability=response_artifact.availability,
                            revisions=full_revisions,
                        )
                        all_artifacts.append(full_artifact)

                    if len(parsed.artifacts) < limit:
                        break

                    offset += limit

                if all_artifacts:
                    for artifact_data in all_artifacts:
                        # Override registry information
                        artifact_data.registry_id = registry_id
                        artifact_data.registry_type = ArtifactRegistryType.RESERVOIR

                    upsert_result = await self.upsert_artifacts_with_revisions(
                        UpsertArtifactsAction(data=all_artifacts)
                    )
                    scanned_models = upsert_result.result

        return ScanArtifactsSyncActionResult(result=scanned_models)

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
                artifact_with_revisions
            ])
            upserted_artifact = upserted_artifacts[0]

            # Upsert revisions for this artifact
            upserted_revisions = await self._artifact_repository.upsert_artifact_revisions(
                artifact_with_revisions.revisions
            )

            # Combine into ArtifactDataWithRevisions
            result_data.append(
                ArtifactDataWithRevisions.from_dataclasses(
                    artifact_data=upserted_artifact, revisions=upserted_revisions
                )
            )

        return UpsertArtifactsActionResult(result=result_data)

    async def retrieve_models(self, action: RetrieveModelsAction) -> RetrieveModelsActionResult:
        registry_meta = await self._resolve_artifact_registry_meta(
            ArtifactType.MODEL, action.registry_id
        )
        registry_type = registry_meta.type
        registry_id = registry_meta.registry_id

        if registry_type != ArtifactRegistryType.HUGGINGFACE:
            raise NotImplementedError("Only HuggingFace registry is supported for model retrieval")

        reservoir_config = self._config_provider.config.reservoir
        storage = await self._object_storage_repository.get_by_name(reservoir_config.storage_name)

        # TODO: Abstract remote registry client layer (scan, import)
        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)

        registry_data = await self._huggingface_registry_repository.get_registry_data_by_id(
            registry_id
        )

        req = HuggingFaceRetrieveModelsReq(
            registry_name=registry_data.name,
            models=action.models,
        )
        resp = await storage_proxy_client.retrieve_huggingface_models(req)
        scanned_models = await self._artifact_repository.upsert_huggingface_model_artifacts(
            resp.models,
            registry_id=registry_data.id,
        )

        return RetrieveModelsActionResult(result=scanned_models)

    async def retrieve_single_model(self, action: RetrieveModelAction) -> RetrieveModelActionResult:
        registry_meta = await self._resolve_artifact_registry_meta(
            ArtifactType.MODEL, action.registry_id
        )
        registry_type = registry_meta.type
        registry_id = registry_meta.registry_id

        if registry_type != ArtifactRegistryType.HUGGINGFACE:
            raise NotImplementedError("Only HuggingFace registry is supported for model retrieval")

        reservoir_config = self._config_provider.config.reservoir
        storage = await self._object_storage_repository.get_by_name(reservoir_config.storage_name)

        # TODO: Abstract remote registry client layer (scan, import)
        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage.host)

        registry_data = await self._huggingface_registry_repository.get_registry_data_by_id(
            registry_id
        )

        path = HuggingFaceRetrieveModelReqPathParam(
            model_id=action.model.model_id,
        )
        query = HuggingFaceRetrieveModelReqQueryParam(
            registry_name=registry_data.name,
            revision=action.model.resolve_revision(ArtifactRegistryType.HUGGINGFACE),
        )

        resp = await storage_proxy_client.retrieve_huggingface_model(path, query)
        scanned_models = await self._artifact_repository.upsert_huggingface_model_artifacts(
            [resp.model],
            registry_id=registry_data.id,
        )

        return RetrieveModelActionResult(result=scanned_models[0])

    async def delete_artifacts(self, action: DeleteArtifactsAction) -> DeleteArtifactsActionResult:
        deleted_artifacts = await self._artifact_repository.delete_artifacts(action.artifact_ids)
        return DeleteArtifactsActionResult(artifacts=deleted_artifacts)

    async def restore_artifacts(
        self, action: RestoreArtifactsAction
    ) -> RestoreArtifactsActionResult:
        restored_artifacts = await self._artifact_repository.restore_artifacts(action.artifact_ids)
        return RestoreArtifactsActionResult(artifacts=restored_artifacts)

    async def _resolve_artifact_registry_meta(
        self, artifact_type: Optional[ArtifactType], registry_id_or_none: Optional[uuid.UUID]
    ) -> ArtifactRegistryData:
        if registry_id_or_none is None:
            # TODO: Handle `artifact_type` for other types
            registry_name = self._config_provider.config.artifact_registry.model_registry
            registry_meta = (
                await self._artifact_registry_repository.get_artifact_registry_data_by_name(
                    registry_name
                )
            )
        else:
            registry_id = registry_id_or_none
            registry_meta = await self._artifact_registry_repository.get_artifact_registry_data(
                registry_id
            )

        return registry_meta

    async def delegate_scan_artifacts(
        self, action: DelegateScanArtifactsAction
    ) -> DelegateScanArtifactsActionResult:
        # If this is a leaf node, perform local scan instead of delegation
        if self._config_provider.config.reservoir.is_delegation_leaf:
            registry_id = None
            if action.delegatee_target:
                registry_id = action.delegatee_target.target_registry_id

            registry_meta = await self._resolve_artifact_registry_meta(
                action.artifact_type, registry_id
            )
            target_registry_id = registry_meta.registry_id

            try:
                scan_result = await self.scan_sync(
                    ScanArtifactsSyncAction(
                        artifact_type=action.artifact_type,
                        registry_id=target_registry_id,
                        limit=action.limit,
                        order=action.order,
                        search=action.search,
                    )
                )
            except Exception as e:
                raise RemoteReservoirScanError(
                    f"Failed to scan artifacts from remote reservoir: {e}"
                ) from e

            readme_data = {
                rev.id: ArtifactRevisionReadme(readme=rev.readme)
                for artifact in scan_result.result
                for rev in artifact.revisions
            }
            return DelegateScanArtifactsActionResult(
                result=scan_result.result,
                source_registry_id=target_registry_id,
                source_registry_type=registry_meta.type,
                readme_data=readme_data,
            )

        # If not a leaf node, perform delegation to remote reservoir
        registry_meta = await self._resolve_artifact_registry_meta(
            action.artifact_type, action.delegator_reservoir_id
        )
        registry_type = registry_meta.type
        registry_id = registry_meta.registry_id

        if registry_type != ArtifactRegistryType.RESERVOIR:
            raise ArtifactRegistryBadScanRequestError(
                "Only Reservoir type registry is supported for delegated scan"
            )

        registry_data = await self._reservoir_registry_repository.get_reservoir_registry_data_by_id(
            registry_id
        )

        remote_reservoir_client = ReservoirRegistryClient(registry_data=registry_data)

        if not (action.limit and action.order):
            raise ArtifactRegistryBadScanRequestError(
                "Invalid scan request, one of `limit` or `order` argument required"
            )

        # Pass delegatee_reservoir_id to delegator_reservoir_id
        delegatee_reservoir_id = (
            action.delegatee_target.delegatee_reservoir_id if action.delegatee_target else None
        )
        req = DelegateScanArtifactsReq(
            delegator_reservoir_id=delegatee_reservoir_id,
            delegatee_target=action.delegatee_target,
            artifact_type=action.artifact_type,
            limit=action.limit,
            search=action.search,
            order=action.order,
        )
        client_resp = await remote_reservoir_client.delegate_scan_artifacts(req)

        if client_resp is None:
            log.warning(
                "Failed to connect to reservoir registry after {}",
                registry_data.endpoint,
            )
            raise ReservoirConnectionError("Failed to connect to remote reservoir")

        RespTypeAdapter = TypeAdapter(DelegateScanArtifactsResponse)
        parsed_resp = RespTypeAdapter.validate_python(client_resp)

        all_artifacts: list[ArtifactDataWithRevisions] = []

        # Convert response data back to full data with readme
        for response_artifact in parsed_resp.artifacts:
            # Convert response revisions back to full revisions
            full_revisions: list[ArtifactRevisionData] = []

            for response_revision in response_artifact.revisions:
                readme = parsed_resp.readme_data[response_revision.id]

                remote_status = ArtifactRemoteStatus.SCANNED
                if response_revision.status == ArtifactStatus.AVAILABLE:
                    remote_status = ArtifactRemoteStatus.AVAILABLE

                full_revision = ArtifactRevisionData(
                    id=response_revision.id,
                    artifact_id=response_revision.artifact_id,
                    version=response_revision.version,
                    readme=readme.readme,
                    size=response_revision.size,
                    status=ArtifactStatus.SCANNED,  # Reset status to SCANNED
                    remote_status=remote_status,
                    created_at=response_revision.created_at,
                    updated_at=response_revision.updated_at,
                )
                full_revisions.append(full_revision)

            # Create full artifact data
            full_artifact = ArtifactDataWithRevisions(
                id=response_artifact.id,
                name=response_artifact.name,
                type=response_artifact.type,
                description=response_artifact.description,
                registry_id=response_artifact.registry_id,
                source_registry_id=response_artifact.source_registry_id,
                registry_type=response_artifact.registry_type,
                source_registry_type=response_artifact.source_registry_type,
                scanned_at=response_artifact.scanned_at,
                updated_at=response_artifact.updated_at,
                readonly=response_artifact.readonly,
                availability=response_artifact.availability,
                revisions=full_revisions,
            )
            all_artifacts.append(full_artifact)

        scanned_models = []
        if all_artifacts:
            for artifact_data in all_artifacts:
                # Override registry information
                artifact_data.source_registry_id = parsed_resp.source_registry_id
                artifact_data.source_registry_type = parsed_resp.source_registry_type
                artifact_data.registry_id = registry_id
                artifact_data.registry_type = ArtifactRegistryType.RESERVOIR

            upsert_result = await self.upsert_artifacts_with_revisions(
                UpsertArtifactsAction(data=all_artifacts)
            )
            scanned_models = upsert_result.result

        return DelegateScanArtifactsActionResult(
            result=scanned_models,
            source_registry_id=parsed_resp.source_registry_id,
            source_registry_type=parsed_resp.source_registry_type,
            readme_data=parsed_resp.readme_data,
        )
