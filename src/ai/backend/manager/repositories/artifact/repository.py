import uuid
from typing import Optional

import sqlalchemy as sa

from ai.backend.common.data.storage.registries.types import ModelData
from ai.backend.common.exception import (
    ArtifactAssociationCreationError,
    ArtifactAssociationDeletionError,
    ArtifactAssociationNotFoundError,
    ArtifactNotFoundError,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.association_artifacts_storages import AssociationArtifactsStorageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

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
    async def insert_huggingface_model_artifacts(
        self,
        model_list: list[ModelData],
        registry_id: uuid.UUID,
        source_registry_id: Optional[uuid.UUID],
    ) -> list[ArtifactData]:
        async with self._db.begin_session() as db_sess:
            models = [
                ArtifactRow.from_huggingface_model_data(
                    model, registry_id=registry_id, source_registry_id=source_registry_id
                )
                for model in model_list
            ]
            db_sess.add_all(models)
            await db_sess.flush()

            for m in models:
                await db_sess.refresh(m, attribute_names=["id", "created_at", "updated_at"])

            result = [model.to_dataclass() for model in models]
        return result

    @repository_decorator()
    async def associate_artifact_with_storage(
        self, artifact_id: uuid.UUID, storage_id: uuid.UUID
    ) -> AssociationArtifactsStoragesData:
        async with self._db.begin_session() as db_sess:
            stmt = (
                sa.insert(AssociationArtifactsStorageRow)
                .values(artifact_id=artifact_id, storage_id=storage_id)
                .returning(AssociationArtifactsStorageRow.id)
            )
            result = await db_sess.execute(stmt)
            inserted_id = result.scalar_one_or_none()
            if inserted_id is None:
                raise ArtifactAssociationCreationError("Failed to create association")

            return AssociationArtifactsStoragesData(
                id=inserted_id,
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
