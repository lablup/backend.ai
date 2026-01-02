from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Final, Optional, cast
from uuid import UUID

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.data.artifact.types import (
    ArtifactRegistryType,
    ArtifactRevisionDownloadProgress,
    CombinedDownloadProgress,
)
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.common.dto.storage.request import (
    DeleteObjectReq,
    HuggingFaceGetCommitHashReqPathParam,
    HuggingFaceGetCommitHashReqQueryParam,
    HuggingFaceImportModelsReq,
    ReservoirImportModelsReq,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.client.artifact_registry.reservoir_client import ReservoirRegistryClient
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import (
    ReservoirConfig,
    ReservoirObjectStorageConfig,
    ReservoirVFSStorageConfig,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactRevisionData,
    ArtifactRevisionReadme,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.dto.request import DelegateImportArtifactsReq
from ai.backend.manager.errors.artifact import (
    ArtifactDeletionBadRequestError,
    ArtifactDeletionError,
    ArtifactImportBadRequestError,
    RemoteReservoirArtifactImportError,
)
from ai.backend.manager.errors.artifact_registry import (
    InvalidArtifactRegistryTypeError,
)
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.errors.storage import UnsupportedStorageTypeError
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.repositories.storage_namespace.repository import StorageNamespaceRepository
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.artifact_revision.actions.approve import (
    ApproveArtifactRevisionAction,
    ApproveArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.associate_with_storage import (
    AssociateWithStorageAction,
    AssociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.cancel_import import (
    CancelImportAction,
    CancelImportActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.cleanup import (
    CleanupArtifactRevisionAction,
    CleanupArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.delegate_import_revision_batch import (
    DelegateImportArtifactRevisionBatchAction,
    DelegateImportArtifactRevisionBatchActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.disassociate_with_storage import (
    DisassociateWithStorageAction,
    DisassociateWithStorageActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.get import (
    GetArtifactRevisionAction,
    GetArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.get_download_progress import (
    GetDownloadProgressAction,
    GetDownloadProgressActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.get_readme import (
    GetArtifactRevisionReadmeAction,
    GetArtifactRevisionReadmeActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.get_verification_result import (
    GetArtifactRevisionVerificationResultAction,
    GetArtifactRevisionVerificationResultActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.import_revision import (
    ImportArtifactRevisionAction,
    ImportArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.reject import (
    RejectArtifactRevisionAction,
    RejectArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.search import (
    SearchArtifactRevisionsAction,
    SearchArtifactRevisionsActionResult,
)

_REMOTE_ARTIFACT_STATUS_POLL_INTERVAL: Final[int] = 30  # seconds
_REMOTE_ARTIFACT_MAX_WAIT_TIME: Final[int] = 3600  # 1 hour

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class ArtifactRevisionService:
    _artifact_repository: ArtifactRepository
    _artifact_registry_repository: ArtifactRegistryRepository
    _object_storage_repository: ObjectStorageRepository
    _vfs_storage_repository: VFSStorageRepository
    _storage_namespace_repository: StorageNamespaceRepository
    _huggingface_registry_repository: HuggingFaceRepository
    _reservoir_registry_repository: ReservoirRegistryRepository
    _storage_manager: StorageSessionManager
    _config_provider: ManagerConfigProvider
    _background_task_manager: BackgroundTaskManager

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        artifact_registry_repository: ArtifactRegistryRepository,
        object_storage_repository: ObjectStorageRepository,
        vfs_storage_repository: VFSStorageRepository,
        storage_namespace_repository: StorageNamespaceRepository,
        huggingface_registry_repository: HuggingFaceRepository,
        reservoir_registry_repository: ReservoirRegistryRepository,
        storage_manager: StorageSessionManager,
        config_provider: ManagerConfigProvider,
        valkey_artifact_client: ValkeyArtifactDownloadTrackingClient,
        background_task_manager: BackgroundTaskManager,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._artifact_registry_repository = artifact_registry_repository
        self._object_storage_repository = object_storage_repository
        self._vfs_storage_repository = vfs_storage_repository
        self._storage_namespace_repository = storage_namespace_repository
        self._huggingface_registry_repository = huggingface_registry_repository
        self._reservoir_registry_repository = reservoir_registry_repository
        self._storage_manager = storage_manager
        self._config_provider = config_provider
        self._valkey_artifact_client = valkey_artifact_client
        self._background_task_manager = background_task_manager

    def _resolve_storage_namespace(self, reservoir_config: ReservoirConfig) -> str:
        """Resolve namespace based on storage type
        Args:
            reservoir_config: Reservoir configuration
        Returns:
            Namespace (bucket name for object storage, subpath for VFS storage)
        """
        match reservoir_config.config.storage_type:
            case ArtifactStorageType.OBJECT_STORAGE.value:
                return cast(ReservoirObjectStorageConfig, reservoir_config.config).bucket_name
            case ArtifactStorageType.VFS_STORAGE.value:
                return cast(ReservoirVFSStorageConfig, reservoir_config.config).subpath
            case _:
                raise UnsupportedStorageTypeError(
                    f"Unsupported storage type: {reservoir_config.config.storage_type}"
                )

    async def _get_storage_info(
        self, storage_name: str, namespace: str
    ) -> tuple[str, uuid.UUID, str]:
        """Get storage info by trying object_storage first, then vfs_storage as fallback
        Args:
            storage_name: Name of the storage
            namespace: Bucket name for object storage or subpath for VFS storage
        Returns: (storage_host, namespace_id, storage_name)
        """
        try:
            object_storage_data = await self._object_storage_repository.get_by_name(storage_name)
            storage_namespace = (
                await self._storage_namespace_repository.get_by_storage_and_namespace(
                    object_storage_data.id, namespace
                )
            )
            return object_storage_data.host, storage_namespace.id, object_storage_data.name
        except Exception:
            vfs_storage_data = await self._vfs_storage_repository.get_by_name(storage_name)
            storage_namespace = (
                await self._storage_namespace_repository.get_by_storage_and_namespace(
                    vfs_storage_data.id, namespace
                )
            )
            return vfs_storage_data.host, storage_namespace.id, vfs_storage_data.name

    async def get(self, action: GetArtifactRevisionAction) -> GetArtifactRevisionActionResult:
        revision = await self._artifact_repository.get_artifact_revision_by_id(
            action.artifact_revision_id
        )
        return GetArtifactRevisionActionResult(revision=revision)

    async def get_readme(
        self, action: GetArtifactRevisionReadmeAction
    ) -> GetArtifactRevisionReadmeActionResult:
        readme = await self._artifact_repository.get_artifact_revision_readme(
            action.artifact_revision_id
        )
        readme_data = ArtifactRevisionReadme(readme=readme)
        return GetArtifactRevisionReadmeActionResult(readme_data=readme_data)

    async def get_verification_result(
        self, action: GetArtifactRevisionVerificationResultAction
    ) -> GetArtifactRevisionVerificationResultActionResult:
        revision = await self._artifact_repository.get_artifact_revision_by_id(
            action.artifact_revision_id
        )
        return GetArtifactRevisionVerificationResultActionResult(
            verification_result=revision.verification_result
        )

    async def get_download_progress(
        self, action: GetDownloadProgressAction
    ) -> GetDownloadProgressActionResult:
        # 1. Get artifact_revision info
        revision = await self._artifact_repository.get_artifact_revision_by_id(
            action.artifact_revision_id
        )

        # 2. Get artifact info to extract model_id and revision
        artifact = await self._artifact_repository.get_artifact_by_id(revision.artifact_id)
        model_id = artifact.name  # artifact name is the model_id
        revision_name = revision.version

        # 3. Get local progress from valkey
        local_progress = await self._valkey_artifact_client.get_download_progress(
            model_id=model_id,
            revision=revision_name,
        )

        # Build local progress with status
        local_download_progress = ArtifactRevisionDownloadProgress(
            progress=local_progress if local_progress.artifact_progress else None,
            status=revision.status.value,
        )

        # 4. Query remote progress when delegation is enabled
        remote_download_progress: Optional[ArtifactRevisionDownloadProgress] = None

        # Only set remote for RESERVOIR type
        if artifact.registry_type == ArtifactRegistryType.RESERVOIR:
            reservoir_cfg = self._config_provider.config.reservoir
            # Default: create remote progress object with None progress and remote_status
            remote_status = revision.remote_status.value if revision.remote_status else "UNSCANNED"

            # Check if delegation is enabled
            if reservoir_cfg and reservoir_cfg.use_delegation:
                # If local is PULLING, return remote status without making remote request
                if revision.status == ArtifactStatus.PULLING:
                    remote_download_progress = ArtifactRevisionDownloadProgress(
                        progress=None,
                        status=remote_status,
                    )
                # Otherwise, query remote only if local has no progress
                elif local_progress.artifact_progress is None:
                    try:
                        # Get reservoir registry data
                        registry_data = await self._reservoir_registry_repository.get_reservoir_registry_data_by_id(
                            artifact.registry_id
                        )

                        # Create remote reservoir client
                        remote_reservoir_client = ReservoirRegistryClient(
                            registry_data=registry_data
                        )

                        # Query remote reservoir manager for download progress
                        remote_resp = await remote_reservoir_client.get_download_progress(
                            artifact_revision_id=action.artifact_revision_id,
                        )

                        # Parse response - expecting GetDownloadProgressResponse structure
                        # We want the remote's "local" progress as our "remote" progress
                        remote_local = remote_resp.download_progress.local

                        if remote_local:
                            remote_download_progress = ArtifactRevisionDownloadProgress(
                                progress=remote_local.progress,
                                status=remote_local.status,
                            )
                        else:
                            # Remote response exists but no local data
                            remote_download_progress = ArtifactRevisionDownloadProgress(
                                progress=None,
                                status=remote_status,
                            )
                    except Exception as e:
                        # If remote query fails, return remote status without progress
                        log.warning("Failed to get remote download progress {}", e)
                        remote_download_progress = ArtifactRevisionDownloadProgress(
                            progress=None,
                            status=remote_status,
                        )
                else:
                    # Local has progress, don't query remote
                    remote_download_progress = ArtifactRevisionDownloadProgress(
                        progress=None,
                        status=remote_status,
                    )
            else:
                # No delegation but still RESERVOIR type
                remote_download_progress = ArtifactRevisionDownloadProgress(
                    progress=None,
                    status=remote_status,
                )
        # else: Not RESERVOIR type, remote_download_progress remains None

        # 5. Build combined response
        combined_progress = CombinedDownloadProgress(
            local=local_download_progress,
            remote=remote_download_progress,
        )

        return GetDownloadProgressActionResult(download_progress=combined_progress)

    async def search_revision(
        self, action: SearchArtifactRevisionsAction
    ) -> SearchArtifactRevisionsActionResult:
        result = await self._artifact_repository.search_artifact_revisions(
            querier=action.querier,
        )
        return SearchArtifactRevisionsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def approve(
        self, action: ApproveArtifactRevisionAction
    ) -> ApproveArtifactRevisionActionResult:
        result = await self._artifact_repository.approve_artifact(action.artifact_revision_id)
        return ApproveArtifactRevisionActionResult(result=result)

    async def reject(
        self, action: RejectArtifactRevisionAction
    ) -> RejectArtifactRevisionActionResult:
        result = await self._artifact_repository.reject_artifact(action.artifact_revision_id)
        return RejectArtifactRevisionActionResult(result=result)

    async def associate_with_storage(
        self, action: AssociateWithStorageAction
    ) -> AssociateWithStorageActionResult:
        result = await self._artifact_repository.associate_artifact_with_storage(
            action.artifact_revision_id, action.storage_namespace_id, action.storage_type
        )
        return AssociateWithStorageActionResult(result=result)

    async def disassociate_with_storage(
        self, action: DisassociateWithStorageAction
    ) -> DisassociateWithStorageActionResult:
        result = await self._artifact_repository.disassociate_artifact_with_storage(
            action.artifact_revision_id, action.storage_namespace_id
        )
        return DisassociateWithStorageActionResult(result=result)

    async def cancel_import(self, action: CancelImportAction) -> CancelImportActionResult:
        await self._artifact_repository.reset_artifact_revision_status(action.artifact_revision_id)
        revision_data = await self._artifact_repository.get_artifact_revision_by_id(
            action.artifact_revision_id
        )
        return CancelImportActionResult(result=revision_data)

    async def import_revision(
        self, action: ImportArtifactRevisionAction
    ) -> ImportArtifactRevisionActionResult:
        try:
            revision_data = await self._artifact_repository.get_artifact_revision_by_id(
                action.artifact_revision_id
            )
            artifact = await self._artifact_repository.get_artifact_by_id(revision_data.artifact_id)

            reservoir_config = self._config_provider.config.reservoir
            if reservoir_config is None:
                raise ServerMisconfiguredError("Reservoir configuration is missing")

            storage_type = reservoir_config.config.storage_type
            reservoir_archive_storage = reservoir_config.archive_storage

            # Get bucket name or subpath depending on storage type
            namespace = self._resolve_storage_namespace(reservoir_config)
            storage_host, namespace_id, _ = await self._get_storage_info(
                reservoir_archive_storage, namespace
            )

            storage_proxy_client = self._storage_manager.get_manager_facing_client(storage_host)
            task_id: UUID
            match artifact.registry_type:
                case ArtifactRegistryType.HUGGINGFACE:
                    huggingface_registry_data = await self._huggingface_registry_repository.get_registry_data_by_artifact_id(
                        artifact.id
                    )

                    # Check current commit hash for this revision
                    commit_hash_resp = await storage_proxy_client.get_huggingface_model_commit_hash(
                        path=HuggingFaceGetCommitHashReqPathParam(
                            model_id=artifact.name,
                        ),
                        query=HuggingFaceGetCommitHashReqQueryParam(
                            revision=revision_data.version,
                            registry_name=huggingface_registry_data.name,
                        ),
                    )
                    latest_commit_hash = commit_hash_resp.commit_hash

                    # Skip import if artifact revision is already Available and commit hash matches
                    # If current_commit_hash is None, always proceed with import
                    if self._is_latest_commit_hash(revision_data, latest_commit_hash):
                        # Return early without calling import API
                        return ImportArtifactRevisionActionResult(
                            result=revision_data, task_id=None
                        )

                    await self._artifact_repository.update_artifact_revision_status(
                        action.artifact_revision_id, ArtifactStatus.PULLING
                    )

                    huggingface_result = await storage_proxy_client.import_huggingface_models(
                        HuggingFaceImportModelsReq(
                            models=[
                                ModelTarget(model_id=artifact.name, revision=revision_data.version)
                            ],
                            registry_name=huggingface_registry_data.name,
                            storage_step_mappings=reservoir_config.resolve_storage_step_selection(),
                        )
                    )
                    task_id = huggingface_result.task_id
                case ArtifactRegistryType.RESERVOIR:
                    registry_data = (
                        await self._reservoir_registry_repository.get_registry_data_by_artifact_id(
                            artifact.id
                        )
                    )

                    async def _task(reporter: ProgressReporter) -> None:
                        # When use_delegation is True, if remote status is not AVAILABLE, delegate import
                        if reservoir_config.use_delegation:
                            remote_reservoir_client = ReservoirRegistryClient(
                                registry_data=registry_data
                            )

                            remote_progress_status_resp = (
                                await remote_reservoir_client.get_download_progress(
                                    revision_data.id
                                )
                            )
                            remote_progress = remote_progress_status_resp.download_progress.local

                            # Wait for remote to start pulling if not yet AVAILABLE
                            if remote_progress.status != ArtifactStatus.AVAILABLE.value:
                                delegate_import_req = DelegateImportArtifactsReq(
                                    artifact_revision_ids=[revision_data.id],
                                    artifact_type=artifact.type,
                                    # We can't pass delegatee_reservoir_id here since we don't have it.
                                    # So we depend on default.
                                    delegator_reservoir_id=None,
                                    delegatee_target=None,
                                )

                                await remote_reservoir_client.delegate_import_artifacts(
                                    delegate_import_req
                                )

                                # Poll until remote status is AVAILABLE
                                elapsed_time = 0

                                log.info(
                                    "Waiting for remote artifact to become AVAILABLE. "
                                    "artifact_revision_id: {}",
                                    revision_data.id,
                                )

                                while elapsed_time < _REMOTE_ARTIFACT_MAX_WAIT_TIME:
                                    await asyncio.sleep(_REMOTE_ARTIFACT_STATUS_POLL_INTERVAL)
                                    elapsed_time += _REMOTE_ARTIFACT_STATUS_POLL_INTERVAL

                                    remote_progress_status_resp = (
                                        await remote_reservoir_client.get_download_progress(
                                            revision_data.id
                                        )
                                    )
                                    remote_progress = (
                                        remote_progress_status_resp.download_progress.local
                                    )

                                    if remote_progress.status == ArtifactStatus.AVAILABLE.value:
                                        log.info(
                                            "Remote artifact is now AVAILABLE. "
                                            "artifact_revision_id: {}, elapsed_time: {}s",
                                            revision_data.id,
                                            elapsed_time,
                                        )
                                        break

                                    log.info(
                                        "Waiting for remote artifact. Status: {}, Elapsed: {}s, "
                                        "artifact_revision_id: {}",
                                        remote_progress.status,
                                        elapsed_time,
                                        revision_data.id,
                                    )
                                else:
                                    # Timeout reached
                                    raise RemoteReservoirArtifactImportError(
                                        f"Timeout waiting for remote artifact to become AVAILABLE. "
                                        f"artifact_revision_id: {revision_data.id}, "
                                        f"Last status: {remote_progress.status}"
                                    )

                        await self._artifact_repository.update_artifact_revision_status(
                            action.artifact_revision_id, ArtifactStatus.PULLING
                        )

                        # TODO: Utilize this internal import task_id
                        _result = await storage_proxy_client.import_reservoir_models(
                            ReservoirImportModelsReq(
                                models=[
                                    ModelTarget(
                                        model_id=artifact.name, revision=revision_data.version
                                    )
                                ],
                                registry_name=registry_data.name,
                                storage_step_mappings=reservoir_config.resolve_storage_step_selection(),
                                artifact_revision_ids=[str(action.artifact_revision_id)],
                            )
                        )

                    task_id = await self._background_task_manager.start(_task)
                case _:
                    raise InvalidArtifactRegistryTypeError(
                        f"Unsupported artifact registry type: {artifact.registry_type}"
                    )

            await self.associate_with_storage(
                AssociateWithStorageAction(
                    revision_data.id, namespace_id, ArtifactStorageType(storage_type)
                )
            )

        except Exception as e:
            await self._artifact_repository.update_artifact_revision_status(
                action.artifact_revision_id, ArtifactStatus.FAILED
            )
            raise e

        return ImportArtifactRevisionActionResult(result=revision_data, task_id=task_id)

    async def cleanup(
        self, action: CleanupArtifactRevisionAction
    ) -> CleanupArtifactRevisionActionResult:
        revision_data = await self._artifact_repository.get_artifact_revision_by_id(
            action.artifact_revision_id
        )

        if revision_data.status in [ArtifactStatus.SCANNED, ArtifactStatus.PULLING]:
            raise ArtifactDeletionBadRequestError(
                "Artifact revision status not ready to be deleted"
            )

        await self._artifact_repository.reset_artifact_revision_status(revision_data.id)
        artifact_data = await self._artifact_repository.get_artifact_by_id(
            revision_data.artifact_id
        )

        reservoir_config = self._config_provider.config.reservoir
        if reservoir_config is None:
            raise ServerMisconfiguredError("Reservoir configuration is missing")

        reservoir_archive_storage = reservoir_config.archive_storage
        # TODO: Abstract this.
        namespace = self._resolve_storage_namespace(reservoir_config)

        storage_data = None
        vfs_storage_data = None
        storage_namespace = None
        storage_host = None
        namespace_id = None
        storage_name = None

        try:
            storage_data = await self._object_storage_repository.get_by_name(
                reservoir_archive_storage
            )
            storage_namespace = (
                await self._storage_namespace_repository.get_by_storage_and_namespace(
                    storage_data.id, namespace
                )
            )
            storage_host = storage_data.host
            namespace_id = storage_namespace.id
            storage_name = storage_data.name
        except Exception:
            vfs_storage_data = await self._vfs_storage_repository.get_by_name(
                reservoir_archive_storage
            )
            storage_namespace = (
                await self._storage_namespace_repository.get_by_storage_and_namespace(
                    vfs_storage_data.id, namespace
                )
            )
            storage_host = vfs_storage_data.host
            namespace_id = storage_namespace.id
            storage_name = vfs_storage_data.name

        if storage_data is None and vfs_storage_data is None:
            raise ArtifactDeletionError("Storage data not found for artifact deletion")

        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage_host)
        key = f"{artifact_data.name}/{revision_data.version}/"

        try:
            await storage_proxy_client.delete_s3_object(
                storage_name=storage_name,
                bucket_name=storage_namespace.namespace,
                req=DeleteObjectReq(
                    key=key,
                ),
            )
        except Exception as e:
            raise ArtifactDeletionError("Failed to delete artifact from storage") from e

        await self.disassociate_with_storage(
            DisassociateWithStorageAction(
                artifact_revision_id=revision_data.id,
                storage_namespace_id=namespace_id,
            )
        )

        artifact_revision = await self._artifact_repository.get_artifact_revision_by_id(
            revision_data.id
        )
        return CleanupArtifactRevisionActionResult(result=artifact_revision)

    async def delegate_import_revision_batch(
        self, action: DelegateImportArtifactRevisionBatchAction
    ) -> DelegateImportArtifactRevisionBatchActionResult:
        # If this is a leaf node, perform local import instead of delegation
        reservoir_cfg = self._config_provider.config.reservoir
        if reservoir_cfg is None:
            raise ServerMisconfiguredError("Reservoir configuration is missing")

        if not reservoir_cfg.use_delegation:
            registry_id = None
            if action.delegatee_target:
                registry_id = action.delegatee_target.target_registry_id

            registry_meta = await self._resolve_artifact_registry_meta(
                action.artifact_type, registry_id
            )

            try:
                # TODO: Improve this
                task_ids = []
                result: list[ArtifactRevisionData] = []
                for revision_id in action.artifact_revision_ids:
                    import_result = await self.import_revision(
                        ImportArtifactRevisionAction(artifact_revision_id=revision_id)
                    )
                    task_ids.append(import_result.task_id)  # Keep None values for zip alignment
                    result.append(import_result.result)
            except Exception as e:
                raise RemoteReservoirArtifactImportError(
                    f"Failed to import artifacts from remote reservoir: {e}"
                ) from e

            return DelegateImportArtifactRevisionBatchActionResult(result=result, task_ids=task_ids)

        # If not a leaf node, perform delegation to remote reservoir
        registry_meta = await self._resolve_artifact_registry_meta(
            action.artifact_type, action.delegator_reservoir_id
        )
        registry_type = registry_meta.type
        registry_id = registry_meta.registry_id

        if registry_type != ArtifactRegistryType.RESERVOIR:
            raise ArtifactImportBadRequestError(
                "Only Reservoir type registry is supported for delegated import"
            )

        registry_data = await self._reservoir_registry_repository.get_reservoir_registry_data_by_id(
            registry_id
        )

        # Update remote_status to SCANNED for all revisions before delegation
        result_revisions: list[ArtifactRevisionData] = []
        for revision_id in action.artifact_revision_ids:
            revision_data = await self._artifact_repository.get_artifact_revision_by_id(revision_id)
            result_revisions.append(revision_data)

        # Pass delegatee_reservoir_id to delegator_reservoir_id for the remote call
        delegatee_reservoir_id = (
            action.delegatee_target.delegatee_reservoir_id if action.delegatee_target else None
        )
        req = DelegateImportArtifactsReq(
            artifact_revision_ids=action.artifact_revision_ids,
            delegator_reservoir_id=delegatee_reservoir_id,
            delegatee_target=action.delegatee_target,
            artifact_type=action.artifact_type,
        )

        remote_reservoir_client = ReservoirRegistryClient(registry_data=registry_data)
        client_resp = await remote_reservoir_client.delegate_import_artifacts(req)

        # Extract task_ids from remote response
        task_ids = [uuid.UUID(task.task_id) if task.task_id else None for task in client_resp.tasks]

        return DelegateImportArtifactRevisionBatchActionResult(
            result=result_revisions, task_ids=task_ids
        )

    async def _resolve_artifact_registry_meta(
        self, artifact_type: Optional[ArtifactType], registry_id_or_none: Optional[uuid.UUID]
    ) -> ArtifactRegistryData:
        if registry_id_or_none is None:
            artifact_registry_cfg = self._config_provider.config.artifact_registry
            if artifact_registry_cfg is None:
                raise ServerMisconfiguredError("Artifact registry configuration is missing.")

            # TODO: Handle `artifact_type` for other types
            registry_name = artifact_registry_cfg.model_registry
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

    def _is_latest_commit_hash(
        self, artifact_revision: ArtifactRevisionData, latest_commit_hash: Optional[str]
    ) -> bool:
        """
        Used in huggingface import to check if the latest commit hash matches the stored digest.
        """
        if latest_commit_hash is None:
            return False
        if (
            artifact_revision.status == ArtifactStatus.AVAILABLE
            and artifact_revision.digest == latest_commit_hash
        ):
            return True
        return False
