import uuid

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryCreatorMeta,
    ArtifactRegistryModifierMeta,
)
from ai.backend.manager.data.huggingface_registry.creator import HuggingFaceRegistryCreator
from ai.backend.manager.data.huggingface_registry.modifier import HuggingFaceRegistryModifier
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.errors.artifact import ArtifactNotFoundError
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
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
                sa.select(HuggingFaceRegistryRow)
                .where(HuggingFaceRegistryRow.id == registry_id)
                .options(selectinload(HuggingFaceRegistryRow.meta))
            )
            row: HuggingFaceRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {registry_id} not found")
            return row.to_dataclass()

    @repository_decorator()
    async def get_registry_data_by_name(self, name: str) -> HuggingFaceRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRegistryRow)
                .where(ArtifactRegistryRow.name == name)
                .options(
                    selectinload(ArtifactRegistryRow.huggingface_registries).selectinload(
                        HuggingFaceRegistryRow.meta
                    )
                )
            )
            row: ArtifactRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with name {name} not found")
            return row.huggingface_registries.to_dataclass()

    @repository_decorator()
    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> HuggingFaceRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow)
                .where(ArtifactRow.id == artifact_id)
                .options(
                    selectinload(ArtifactRow.huggingface_registry).selectinload(
                        HuggingFaceRegistryRow.meta
                    ),
                )
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found")
            return row.huggingface_registry.to_dataclass()

    @repository_decorator()
    async def create(
        self, creator: HuggingFaceRegistryCreator, meta: ArtifactRegistryCreatorMeta
    ) -> HuggingFaceRegistryData:
        """
        Create a new Hugging Face registry entry.
        """
        async with self._db.begin_session() as db:
            hf_insert = (
                sa.insert(HuggingFaceRegistryRow)
                .values(**creator.fields_to_store())
                .returning(HuggingFaceRegistryRow.id)
            )
            hf_id = (await db.execute(hf_insert)).scalar_one()

            reg_insert = sa.insert(ArtifactRegistryRow).values(
                name=meta.name,
                registry_id=hf_id,
                type=ArtifactRegistryType.HUGGINGFACE,
            )
            await db.execute(reg_insert)

            stmt = (
                sa.select(HuggingFaceRegistryRow)
                .where(HuggingFaceRegistryRow.id == hf_id)
                .options(selectinload(HuggingFaceRegistryRow.meta))
            )
            row: HuggingFaceRegistryRow | None = (await db.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {hf_id} not found")

            return row.to_dataclass()

    @repository_decorator()
    async def update(
        self,
        registry_id: uuid.UUID,
        modifier: HuggingFaceRegistryModifier,
        meta: ArtifactRegistryModifierMeta,
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
                .returning(HuggingFaceRegistryRow.id)
            )

            result = await db_session.execute(update_stmt)
            inserted_row_id = result.scalar()

            if (name := meta.name.optional_value()) is not None:
                await db_session.execute(
                    sa.update(ArtifactRegistryRow)
                    .where(ArtifactRegistryRow.registry_id == inserted_row_id)
                    .values(name=name)
                )

            # Reselect for the `selectinload`
            row = (
                await db_session.execute(
                    sa.select(HuggingFaceRegistryRow)
                    .where(HuggingFaceRegistryRow.id == inserted_row_id)
                    .options(selectinload(HuggingFaceRegistryRow.meta))
                )
            ).scalar_one()

            return row.to_dataclass()

    @repository_decorator()
    async def delete(self, registry_id: uuid.UUID) -> uuid.UUID:
        """
        Delete an existing Hugging Face registry entry from the database.
        """
        async with self._db.begin_session() as db_session:
            delete_query = (
                sa.delete(HuggingFaceRegistryRow)
                .where(HuggingFaceRegistryRow.id == registry_id)
                .returning(HuggingFaceRegistryRow.id)
            )
            result = await db_session.execute(delete_query)
            deleted_id = result.scalar()

            delete_meta_query = sa.delete(ArtifactRegistryRow).where(
                ArtifactRegistryRow.id == registry_id
            )
            await db_session.execute(delete_meta_query)
            return deleted_id

    @repository_decorator()
    async def get_registries_by_ids(
        self, registry_ids: list[uuid.UUID]
    ) -> list[HuggingFaceRegistryData]:
        """
        Get multiple Hugging Face registry entries by their IDs in a single query.
        """
        async with self._db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(HuggingFaceRegistryRow)
                .where(HuggingFaceRegistryRow.id.in_(registry_ids))
                .options(selectinload(HuggingFaceRegistryRow.meta))
            )
            rows: list[HuggingFaceRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    @repository_decorator()
    async def list_registries(self) -> list[HuggingFaceRegistryData]:
        """
        List all Hugging Face registry entries from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(HuggingFaceRegistryRow).options(
                selectinload(HuggingFaceRegistryRow.meta)
            )
            result = await db_session.execute(query)
            rows: list[HuggingFaceRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]
