import uuid
from typing import Optional

from ai.backend.common.data.artifact.types import VerificationStepResult
from ai.backend.common.data.storage.registries.types import ModelData
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactFilterOptions,
    ArtifactListResult,
    ArtifactOrderingOptions,
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactRevisionListResult,
    ArtifactStatus,
    ArtifactWithRevisionsListResult,
)
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact.db_source.db_source import ArtifactDBSource
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.types import PaginationOptions

artifact_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.ARTIFACT_REPOSITORY)),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


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
    async def update_artifact(self, updater: Updater[ArtifactRow]) -> ArtifactData:
        return await self._db_source.update_artifact(updater)

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
    async def update_artifact_revision_digest(
        self, artifact_revision_id: uuid.UUID, digest: str
    ) -> uuid.UUID:
        return await self._db_source.update_artifact_revision_digest(artifact_revision_id, digest)

    @artifact_repository_resilience.apply()
    async def update_artifact_revision_readme(
        self, artifact_revision_id: uuid.UUID, readme: str
    ) -> uuid.UUID:
        return await self._db_source.update_artifact_revision_readme(artifact_revision_id, readme)

    @artifact_repository_resilience.apply()
    async def update_artifact_revision_verification_result(
        self, artifact_revision_id: uuid.UUID, verification_result: VerificationStepResult
    ) -> uuid.UUID:
        return await self._db_source.update_artifact_revision_verification_result(
            artifact_revision_id, verification_result
        )

    @artifact_repository_resilience.apply()
    async def get_artifact_revision_readme(self, artifact_revision_id: uuid.UUID) -> str:
        return await self._db_source.get_artifact_revision_readme(artifact_revision_id)

    @artifact_repository_resilience.apply()
    async def list_artifacts_with_revisions_paginated(
        self,
        *,
        pagination: Optional[PaginationOptions] = None,
        ordering: Optional[ArtifactOrderingOptions] = None,
        filters: Optional[ArtifactFilterOptions] = None,
    ) -> tuple[list[ArtifactDataWithRevisions], int]:
        # Legacy
        return await self._db_source.list_artifacts_with_revisions_paginated(
            pagination=pagination, ordering=ordering, filters=filters
        )

    @artifact_repository_resilience.apply()
    async def search_artifacts(
        self,
        querier: BatchQuerier,
    ) -> ArtifactListResult:
        """Search artifacts with querier pattern."""

        return await self._db_source.search_artifacts(querier=querier)

    @artifact_repository_resilience.apply()
    async def search_artifact_revisions(
        self,
        querier: BatchQuerier,
    ) -> ArtifactRevisionListResult:
        """Search artifact revisions with querier pattern."""

        return await self._db_source.search_artifact_revisions(querier=querier)

    @artifact_repository_resilience.apply()
    async def search_artifacts_with_revisions(
        self,
        querier: BatchQuerier,
    ) -> ArtifactWithRevisionsListResult:
        """Search artifacts with their revisions using querier pattern."""

        return await self._db_source.search_artifacts_with_revisions(querier=querier)
