import uuid

import sqlalchemy as sa

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryData,
    ArtifactRegistryListResult,
)
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier


class ArtifactRegistryDBSource:
    """Database source for artifact registry operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_artifact_registry_data(self, registry_id: uuid.UUID) -> ArtifactRegistryData:
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(
                sa.select(ArtifactRegistryRow).where(ArtifactRegistryRow.registry_id == registry_id)
            )
            row: ArtifactRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {registry_id} not found")
            return row.to_dataclass()

    async def get_artifact_registry_data_by_name(self, registry_name: str) -> ArtifactRegistryData:
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(
                sa.select(ArtifactRegistryRow).where(ArtifactRegistryRow.name == registry_name)
            )
            row: ArtifactRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with name {registry_name} not found")
            return row.to_dataclass()

    async def get_artifact_registry_datas(
        self, registry_ids: list[uuid.UUID]
    ) -> list[ArtifactRegistryData]:
        """
        Get multiple artifact registry entries by their IDs in a single query.
        """
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(
                sa.select(ArtifactRegistryRow).where(
                    ArtifactRegistryRow.registry_id.in_(registry_ids)
                )
            )
            rows: list[ArtifactRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def get_artifact_registry_type(self, registry_id: uuid.UUID) -> ArtifactRegistryType:
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(
                sa.select(ArtifactRegistryRow.type).where(
                    ArtifactRegistryRow.registry_id == registry_id
                )
            )
            typ = result.scalar_one_or_none()
            if typ is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {registry_id} not found")
            return ArtifactRegistryType(typ)

    async def list_artifact_registry_data(self) -> list[ArtifactRegistryData]:
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(sa.select(ArtifactRegistryRow))
            rows: list[ArtifactRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def search_artifact_registries(
        self,
        querier: BatchQuerier,
    ) -> ArtifactRegistryListResult:
        """Searches artifact registries with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ArtifactRegistryRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.ArtifactRegistryRow.to_dataclass() for row in result.rows]

            return ArtifactRegistryListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
