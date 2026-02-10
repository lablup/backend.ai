from __future__ import annotations

import logging
import uuid
from typing import cast

import sqlalchemy as sa

from ai.backend.common.container_registry import AllowedGroupsModel
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryData,
)
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.errors.image import (
    ContainerRegistryNotFound,
)
from ai.backend.manager.models.container_registry import (
    ContainerRegistryRow,
    ContainerRegistryValidator,
    ContainerRegistryValidatorArgs,
)
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.purger import Purger, execute_purger
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.repositories.container_registry.creators import ContainerRegistryCreatorSpec
from ai.backend.manager.repositories.container_registry.updaters import (
    ContainerRegistryUpdaterSpec,
    handle_allowed_groups_update,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ContainerRegistryDBSource:
    """Database source for container registry-related operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def insert_registry(
        self,
        creator: Creator[ContainerRegistryRow],
    ) -> ContainerRegistryData:
        spec = cast(ContainerRegistryCreatorSpec, creator.spec)
        async with self._db.begin_session() as session:
            creator_result = await execute_creator(session, creator)
            container_registry_row: ContainerRegistryRow = creator_result.row

            if spec.has_allowed_groups:
                allowed_groups = cast(AllowedGroupsModel, spec.allowed_groups)
                await handle_allowed_groups_update(
                    session, container_registry_row.id, allowed_groups
                )

            return container_registry_row.to_dataclass()

    async def update_registry(
        self,
        updater: Updater[ContainerRegistryRow],
    ) -> ContainerRegistryData:
        async with self._db.begin_session() as session:
            updater.spec = cast(ContainerRegistryUpdaterSpec, updater.spec)
            registry_id = cast(uuid.UUID, updater.pk_value)

            stmt = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == registry_id)
            result = await session.execute(stmt)
            reg_row = result.scalar_one_or_none()

            if reg_row is None:
                raise ContainerRegistryNotFound(f"Container registry not found (id:{registry_id})")

            if updater.spec.has_allowed_groups_update is True:
                await handle_allowed_groups_update(
                    session, registry_id, updater.spec.allowed_groups.value()
                )

            to_update = updater.spec.build_values()
            if to_update == {}:  # means no fields to update or only allowed_groups updated
                return reg_row.to_dataclass()

            session.expire(reg_row)  # Expire to get updated values after update
            update_result = await execute_updater(session, updater)
            if update_result is None:
                raise ContainerRegistryNotFound(f"Container registry not found (id:{registry_id})")

            reg_row = update_result.row
            validator = ContainerRegistryValidator(
                ContainerRegistryValidatorArgs(
                    type=reg_row.type,
                    project=reg_row.project,
                    url=reg_row.url,
                )
            )
            validator.validate()
            return reg_row.to_dataclass()

    async def remove_registry(
        self,
        purger: Purger[ContainerRegistryRow],
    ) -> ContainerRegistryData:
        async with self._db.begin_session() as session:
            result = await execute_purger(session, purger)

            if result is None:
                raise ContainerRegistryNotFound(
                    f"Container registry not found (id:{purger.pk_value})"
                )

            return result.row.to_dataclass()

    async def fetch_by_registry_and_project(
        self,
        registry_name: str,
        project: str | None = None,
    ) -> ContainerRegistryData:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name,
            )
            if project:
                stmt = stmt.where(ContainerRegistryRow.project == project)

            row: ContainerRegistryRow | None = await session.scalar(stmt)
            if not row:
                raise ContainerRegistryNotFound()
            return row.to_dataclass()

    async def fetch_by_registry_name(self, registry_name: str) -> list[ContainerRegistryData]:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name
            )
            result = await session.execute(stmt)
            rows = list(result.scalars().all())
            return [row.to_dataclass() for row in rows]

    async def fetch_all(self) -> list[ContainerRegistryData]:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ContainerRegistryRow)
            result = await session.execute(stmt)
            rows = list(result.scalars().all())
            return [row.to_dataclass() for row in rows]

    async def clear_registry_images(
        self,
        registry_name: str,
        project: str | None,
    ) -> ContainerRegistryData:
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

            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name,
            )
            if project:
                stmt = stmt.where(ContainerRegistryRow.project == project)

            row: ContainerRegistryRow | None = await session.scalar(stmt)
            if not row:
                raise ContainerRegistryNotFound()
            return row.to_dataclass()

    async def fetch_known_registries(self) -> dict[str, str]:
        async with self._db.begin_readonly_session_read_committed() as session:
            known_registries_map = await ContainerRegistryRow.get_known_container_registries(
                session
            )

            known_registries = {}
            for project, registries in known_registries_map.items():
                for registry_name, url in registries.items():
                    if project not in known_registries:
                        known_registries[f"{project}/{registry_name}"] = url.human_repr()

            return known_registries

    async def fetch_registry_row_for_scanner(
        self,
        registry_name: str,
        project: str | None = None,
    ) -> ContainerRegistryRow:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name,
            )
            if project:
                stmt = stmt.where(ContainerRegistryRow.project == project)

            row: ContainerRegistryRow | None = await session.scalar(stmt)
            if not row:
                raise ContainerRegistryNotFound()
            return row
