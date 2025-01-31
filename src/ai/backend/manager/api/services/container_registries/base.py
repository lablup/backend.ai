from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import load_only

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.exceptions import (
    ContainerRegistryNotFound,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

if TYPE_CHECKING:
    pass

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PerProjectRegistryQuotaRepository:
    """ """

    def __init__(self, db: ExtendedAsyncSAEngine):
        self.db = db

    @classmethod
    def _is_valid_group_row(cls, group_row: GroupRow) -> bool:
        return (
            group_row
            and group_row.container_registry
            and "registry" in group_row.container_registry
            and "project" in group_row.container_registry
        )

    async def fetch_container_registry_row(self, scope_id: ProjectScope) -> ContainerRegistryRow:
        async with self.db.begin_readonly_session() as db_sess:
            project_id = scope_id.project_id
            group_query = (
                sa.select(GroupRow)
                .where(GroupRow.id == project_id)
                .options(load_only(GroupRow.container_registry))
            )
            result = await db_sess.execute(group_query)
            group_row = result.scalar_one_or_none()

            if not PerProjectRegistryQuotaRepository._is_valid_group_row(group_row):
                raise ContainerRegistryNotFound(
                    f"Container registry info does not exist or is invalid in the group. (gr: {project_id})"
                )

            registry_name, project = (
                group_row.container_registry["registry"],
                group_row.container_registry["project"],
            )

            registry_query = sa.select(ContainerRegistryRow).where(
                (ContainerRegistryRow.registry_name == registry_name)
                & (ContainerRegistryRow.project == project)
            )

            result = await db_sess.execute(registry_query)
            registry = result.scalars().one_or_none()

            if not registry:
                raise ContainerRegistryNotFound(
                    f"Specified container registry row not found. (cr: {registry_name}, gr: {project})"
                )

            return registry
