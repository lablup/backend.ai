import uuid
from typing import Optional

import sqlalchemy as sa

from ai.backend.common.data.storage.registries.types import ModelData, ModelTarget
from ai.backend.common.exception import (
    ArtifactAssociationDeletionError,
    ArtifactAssociationNotFoundError,
    ArtifactNotFoundError,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactRegistryType,
    ArtifactStatus,
)
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.artifact import ArtifactRow
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
    async def get_artifact_by_model_target(self, model_target: ModelTarget) -> ArtifactData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(
                    sa.and_(
                        ArtifactRow.name == model_target.model_id,
                        ArtifactRow.version == model_target.revision,
                    )
                )
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError()
            return row.to_dataclass()

    @repository_decorator()
    async def upsert_huggingface_model_artifacts(
        self,
        model_list: list[ModelData],
        registry_id: uuid.UUID,
        source_registry_id: uuid.UUID,
        source_registry_type: ArtifactRegistryType,
    ) -> list[ArtifactData]:
        async with self._db.begin_session() as db_sess:
            result = []

            for model in model_list:
                # Check if artifact with same model_id and registry_id already exists
                existing_stmt = sa.select(ArtifactRow).where(
                    sa.and_(
                        ArtifactRow.name == model.id,
                        ArtifactRow.registry_id == registry_id,
                    )
                )
                existing_result = await db_sess.execute(existing_stmt)
                existing_artifact = existing_result.scalar_one_or_none()

                if existing_artifact is not None:
                    # Update existing artifacts
                    existing_artifact.source_registry_id = source_registry_id
                    existing_artifact.source_registry_type = source_registry_type
                    if model.modified_at:
                        existing_artifact.updated_at = model.modified_at
                    existing_artifact.authorized = False
                    existing_artifact.version = model.revision

                    await db_sess.flush()
                    await db_sess.refresh(existing_artifact, attribute_names=["updated_at"])
                    result.append(existing_artifact.to_dataclass())
                else:
                    # Insert new artifacts
                    new_artifact = ArtifactRow.from_huggingface_model_data(
                        model,
                        registry_id=registry_id,
                        source_registry_id=source_registry_id,
                        source_registry_type=source_registry_type,
                    )
                    db_sess.add(new_artifact)
                    await db_sess.flush()
                    await db_sess.refresh(
                        new_artifact, attribute_names=["id", "created_at", "updated_at"]
                    )
                    result.append(new_artifact.to_dataclass())

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
    async def authorize_artifact(self, artifact_id: uuid.UUID) -> ArtifactData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(ArtifactRow.id == artifact_id)
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError()

            row.authorized = True
            await db_sess.flush()
            await db_sess.refresh(row, attribute_names=["updated_at"])
            return row.to_dataclass()

    @repository_decorator()
    async def unauthorize_artifact(self, artifact_id: uuid.UUID) -> ArtifactData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(ArtifactRow.id == artifact_id)
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError()

            row.authorized = False
            await db_sess.flush()
            await db_sess.refresh(row, attribute_names=["updated_at"])
            return row.to_dataclass()

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
    async def update_artifact_status(
        self, artifact_id: uuid.UUID, status: ArtifactStatus
    ) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = sa.update(ArtifactRow).where(ArtifactRow.id == artifact_id).values(status=status)
            await db_sess.execute(stmt)
            return artifact_id

    @repository_decorator()
    async def update_artifact_bytesize(self, artifact_id: uuid.UUID, size: int) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = sa.update(ArtifactRow).where(ArtifactRow.id == artifact_id).values(size=size)
            await db_sess.execute(stmt)
            return artifact_id

    @repository_decorator()
    async def update_artifact_readme(self, artifact_id: uuid.UUID, readme: str) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = sa.update(ArtifactRow).where(ArtifactRow.id == artifact_id).values(readme=readme)
            await db_sess.execute(stmt)
            return artifact_id

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
