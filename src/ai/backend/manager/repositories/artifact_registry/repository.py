import uuid

import sqlalchemy as sa

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for container_registry repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.ARTIFACT_REGISTRY)


class ArtifactRegistryRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def get_artifact_registry_data(self, registry_id: uuid.UUID) -> ArtifactRegistryData:
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(
                sa.select(ArtifactRegistryRow).where(ArtifactRegistryRow.registry_id == registry_id)
            )
            row: ArtifactRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {registry_id} not found")
            return row.to_dataclass()

    @repository_decorator()
    async def get_artifact_registry_data_by_name(self, registry_name: str) -> ArtifactRegistryData:
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(
                sa.select(ArtifactRegistryRow).where(ArtifactRegistryRow.name == registry_name)
            )
            row: ArtifactRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with name {registry_name} not found")
            return row.to_dataclass()

    @repository_decorator()
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

    @repository_decorator()
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

    @repository_decorator()
    async def list_artifact_registry_data(self) -> list[ArtifactRegistryData]:
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(sa.select(ArtifactRegistryRow))
            rows: list[ArtifactRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]
