import uuid
from typing import Optional, cast
from uuid import UUID

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.common.dto.storage.request import (
    DeleteObjectReq,
    HuggingFaceImportModelsReq,
    ReservoirImportModelsReq,
)
from ai.backend.manager.client.artifact_registry.reservoir_client import ReservoirRegistryClient
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import (
    ReservoirConfig,
    ReservoirObjectStorageConfig,
    ReservoirVFSStorageConfig,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactRemoteStatus,
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
from ai.backend.manager.services.artifact_revision.actions.get_readme import (
    GetArtifactRevisionReadmeAction,
    GetArtifactRevisionReadmeActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.import_revision import (
    ImportArtifactRevisionAction,
    ImportArtifactRevisionActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.list import (
    ListArtifactRevisionsAction,
    ListArtifactRevisionsActionResult,
)
from ai.backend.manager.services.artifact_revision.actions.reject import (
    RejectArtifactRevisionAction,
    RejectArtifactRevisionActionResult,
)


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

    async def list_revision(
        self, action: ListArtifactRevisionsAction
    ) -> ListArtifactRevisionsActionResult:
        (
            artifacts_data,
            total_count,
        ) = await self._artifact_repository.list_artifact_revisions_paginated(
            pagination=action.pagination,
            ordering=action.ordering,
            filters=action.filters,
        )
        return ListArtifactRevisionsActionResult(data=artifacts_data, total_count=total_count)

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
            await self._artifact_repository.update_artifact_revision_status(
                action.artifact_revision_id, ArtifactStatus.PULLING
            )
            revision_data = await self._artifact_repository.get_artifact_revision_by_id(
                action.artifact_revision_id
            )
            artifact = await self._artifact_repository.get_artifact_by_id(revision_data.artifact_id)

            reservoir_config = self._config_provider.config.reservoir
            storage_type = reservoir_config.config.storage_type
            reservoir_storage_name = reservoir_config.storage_name

            # Get bucket name or subpath depending on storage type
            namespace = self._resolve_storage_namespace(reservoir_config)
            storage_host, namespace_id, storage_name = await self._get_storage_info(
                reservoir_storage_name, namespace
            )

            storage_proxy_client = self._storage_manager.get_manager_facing_client(storage_host)
            task_id: UUID
            match artifact.registry_type:
                case ArtifactRegistryType.HUGGINGFACE:
                    huggingface_registry_data = await self._huggingface_registry_repository.get_registry_data_by_artifact_id(
                        artifact.id
                    )

                    huggingface_result = await storage_proxy_client.import_huggingface_models(
                        HuggingFaceImportModelsReq(
                            models=[
                                ModelTarget(model_id=artifact.name, revision=revision_data.version)
                            ],
                            registry_name=huggingface_registry_data.name,
                            storage_name=storage_name,
                            storage_step_mappings=reservoir_config.storage_step_selection,
                        )
                    )
                    task_id = huggingface_result.task_id
                case ArtifactRegistryType.RESERVOIR:
                    registry_data = (
                        await self._reservoir_registry_repository.get_registry_data_by_artifact_id(
                            artifact.id
                        )
                    )

                    result = await storage_proxy_client.import_reservoir_models(
                        ReservoirImportModelsReq(
                            models=[
                                ModelTarget(model_id=artifact.name, revision=revision_data.version)
                            ],
                            registry_name=registry_data.name,
                            storage_name=storage_name,
                            storage_step_mappings=reservoir_config.storage_step_selection,
                        )
                    )
                    task_id = result.task_id
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
        reservoir_storage_name = reservoir_config.storage_name
        # TODO: Abstract this.
        namespace = self._resolve_storage_namespace(reservoir_config)

        storage_data = None
        vfs_storage_data = None
        storage_namespace = None
        storage_host = None
        namespace_id = None
        storage_name = None

        try:
            storage_data = await self._object_storage_repository.get_by_name(reservoir_storage_name)
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
                reservoir_storage_name
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
        if not self._config_provider.config.reservoir.use_delegation:
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
                    task_ids.append(import_result.task_id)
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
            await self._artifact_repository.update_artifact_revision_remote_status(
                revision_id, ArtifactRemoteStatus.SCANNED
            )
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

        if client_resp is None:
            raise RemoteReservoirArtifactImportError("Failed to connect to remote reservoir")

        # Extract task_ids from remote response
        task_ids = [uuid.UUID(task.task_id) for task in client_resp.tasks]

        return DelegateImportArtifactRevisionBatchActionResult(
            result=result_revisions, task_ids=task_ids
        )

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
