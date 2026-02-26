"""Database source for container registry quota repository operations."""

from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only

from ai.backend.manager.data.container_registry.types import PerProjectContainerRegistryInfo
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class PerProjectRegistryQuotaDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def fetch_container_registry_row(
        self, scope_id: ProjectScope
    ) -> PerProjectContainerRegistryInfo:
        async with self._db.begin_readonly_session() as db_sess:
            project_id = scope_id.project_id
            container_registry_id = await self._fetch_project_container_registry_id(
                db_sess, project_id
            )

            if container_registry_id is None:
                raise ContainerRegistryNotFound(
                    f"Container registry info does not exist or is invalid in the project. (project: {project_id})"
                )

            registry_row = await self._fetch_registry_row_by_id(db_sess, container_registry_id)

            if registry_row is None:
                raise ContainerRegistryNotFound(
                    f"Container registry row not found. (id: {container_registry_id})"
                )

            return PerProjectContainerRegistryInfo(
                id=registry_row.id,
                url=registry_row.url,
                registry_name=registry_row.registry_name,
                type=registry_row.type,
                project=registry_row.project or "",
                username=registry_row.username or "",
                password=registry_row.password or "",
                ssl_verify=registry_row.ssl_verify if registry_row.ssl_verify is not None else True,
                is_global=registry_row.is_global if registry_row.is_global is not None else False,
                extra=registry_row.extra or {},
            )

    async def _fetch_project_container_registry_id(
        self,
        db_sess: SASession,
        project_id: UUID,
    ) -> UUID | None:
        project_query = (
            sa.select(GroupRow)
            .where(GroupRow.id == project_id)
            .options(load_only(GroupRow.container_registry_id))
        )
        result = await db_sess.execute(project_query)
        project_row = result.scalar_one_or_none()
        if project_row is None:
            return None
        return project_row.container_registry_id

    async def _fetch_registry_row_by_id(
        self,
        db_sess: SASession,
        registry_id: UUID,
    ) -> ContainerRegistryRow | None:
        registry_query = sa.select(ContainerRegistryRow).where(
            ContainerRegistryRow.id == registry_id
        )
        result = await db_sess.execute(registry_query)
        return result.scalars().one_or_none()
