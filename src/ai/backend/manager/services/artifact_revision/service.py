from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.common.dto.storage.request import (
    DeleteObjectReq,
    HuggingFaceImportModelsReq,
    ReservoirImportModelsReq,
)
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.artifact.types import ArtifactRevisionReadme, ArtifactStatus
from ai.backend.manager.errors.artifact import (
    ArtifactDeletionBadRequestError,
    ArtifactDeletionError,
)
from ai.backend.manager.errors.artifact_registry import InvalidArtifactRegistryTypeError
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
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
    _object_storage_repository: ObjectStorageRepository
    _huggingface_registry_repository: HuggingFaceRepository
    _reservoir_registry_repository: ReservoirRegistryRepository
    _storage_manager: StorageSessionManager
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        object_storage_repository: ObjectStorageRepository,
        huggingface_registry_repository: HuggingFaceRepository,
        reservoir_registry_repository: ReservoirRegistryRepository,
        storage_manager: StorageSessionManager,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._object_storage_repository = object_storage_repository
        self._huggingface_registry_repository = huggingface_registry_repository
        self._reservoir_registry_repository = reservoir_registry_repository
        self._storage_manager = storage_manager
        self._config_provider = config_provider

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
        bucket_name = reservoir_config.config.bucket_name
        storage_data = await self._object_storage_repository.get_by_name(reservoir_storage_name)
        storage_namespace = await self._object_storage_repository.get_storage_namespace(
            storage_data.id, bucket_name
        )
        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage_data.host)

        match artifact.registry_type:
            case ArtifactRegistryType.HUGGINGFACE:
                registry_data = (
                    await self._huggingface_registry_repository.get_registry_data_by_artifact_id(
                        artifact.id
                    )
                )

                result = await storage_proxy_client.import_huggingface_models(
                    HuggingFaceImportModelsReq(
                        models=[
                            ModelTarget(model_id=artifact.name, revision=revision_data.version)
                        ],
                        registry_name=registry_data.name,
                        storage_name=storage_data.name,
                    )
                )
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
                        storage_name=storage_data.name,
                    )
                )
            case _:
                raise InvalidArtifactRegistryTypeError(
                    f"Unsupported artifact registry type: {artifact.registry_type}"
                )

        await self.associate_with_storage(
            AssociateWithStorageAction(
                revision_data.id, storage_namespace.id, ArtifactStorageType(storage_type)
            )
        )

        return ImportArtifactRevisionActionResult(result=revision_data, task_id=result.task_id)

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
        bucket_name = reservoir_config.config.bucket_name

        storage_data = await self._object_storage_repository.get_by_name(reservoir_storage_name)
        storage_namespace = await self._object_storage_repository.get_storage_namespace(
            storage_data.id, bucket_name
        )
        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage_data.host)

        key = f"{artifact_data.name}/{revision_data.version}/"

        try:
            await storage_proxy_client.delete_s3_object(
                storage_name=storage_data.name,
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
                storage_namespace_id=storage_namespace.id,
            )
        )

        artifact_revision = await self._artifact_repository.get_artifact_revision_by_id(
            revision_data.id
        )
        return CleanupArtifactRevisionActionResult(result=artifact_revision)
