from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.resource_preset.types import (
    ResourcePresetCreator,
    ResourcePresetModifier,
)

# Layer-specific decorator for resource_preset repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.RESOURCE_PRESET)


class ResourcePresetRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def create_preset_validated(
        self, creator: ResourcePresetCreator
    ) -> Optional[ResourcePresetData]:
        """
        Creates a new resource preset.
        Returns None if a preset with the same name and scaling group already exists.
        """
        async with self._db.begin_session() as session:
            preset_row = await ResourcePresetRow.create(creator, db_session=session)
            if preset_row is None:
                return None
            data = preset_row.to_dataclass()
        return data

    @repository_decorator()
    async def get_preset_by_id(self, preset_id: UUID) -> ResourcePresetData:
        """
        Gets a resource preset by ID.
        Raises ObjectNotFound if the preset doesn't exist.
        """
        async with self._db.begin_session() as session:
            preset_row = await self._get_preset_by_id(session, preset_id)
            if preset_row is None:
                raise ObjectNotFound("Resource preset not found")
            data = preset_row.to_dataclass()
        return data

    @repository_decorator()
    async def get_preset_by_name(self, name: str) -> ResourcePresetData:
        """
        Gets a resource preset by name.
        Raises ObjectNotFound if the preset doesn't exist.
        """
        async with self._db.begin_session() as session:
            preset_row = await self._get_preset_by_name(session, name)
            if preset_row is None:
                raise ObjectNotFound("Resource preset not found")
            data = preset_row.to_dataclass()
        return data

    @repository_decorator()
    async def get_preset_by_id_or_name(
        self, preset_id: Optional[UUID], name: Optional[str]
    ) -> ResourcePresetData:
        """
        Gets a resource preset by ID or name.
        ID takes precedence if both are provided.
        Raises ObjectNotFound if the preset doesn't exist.
        """
        async with self._db.begin_session() as session:
            if preset_id is not None:
                preset_row = await self._get_preset_by_id(session, preset_id)
            elif name is not None:
                preset_row = await self._get_preset_by_name(session, name)
            else:
                raise ValueError("Either preset_id or name must be provided")

            if preset_row is None:
                raise ObjectNotFound("Resource preset not found")
            data = preset_row.to_dataclass()
        return data

    @repository_decorator()
    async def modify_preset_validated(
        self, preset_id: Optional[UUID], name: Optional[str], modifier: ResourcePresetModifier
    ) -> ResourcePresetData:
        """
        Modifies an existing resource preset.
        Raises ObjectNotFound if the preset doesn't exist.
        """
        async with self._db.begin_session() as session:
            if preset_id is not None:
                preset_row = await self._get_preset_by_id(session, preset_id)
            elif name is not None:
                preset_row = await self._get_preset_by_name(session, name)
            else:
                raise ValueError("Either preset_id or name must be provided")

            if preset_row is None:
                raise ObjectNotFound("Resource preset not found")

            to_update = modifier.fields_to_update()
            for key, value in to_update.items():
                setattr(preset_row, key, value)
            await session.flush()
            data = preset_row.to_dataclass()
        return data

    @repository_decorator()
    async def delete_preset_validated(
        self, preset_id: Optional[UUID], name: Optional[str]
    ) -> ResourcePresetData:
        """
        Deletes a resource preset.
        Returns the deleted preset data.
        Raises ObjectNotFound if the preset doesn't exist.
        """
        async with self._db.begin_session() as session:
            if preset_id is not None:
                preset_row = await self._get_preset_by_id(session, preset_id)
            elif name is not None:
                preset_row = await self._get_preset_by_name(session, name)
            else:
                raise ValueError("Either preset_id or name must be provided")

            if preset_row is None:
                raise ObjectNotFound("Resource preset not found")

            data = preset_row.to_dataclass()
            await session.delete(preset_row)
        return data

    @repository_decorator()
    async def list_presets(
        self, scaling_group_name: Optional[str] = None
    ) -> list[ResourcePresetData]:
        """
        Lists all resource presets.
        If scaling_group_name is provided, returns presets for that scaling group and global presets.
        """
        async with self._db.begin_readonly_session() as session:
            query = sa.select(ResourcePresetRow)
            query_condition = ResourcePresetRow.scaling_group_name.is_(None)
            if scaling_group_name is not None:
                query_condition = sa.or_(
                    query_condition, ResourcePresetRow.scaling_group_name == scaling_group_name
                )
            query = query.where(query_condition)

            presets = []
            async for row in await session.stream_scalars(query):
                presets.append(row.to_dataclass())

        return presets

    async def _get_preset_by_id(
        self, session: SASession, preset_id: UUID
    ) -> Optional[ResourcePresetRow]:
        """
        Private method to get a preset by ID using an existing session.
        """
        return await session.scalar(
            sa.select(ResourcePresetRow).where(ResourcePresetRow.id == preset_id)
        )

    async def _get_preset_by_name(
        self, session: SASession, name: str
    ) -> Optional[ResourcePresetRow]:
        """
        Private method to get a preset by name using an existing session.
        """
        return await session.scalar(
            sa.select(ResourcePresetRow).where(ResourcePresetRow.name == name)
        )
