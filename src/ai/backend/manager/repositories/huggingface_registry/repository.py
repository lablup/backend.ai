import uuid

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.huggingface_registry.creator import HuggingFaceRegistryCreator
from ai.backend.manager.data.huggingface_registry.modifier import HuggingFaceRegistryModifier
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for artifact registry repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.ARTIFACT_REGISTRY)


class HuggingFaceRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def get_registry_data_by_id(self, registry_id: uuid.UUID) -> HuggingFaceRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(HuggingFaceRegistryRow).where(HuggingFaceRegistryRow.id == registry_id)
            )
            row: HuggingFaceRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ValueError(f"Registry with ID {registry_id} not found")
            return row.to_dataclass()

    @repository_decorator()
    async def get_registry_data_by_name(self, name: str) -> HuggingFaceRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(HuggingFaceRegistryRow).where(HuggingFaceRegistryRow.name == name)
            )
            row: HuggingFaceRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ValueError(f"Registry with name {name} not found")
            return row.to_dataclass()

    @repository_decorator()
    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> HuggingFaceRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow)
                .where(ArtifactRow.id == artifact_id)
                .options(selectinload(ArtifactRow.huggingface_registry))
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ValueError(f"Artifact with ID {artifact_id} not found")
            return row.huggingface_registry.to_dataclass()

    @repository_decorator()
    async def create(self, creator: HuggingFaceRegistryCreator) -> HuggingFaceRegistryData:
        """
        Create a new Hugging Face registry entry.
        """
        async with self._db.begin_session() as db_session:
            huggingface_registry_data = creator.fields_to_store()
            huggingface_registry_row = HuggingFaceRegistryRow(**huggingface_registry_data)
            db_session.add(huggingface_registry_row)
            await db_session.flush()
            await db_session.refresh(huggingface_registry_row)
            return huggingface_registry_row.to_dataclass()

    @repository_decorator()
    async def update(
        self, registry_id: uuid.UUID, modifier: HuggingFaceRegistryModifier
    ) -> HuggingFaceRegistryData:
        """
        Update an existing Hugging Face registry entry in the database.
        """
        async with self._db.begin_session() as db_session:
            data = modifier.fields_to_update()
            update_stmt = (
                sa.update(HuggingFaceRegistryRow)
                .where(HuggingFaceRegistryRow.id == registry_id)
                .values(**data)
                .returning(*sa.select(HuggingFaceRegistryRow).selected_columns)
            )
            stmt = sa.select(HuggingFaceRegistryRow).from_statement(update_stmt)
            row: HuggingFaceRegistryRow = (await db_session.execute(stmt)).scalars().one()
            return row.to_dataclass()

    @repository_decorator()
    async def delete(self, storage_id: uuid.UUID) -> uuid.UUID:
        """
        Delete an existing Hugging Face registry entry from the database.
        """
        async with self._db.begin_session() as db_session:
            delete_query = (
                sa.delete(HuggingFaceRegistryRow)
                .where(HuggingFaceRegistryRow.id == storage_id)
                .returning(HuggingFaceRegistryRow.id)
            )
            result = await db_session.execute(delete_query)
            deleted_id = result.scalar()
            return deleted_id

    @repository_decorator()
    async def list_registries(self) -> list[HuggingFaceRegistryData]:
        """
        List all Hugging Face registry entries from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(HuggingFaceRegistryRow)
            result = await db_session.execute(query)
            rows: list[HuggingFaceRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]
