import uuid
from typing import Optional

import sqlalchemy as sa

from ai.backend.common.data.storage.registries.types import ModelData
from ai.backend.common.exception import (
    ArtifactAssociationDeletionError,
    ArtifactAssociationNotFoundError,
    ArtifactNotFoundError,
    ArtifactNotVerified,
    ArtifactRevisionNotFoundError,
    ArtifactUpdateError,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactRegistryType,
    ArtifactRevisionData,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
from ai.backend.manager.models.association_artifacts_storages import AssociationArtifactsStorageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact.types import (
    ArtifactFilterOptions,
    ArtifactOrderingOptions,
)
from ai.backend.manager.repositories.types import (
    PaginationOptions,
)

# Layer-specific decorator for artifact repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.ARTIFACT)


class ArtifactRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def get_artifact_by_id(self, artifact_id: uuid.UUID) -> ArtifactData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(ArtifactRow.id == artifact_id)
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError()
            return row.to_dataclass()

    @repository_decorator()
    async def get_model_artifact(self, model_id: str, registry_id: uuid.UUID) -> ArtifactData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(
                    sa.and_(ArtifactRow.name == model_id, ArtifactRow.registry_id == registry_id)
                )
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError()
            return row.to_dataclass()

    @repository_decorator()
    async def get_artifact_revision(
        self, artifact_id: uuid.UUID, revision: str
    ) -> ArtifactRevisionData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(
                    sa.and_(
                        ArtifactRevisionRow.artifact_id == artifact_id,
                        ArtifactRevisionRow.version == revision,
                    )
                )
            )
            row: ArtifactRevisionRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRevisionNotFoundError()
            return row.to_dataclass()

    @repository_decorator()
    async def list_artifact_revisions(self, artifact_id: uuid.UUID) -> list[ArtifactRevisionData]:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.artifact_id == artifact_id)
            )
            rows: list[ArtifactRevisionRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    @repository_decorator()
    async def upsert_huggingface_model_artifacts(
        self,
        model_list: list[ModelData],
        registry_id: uuid.UUID,
    ) -> list[ArtifactDataWithRevisions]:
        async with self._db.begin_session() as db_sess:
            # key: artifact_id
            artifacts_map: dict[uuid.UUID, tuple[ArtifactRow, list[ArtifactRevisionRow]]] = {}

            for model in model_list:
                # Check if artifact exists within the current session
                artifact_query_result = await db_sess.execute(
                    sa.select(ArtifactRow).where(
                        sa.and_(
                            ArtifactRow.name == model.id, ArtifactRow.registry_id == registry_id
                        )
                    )
                )
                artifact_row: ArtifactRow = artifact_query_result.scalar_one_or_none()

                if artifact_row is None:
                    # Create new artifact
                    artifact_row = ArtifactRow(
                        type=ArtifactType.MODEL,
                        name=model.id,
                        registry_id=registry_id,
                        registry_type=ArtifactRegistryType.HUGGINGFACE,
                        source_registry_id=registry_id,
                        source_registry_type=ArtifactRegistryType.HUGGINGFACE,
                    )
                    db_sess.add(artifact_row)
                    await db_sess.flush()
                    await db_sess.refresh(artifact_row)

                # Initialize artifact in map if not exists
                if artifact_row.id not in artifacts_map:
                    artifacts_map[artifact_row.id] = (artifact_row, [])

                # Check if artifact revision exists
                revision_query_result = await db_sess.execute(
                    sa.select(ArtifactRevisionRow).where(
                        sa.and_(
                            ArtifactRevisionRow.artifact_id == artifact_row.id,
                            ArtifactRevisionRow.version == model.revision,
                        )
                    )
                )

                existing_revision: ArtifactRevisionRow = revision_query_result.scalar_one_or_none()
                if existing_revision is not None:
                    # Update existing revision
                    # TODO: Reset to SCANNED?
                    if model.modified_at:
                        existing_revision.updated_at = model.modified_at

                    # Check if version row already exists for this artifact
                    existing_version_stmt = sa.select(ArtifactVersionRow).where(
                        sa.and_(
                            ArtifactVersionRow.artifact_id == existing_artifact.id,
                            ArtifactVersionRow.version == model.revision,
                        )
                    )
                    existing_version_result = await db_sess.execute(existing_version_stmt)
                    existing_version = existing_version_result.scalar_one_or_none()

                    # Create version row if it doesn't exist
                    if existing_version is None:
                        artifact_version_row = ArtifactVersionRow(
                            artifact_id=existing_artifact.id, version=model.revision
                        )
                        db_sess.add(artifact_version_row)

                    await db_sess.flush()
                    await db_sess.refresh(existing_revision, attribute_names=["updated_at"])
                    artifacts_map[artifact_row.id][1].append(existing_revision)
                else:
                    # Insert new artifact revision
                    new_revision = ArtifactRevisionRow.from_huggingface_model_data(
                        artifact_id=artifact_row.id,
                        model_data=model,
                    )

                    db_sess.add(new_revision)
                    await db_sess.flush()
                    await db_sess.refresh(
                        new_revision, attribute_names=["id", "created_at", "updated_at"]
                    )
                    artifacts_map[artifact_row.id][1].append(new_revision)

            # Convert to ArtifactDataWithRevisions format
            result: list[ArtifactDataWithRevisions] = []
            for artifact_row, revision_rows in artifacts_map.values():
                artifact_data = artifact_row.to_dataclass()
                revision_data_list = [revision.to_dataclass() for revision in revision_rows]
                result.append(
                    ArtifactDataWithRevisions(artifact=artifact_data, revisions=revision_data_list)
                )

        return result

    @repository_decorator()
    async def associate_artifact_with_storage(
        self,
        artifact_id: uuid.UUID,
        storage_id: uuid.UUID,
    ) -> AssociationArtifactsStoragesData:
        async with self._db.begin_session() as db_sess:
            select_stmt = sa.select(AssociationArtifactsStorageRow.id).where(
                sa.and_(
                    AssociationArtifactsStorageRow.artifact_id == artifact_id,
                    AssociationArtifactsStorageRow.storage_id == storage_id,
                )
            )
            existing = (await db_sess.execute(select_stmt)).scalar_one_or_none()
            if existing is not None:
                return AssociationArtifactsStoragesData(
                    id=existing, artifact_id=artifact_id, storage_id=storage_id
                )

            insert_stmt = (
                sa.insert(AssociationArtifactsStorageRow)
                .values(artifact_id=artifact_id, storage_id=storage_id)
                .returning(AssociationArtifactsStorageRow.id)
            )

            result = await db_sess.execute(insert_stmt)
            existing = result.scalar_one_or_none()

            return AssociationArtifactsStoragesData(
                id=existing,
                artifact_id=artifact_id,
                storage_id=storage_id,
            )

    @repository_decorator()
    async def disassociate_artifact_with_storage(
        self, artifact_id: uuid.UUID, storage_id: uuid.UUID
    ) -> AssociationArtifactsStoragesData:
        async with self._db.begin_session() as db_sess:
            select_result = await db_sess.execute(
                sa.select(AssociationArtifactsStorageRow).where(
                    sa.and_(
                        AssociationArtifactsStorageRow.artifact_id == artifact_id,
                        AssociationArtifactsStorageRow.storage_id == storage_id,
                    )
                )
            )
            existing_row: AssociationArtifactsStorageRow = select_result.scalar_one_or_none()
            if existing_row is None:
                # TODO: Make exception
                raise ArtifactAssociationNotFoundError(
                    f"Association between artifact {artifact_id} and storage {storage_id} does not exist"
                )

            # Store the data before deletion
            association_data = AssociationArtifactsStoragesData(
                id=existing_row.id,
                artifact_id=existing_row.artifact_id,
                storage_id=existing_row.storage_id,
            )

            # Delete the association
            delete_result = await db_sess.execute(
                sa.delete(AssociationArtifactsStorageRow).where(
                    sa.and_(
                        AssociationArtifactsStorageRow.artifact_id == artifact_id,
                        AssociationArtifactsStorageRow.storage_id == storage_id,
                    )
                )
            )

            # TODO: Make exception
            if delete_result.rowcount == 0:
                raise ArtifactAssociationDeletionError("Failed to delete association")

            return association_data

    @repository_decorator()
    async def approve_artifact(self, revision_id: uuid.UUID) -> ArtifactRevisionData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.id == revision_id)
            )
            row: ArtifactRevisionRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRevisionNotFoundError()

            if row.status != ArtifactStatus.NEEDS_APPROVAL:
                raise ArtifactNotVerified("Only verified artifacts could be approved")

            update_stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == revision_id)
                .values(status=ArtifactStatus.AVAILABLE.value)
                .returning(ArtifactRevisionRow)
            )

            result = await db_sess.execute(update_stmt)
            updated_row: ArtifactRevisionRow | None = result.scalar_one_or_none()

            if updated_row is None:
                raise ArtifactUpdateError()

            return updated_row.to_dataclass()

    @repository_decorator()
    async def disapprove_artifact(self, revision_id: uuid.UUID) -> ArtifactRevisionData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.id == revision_id)
            )
            row: ArtifactRevisionRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRevisionNotFoundError()

            if row.status != ArtifactStatus.AVAILABLE:
                raise ArtifactNotVerified("Only approved artifacts could be disapproved")

            update_stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == revision_id)
                .values(status=ArtifactStatus.NEEDS_APPROVAL.value)
                .returning(ArtifactRevisionRow)
            )

            result = await db_sess.execute(update_stmt)
            updated_row: ArtifactRevisionRow | None = result.scalar_one_or_none()

            if updated_row is None:
                raise ArtifactUpdateError()

            return updated_row.to_dataclass()

    @repository_decorator()
    async def delete_artifact(self, artifact_id: uuid.UUID) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(ArtifactRow.id == artifact_id)
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError()

            await db_sess.delete(row)
            await db_sess.flush()

            return artifact_id

    @repository_decorator()
    async def cancel_import_artifact(self, artifact_id: uuid.UUID) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = (
                sa.update(ArtifactRow)
                .where(ArtifactRow.id == artifact_id)
                .values(status=ArtifactStatus.SCANNED)
            )
            await db_sess.execute(stmt)
            return artifact_id

    @repository_decorator()
    async def update_artifact_revision_status(
        self, artifact_revision_id: uuid.UUID, status: ArtifactStatus
    ) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == artifact_revision_id)
                .values(status=status)
            )
            await db_sess.execute(stmt)
            return artifact_revision_id

    @repository_decorator()
    async def update_artifact_revision_bytesize(
        self, artifact_revision_id: uuid.UUID, size: int
    ) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == artifact_revision_id)
                .values(size=size)
            )
            await db_sess.execute(stmt)
            return artifact_revision_id

    @repository_decorator()
    async def update_artifact_revision_readme(
        self, artifact_revision_id: uuid.UUID, readme: str
    ) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == artifact_revision_id)
                .values(readme=readme)
            )
            await db_sess.execute(stmt)
            return artifact_revision_id

    @repository_decorator()
    async def list_artifacts_paginated(
        self,
        *,
        pagination: Optional[PaginationOptions] = None,
        ordering: Optional[ArtifactOrderingOptions] = None,
        filters: Optional[ArtifactFilterOptions] = None,
    ) -> tuple[list[ArtifactData], int]:
        """List artifacts with pagination and filtering.

        Args:
            pagination: Pagination options for the query
            ordering: Ordering options for the query
            filters: Filtering options for artifacts

        Returns:
            Tuple of (artifacts list, total count)
        """
        raise NotImplementedError()
