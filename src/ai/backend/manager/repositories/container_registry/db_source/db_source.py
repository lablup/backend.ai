from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.container_registry import AllowedGroupsModel
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryCreator,
    ContainerRegistryData,
    ContainerRegistryModifier,
)
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.errors.image import (
    ContainerRegistryGroupsAssociationNotFound,
    ContainerRegistryNotFound,
)
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import (
    ContainerRegistryRow,
    ContainerRegistryValidator,
    ContainerRegistryValidatorArgs,
)
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ContainerRegistryDBSource:
    """Database source for container registry-related operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def insert_registry(
        self,
        creator: ContainerRegistryCreator,
    ) -> ContainerRegistryData:
        async with self._db.begin_session() as db_session:
            reg_row = ContainerRegistryRow.from_creator(creator)
            db_session.add(reg_row)
            await db_session.flush()
            await db_session.refresh(reg_row)

        if creator.allowed_groups:
            await self._update_registry_access_allowed_groups(
                db_session, reg_row.id, creator.allowed_groups
            )

        return reg_row.to_dataclass()

    async def update_registry(
        self,
        registry_id: UUID,
        modifier: ContainerRegistryModifier,
    ) -> ContainerRegistryData:
        async with self._db.begin_session() as session:
            result = await session.execute(
                sa.update(ContainerRegistryRow)
                .where(ContainerRegistryRow.id == registry_id)
                .values(modifier.fields_to_update())
            )

            if result.rowcount == 0:
                raise ContainerRegistryNotFound(f"Container registry not found (id:{registry_id})")

            reg_row = await session.scalar(
                sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == registry_id)
            )

            validator = ContainerRegistryValidator(
                ContainerRegistryValidatorArgs(
                    type=reg_row.type,
                    project=reg_row.project,
                    url=reg_row.url,
                )
            )
            validator.validate()

        if modifier.allowed_groups.optional_value() is not None:
            await self._update_registry_access_allowed_groups(
                session,
                registry_id,
                modifier.allowed_groups.value(),
            )

        return reg_row.to_dataclass()

    async def _update_registry_access_allowed_groups(
        self, session: SASession, registry_id: UUID, allowed_groups: AllowedGroupsModel
    ) -> None:
        async with self._db.begin_session() as session:
            if allowed_groups.add:
                insert_values = [
                    {"registry_id": registry_id, "group_id": group_id}
                    for group_id in allowed_groups.add
                ]

                insert_query = sa.insert(AssociationContainerRegistriesGroupsRow).values(
                    insert_values
                )
                await session.execute(insert_query)
            if allowed_groups.remove:
                delete_query = (
                    sa.delete(AssociationContainerRegistriesGroupsRow)
                    .where(AssociationContainerRegistriesGroupsRow.registry_id == registry_id)
                    .where(
                        AssociationContainerRegistriesGroupsRow.group_id.in_(allowed_groups.remove)
                    )
                )
                result = await session.execute(delete_query)
                if result.rowcount == 0:
                    raise ContainerRegistryGroupsAssociationNotFound(
                        f"Tried to remove non-existing associations for registry_id: {registry_id}, group_ids: {allowed_groups.remove}"
                    )

    async def delete_registry(
        self,
        registry_id: UUID,
    ) -> ContainerRegistryData:
        async with self._db.begin_session() as db_session:
            reg_row: Optional[ContainerRegistryRow] = await db_session.scalar(
                sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == registry_id)
            )
            if reg_row is None:
                raise ContainerRegistryNotFound(f"Container registry not found (id:{registry_id})")
            registry_data = reg_row.to_dataclass()
            await db_session.execute(
                sa.delete(ContainerRegistryRow).where(ContainerRegistryRow.id == registry_id)
            )
        return registry_data

    async def fetch_by_registry_and_project(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryData:
        """Fetch container registry data by registry name and optional project."""
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name,
            )
            if project:
                stmt = stmt.where(ContainerRegistryRow.project == project)

            row: Optional[ContainerRegistryRow] = await session.scalar(stmt)
            if row is None:
                raise ContainerRegistryNotFound()
            return row.to_dataclass()

    async def fetch_by_registry_name(self, registry_name: str) -> list[ContainerRegistryData]:
        """Fetch all container registries with the given registry name."""
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name
            )
            result = await session.execute(stmt)
            rows: list[ContainerRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def fetch_all(self) -> list[ContainerRegistryData]:
        """Fetch all container registries."""
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ContainerRegistryRow)
            result = await session.execute(stmt)
            rows: list[ContainerRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def mark_images_as_deleted(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> None:
        """Mark all images as deleted for a given registry and optional project."""
        async with self._db.begin_session() as session:
            update_stmt = (
                sa.update(ImageRow)
                .where(ImageRow.registry == registry_name)
                .where(ImageRow.status != ImageStatus.DELETED)
                .values(status=ImageStatus.DELETED)
            )
            if project:
                update_stmt = update_stmt.where(ImageRow.project == project)

            await session.execute(update_stmt)

    async def fetch_known_registries(self) -> dict[str, str]:
        """Fetch all known container registries from the database."""
        async with self._db.begin_readonly_session() as session:
            known_registries_map = await ContainerRegistryRow.get_known_container_registries(
                session
            )

            known_registries = {}
            for project, registries in known_registries_map.items():
                for registry_name, url in registries.items():
                    if project not in known_registries:
                        known_registries[f"{project}/{registry_name}"] = url.human_repr()

            return known_registries

    async def fetch_registry_row(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryRow:
        """
        Fetch the raw ContainerRegistryRow object.
        Raise ContainerRegistryNotFound if registry is not found.
        """
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name,
            )
            if project:
                stmt = stmt.where(ContainerRegistryRow.project == project)

            row: Optional[ContainerRegistryRow] = await session.scalar(stmt)
            if row is None:
                raise ContainerRegistryNotFound()
            return row
