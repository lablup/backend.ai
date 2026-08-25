import uuid

from ai.backend.common.data.artifact.types import ArtifactRegistryType, VerificationStepResult
from ai.backend.common.data.entity.artifact import ArtifactID
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
    ArtifactListResult,
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactRevisionListResult,
    ArtifactStatus,
    ArtifactType,
    ArtifactWithRevisionsListResult,
)
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.errors.artifact import ArtifactNotFoundError
from ai.backend.manager.models.artifact.conditions import ArtifactConditions
from ai.backend.manager.models.artifact.creators import ArtifactCreator
from ai.backend.manager.models.artifact.searchers import (
    ArtifactSearcher,
    ArtifactWithRevisionsSearcher,
)
from ai.backend.manager.models.artifact.updaters import (
    ArtifactScanUpdater,
    ArtifactTouchUpdater,
    ArtifactUpdater,
)
from ai.backend.manager.models.artifact_revision.conditions import ArtifactRevisionConditions
from ai.backend.manager.models.artifact_revision.creators import ArtifactRevisionCreator
from ai.backend.manager.models.artifact_revision.searchers import ArtifactRevisionSearcher
from ai.backend.manager.models.artifact_revision.updaters import ArtifactRevisionScanUpdater
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact.db_source.db_source import ArtifactDBSource
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps
from ai.backend.manager.types import TriState

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
    _v2_ops: V2DBOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, v2_ops_provider: V2DBOpsProvider) -> None:
        self._db_source = ArtifactDBSource(db)
        self._v2_ops = v2_ops_provider

    @artifact_repository_resilience.apply()
    async def get_artifact_by_id(self, artifact_id: uuid.UUID) -> ArtifactData:
        return await self._db_source.get_artifact_by_id(artifact_id)

    @artifact_repository_resilience.apply()
    async def get_model_artifact(self, model_id: str, registry_id: uuid.UUID) -> ArtifactData:
        return await self._db_source.get_model_artifact(model_id, registry_id)

    @artifact_repository_resilience.apply()
    async def get_artifact_revision(
        self, artifact_id: uuid.UUID, revision: str
    ) -> ArtifactRevisionData:
        return await self._db_source.get_artifact_revision(artifact_id, revision)

    @artifact_repository_resilience.apply()
    async def update_artifact(self, updater: ArtifactUpdater) -> ArtifactData:
        """Edit one artifact.

        Raises ArtifactNotFoundError if the artifact is gone or already deleted.
        """
        async with self._v2_ops.write_ops() as w:
            data = await w.update_guarded_data(updater)
            if data is None:
                raise ArtifactNotFoundError(f"Artifact with ID {updater.artifact_id} not found")
            return data

    @artifact_repository_resilience.apply()
    async def list_artifact_revisions(self, artifact_id: uuid.UUID) -> list[ArtifactRevisionData]:
        return await self._db_source.list_artifact_revisions(artifact_id)

    @artifact_repository_resilience.apply()
    async def upsert_artifacts(
        self,
        artifacts: list[ArtifactData],
    ) -> list[ArtifactData]:
        """Register each scanned artifact, or write back what the scan found."""
        async with self._v2_ops.write_ops() as w:
            results: list[ArtifactData] = []
            for artifact in artifacts:
                existing = await self._artifact_by_name(w, artifact.name, artifact.registry_id)
                if existing is None:
                    results.append(
                        await w.create_global_entity(
                            ArtifactCreator(
                                name=artifact.name,
                                type=artifact.type,
                                description=artifact.description,
                                registry_id=artifact.registry_id,
                                registry_type=artifact.registry_type,
                                source_registry_id=artifact.source_registry_id,
                                source_registry_type=artifact.source_registry_type,
                                readonly=True,
                                extra=artifact.extra,
                            )
                        )
                    )
                    continue
                if (
                    existing.description == artifact.description
                    and existing.extra == artifact.extra
                ):
                    results.append(existing)
                    continue
                updated = await w.update_data(
                    ArtifactScanUpdater(
                        artifact_id=existing.id,
                        extra=artifact.extra,
                        description=TriState[str].from_nullable(artifact.description),
                    )
                )
                results.append(updated if updated is not None else existing)
            return results

    @artifact_repository_resilience.apply()
    async def upsert_artifact_revisions(
        self,
        revisions: list[ArtifactRevisionData],
    ) -> list[ArtifactRevisionData]:
        """Record each scanned revision, skipping the ones a scan does not copy."""
        async with self._v2_ops.write_ops() as w:
            results: list[ArtifactRevisionData] = []
            touched: set[uuid.UUID] = set()
            for revision in revisions:
                if revision.status in (ArtifactStatus.FAILED, ArtifactStatus.REJECTED):
                    continue
                verification_result = (
                    revision.verification_result.model_dump()
                    if revision.verification_result is not None
                    else None
                )
                existing = await self._revision_by_version(
                    w, revision.artifact_id, revision.version
                )
                if existing is None:
                    results.append(
                        await w.create_field(
                            revision.artifact_id,
                            ArtifactRevisionCreator(
                                id=revision.id,
                                version=revision.version,
                                readme=revision.readme,
                                size=revision.size,
                                status=ArtifactStatus.SCANNED,
                                remote_status=revision.remote_status,
                                created_at=revision.created_at,
                                updated_at=revision.updated_at,
                                digest=revision.digest,
                                verification_result=verification_result,
                            ),
                        )
                    )
                    touched.add(revision.artifact_id)
                    continue
                updated = await w.update_data(
                    ArtifactRevisionScanUpdater(
                        revision_id=existing.id,
                        readme=revision.readme,
                        size=revision.size,
                        created_at=revision.created_at,
                        updated_at=revision.updated_at,
                        digest=revision.digest,
                        verification_result=verification_result,
                        remote_status=revision.remote_status,
                    )
                )
                results.append(updated if updated is not None else existing)
                touched.add(revision.artifact_id)
            if touched:
                await w.batch_update_in_global(ArtifactTouchUpdater(artifact_ids=touched))
            return results

    @artifact_repository_resilience.apply()
    async def upsert_huggingface_model_artifacts(
        self,
        model_list: list[ModelData],
        registry_id: uuid.UUID,
    ) -> list[ArtifactDataWithRevisions]:
        """Register the models a HuggingFace scan returned, with their revisions."""
        async with self._v2_ops.write_ops() as w:
            scanned: dict[uuid.UUID, tuple[ArtifactData, list[ArtifactRevisionData]]] = {}
            touched: set[uuid.UUID] = set()
            for model in model_list:
                artifact = await self._artifact_by_name(w, model.id, registry_id)
                if artifact is None:
                    artifact = await w.create_global_entity(
                        ArtifactCreator(
                            name=model.id,
                            type=ArtifactType.MODEL,
                            registry_id=registry_id,
                            registry_type=ArtifactRegistryType.HUGGINGFACE,
                            source_registry_id=registry_id,
                            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
                            readonly=True,
                            extra=model.extra,
                        )
                    )
                else:
                    updated = await w.update_data(
                        ArtifactScanUpdater(artifact_id=artifact.id, extra=model.extra)
                    )
                    artifact = updated if updated is not None else artifact
                    touched.add(artifact.id)
                scanned.setdefault(artifact.id, (artifact, []))

                revision = await self._revision_by_version(w, artifact.id, model.revision)
                if revision is None:
                    revision = await w.create_field(
                        artifact.id,
                        ArtifactRevisionCreator(
                            version=model.revision,
                            readme=model.readme,
                            size=model.size,
                            status=ArtifactStatus.SCANNED,
                            remote_status=None,
                            created_at=model.created_at,
                            updated_at=model.modified_at,
                            digest=model.sha,
                            verification_result=None,
                        ),
                    )
                    touched.add(artifact.id)
                elif revision.digest != model.sha:
                    updated_revision = await w.update_data(
                        ArtifactRevisionScanUpdater(
                            revision_id=revision.id,
                            readme=model.readme,
                            size=revision.size,
                            created_at=revision.created_at,
                            updated_at=model.modified_at,
                            digest=revision.digest,
                            verification_result=None,
                            remote_status=revision.remote_status,
                        )
                    )
                    revision = updated_revision if updated_revision is not None else revision
                    touched.add(artifact.id)
                scanned[artifact.id][1].append(revision)

            if touched:
                for stamped in await w.batch_update_in_global(
                    ArtifactTouchUpdater(artifact_ids=touched)
                ):
                    scanned[stamped.id] = (stamped, scanned[stamped.id][1])

            return [
                ArtifactDataWithRevisions.from_dataclasses(
                    artifact_data=artifact, revisions=revisions
                )
                for artifact, revisions in scanned.values()
            ]

    async def _artifact_by_name(
        self, ops: V2WriteOps, name: str, registry_id: uuid.UUID
    ) -> ArtifactData | None:
        """The artifact a scan is about, named by the pair a registry knows it by."""
        result = await ops.search_in_global(
            ArtifactSearcher(
                pagination=OffsetPagination(limit=1),
                conditions=[ArtifactConditions.by_name_and_registry(name, registry_id)],
            )
        )
        return result.items[0] if result.items else None

    async def _revision_by_version(
        self, ops: V2WriteOps, artifact_id: ArtifactID, version: str
    ) -> ArtifactRevisionData | None:
        result = await ops.search_in_global(
            ArtifactRevisionSearcher(
                pagination=OffsetPagination(limit=1),
                conditions=[
                    ArtifactRevisionConditions.by_artifact_and_version(artifact_id, version)
                ],
            )
        )
        return result.items[0] if result.items else None

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
    async def get_artifact_revision_readme(self, artifact_revision_id: uuid.UUID) -> str | None:
        return await self._db_source.get_artifact_revision_readme(artifact_revision_id)

    @artifact_repository_resilience.apply()
    async def search_artifacts(
        self,
        searcher: ArtifactSearcher,
    ) -> ArtifactListResult:
        """Search artifacts."""
        async with self._v2_ops.read_ops() as r:
            result = await r.search_in_global(searcher)
        return ArtifactListResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    @artifact_repository_resilience.apply()
    async def search_artifact_revisions(
        self,
        searcher: ArtifactRevisionSearcher,
    ) -> ArtifactRevisionListResult:
        """Search artifact revisions."""
        async with self._v2_ops.read_ops() as r:
            result = await r.search_in_global(searcher)
        return ArtifactRevisionListResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    @artifact_repository_resilience.apply()
    async def search_artifacts_with_revisions(
        self,
        searcher: ArtifactWithRevisionsSearcher,
    ) -> ArtifactWithRevisionsListResult:
        """Search artifacts with their revisions."""
        async with self._v2_ops.read_ops() as r:
            result = await r.search_in_global(searcher)
        return ArtifactWithRevisionsListResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
