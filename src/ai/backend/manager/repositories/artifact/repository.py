import uuid
from typing import Optional

from ai.backend.common.data.storage.registries.types import ModelData
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.manager.data.artifact.modifier import ArtifactModifier
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactStatus,
)
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact.db_source.db_source import (
    ArtifactDBSource,
    artifact_repository_resilience,
)
from ai.backend.manager.repositories.artifact.types import (
    ArtifactFilterOptions,
    ArtifactOrderingOptions,
    ArtifactRevisionFilterOptions,
    ArtifactRevisionOrderingOptions,
)
from ai.backend.manager.repositories.types import PaginationOptions


class ArtifactRepository:
    """Repository layer that delegates to data source."""

    _db_source: ArtifactDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ArtifactDBSource(db)

    @artifact_repository_resilience.apply()
    async def get_artifact_by_id(self, artifact_id: uuid.UUID) -> ArtifactData:
        return await self._db_source.get_artifact_by_id(artifact_id)

    @artifact_repository_resilience.apply()
    async def get_artifact_revision_by_id(self, revision_id: uuid.UUID) -> ArtifactRevisionData:
        return await self._db_source.get_artifact_revision_by_id(revision_id)

    @artifact_repository_resilience.apply()
    async def get_model_artifact(self, model_id: str, registry_id: uuid.UUID) -> ArtifactData:
        return await self._db_source.get_model_artifact(model_id, registry_id)

    @artifact_repository_resilience.apply()
    async def get_artifact_revision(
        self, artifact_id: uuid.UUID, revision: str
    ) -> ArtifactRevisionData:
        return await self._db_source.get_artifact_revision(artifact_id, revision)

    @artifact_repository_resilience.apply()
    async def update_artifact(
        self, artifact_id: uuid.UUID, modifier: ArtifactModifier
    ) -> ArtifactData:
        return await self._db_source.update_artifact(artifact_id, modifier)

    @artifact_repository_resilience.apply()
    async def list_artifact_revisions(self, artifact_id: uuid.UUID) -> list[ArtifactRevisionData]:
        return await self._db_source.list_artifact_revisions(artifact_id)

    @artifact_repository_resilience.apply()
    async def upsert_artifacts(
        self,
        artifacts: list[ArtifactData],
    ) -> list[ArtifactData]:
        return await self._db_source.upsert_artifacts(artifacts)

    @artifact_repository_resilience.apply()
    async def upsert_artifact_revisions(
        self,
        revisions: list[ArtifactRevisionData],
    ) -> list[ArtifactRevisionData]:
        return await self._db_source.upsert_artifact_revisions(revisions)

    @artifact_repository_resilience.apply()
    async def upsert_huggingface_model_artifacts(
        self,
        model_list: list[ModelData],
        registry_id: uuid.UUID,
    ) -> list[ArtifactDataWithRevisions]:
        return await self._db_source.upsert_huggingface_model_artifacts(model_list, registry_id)

    @artifact_repository_resilience.apply()
    async def associate_artifact_with_storage(
        self,
        artifact_revision_id: uuid.UUID,
        storage_namespace_id: uuid.UUID,
        storage_type: ArtifactStorageType,
    ) -> AssociationArtifactsStoragesData:
        return await self._db_source.associate_artifact_with_storage(
            artifact_revision_id, storage_namespace_id, storage_type
        )

    @artifact_repository_resilience.apply()
    async def disassociate_artifact_with_storage(
        self, artifact_revision_id: uuid.UUID, storage_namespace_id: uuid.UUID
    ) -> AssociationArtifactsStoragesData:
        return await self._db_source.disassociate_artifact_with_storage(
            artifact_revision_id, storage_namespace_id
        )

    @artifact_repository_resilience.apply()
    async def approve_artifact(self, revision_id: uuid.UUID) -> ArtifactRevisionData:
        return await self._db_source.approve_artifact(revision_id)

    @artifact_repository_resilience.apply()
    async def reject_artifact(self, revision_id: uuid.UUID) -> ArtifactRevisionData:
        return await self._db_source.reject_artifact(revision_id)

    @artifact_repository_resilience.apply()
    async def reset_artifact_revision_status(self, revision_id: uuid.UUID) -> uuid.UUID:
        return await self._db_source.reset_artifact_revision_status(revision_id)

    @artifact_repository_resilience.apply()
    async def update_artifact_revision_status(
        self, artifact_revision_id: uuid.UUID, status: ArtifactStatus
    ) -> uuid.UUID:
        return await self._db_source.update_artifact_revision_status(artifact_revision_id, status)

    @artifact_repository_resilience.apply()
    async def update_artifact_revision_remote_status(
        self, artifact_revision_id: uuid.UUID, remote_status: ArtifactRemoteStatus
    ) -> uuid.UUID:
        return await self._db_source.update_artifact_revision_remote_status(
            artifact_revision_id, remote_status
        )

    @artifact_repository_resilience.apply()
    async def delete_artifacts(self, artifact_ids: list[uuid.UUID]) -> list[ArtifactData]:
        return await self._db_source.delete_artifacts(artifact_ids)

    @artifact_repository_resilience.apply()
    async def restore_artifacts(self, artifact_ids: list[uuid.UUID]) -> list[ArtifactData]:
        return await self._db_source.restore_artifacts(artifact_ids)

    @artifact_repository_resilience.apply()
    async def update_artifact_revision_bytesize(
        self, artifact_revision_id: uuid.UUID, size: int
    ) -> uuid.UUID:
        return await self._db_source.update_artifact_revision_bytesize(artifact_revision_id, size)

    @artifact_repository_resilience.apply()
    async def update_artifact_revision_readme(
        self, artifact_revision_id: uuid.UUID, readme: str
    ) -> uuid.UUID:
        return await self._db_source.update_artifact_revision_readme(artifact_revision_id, readme)

    @artifact_repository_resilience.apply()
    async def get_artifact_revision_readme(self, artifact_revision_id: uuid.UUID) -> str:
        return await self._db_source.get_artifact_revision_readme(artifact_revision_id)

    @artifact_repository_resilience.apply()
    async def list_artifacts_paginated(
        self,
        *,
        pagination: Optional[PaginationOptions] = None,
        ordering: Optional[ArtifactOrderingOptions] = None,
        filters: Optional[ArtifactFilterOptions] = None,
    ) -> tuple[list[ArtifactData], int]:
        return await self._db_source.list_artifacts_paginated(
            pagination=pagination, ordering=ordering, filters=filters
        )

    @artifact_repository_resilience.apply()
    async def list_artifacts_with_revisions_paginated(
        self,
        *,
        pagination: Optional[PaginationOptions] = None,
        ordering: Optional[ArtifactOrderingOptions] = None,
        filters: Optional[ArtifactFilterOptions] = None,
    ) -> tuple[list[ArtifactDataWithRevisions], int]:
        return await self._db_source.list_artifacts_with_revisions_paginated(
            pagination=pagination, ordering=ordering, filters=filters
        )

    @artifact_repository_resilience.apply()
    async def list_artifact_revisions_paginated(
        self,
        *,
        pagination: Optional[PaginationOptions] = None,
        ordering: Optional[ArtifactRevisionOrderingOptions] = None,
        filters: Optional[ArtifactRevisionFilterOptions] = None,
    ) -> tuple[list[ArtifactRevisionData], int]:
        return await self._db_source.list_artifact_revisions_paginated(
            pagination=pagination, ordering=ordering, filters=filters
        )
