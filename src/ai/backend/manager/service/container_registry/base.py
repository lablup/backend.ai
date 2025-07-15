from __future__ import annotations

import abc
import logging
import uuid
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import load_only

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.image import (
    ContainerRegistryNotFound,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ContainerRegistryRowInfo:
    id: uuid.UUID
    url: str
    registry_name: str
    type: ContainerRegistryType
    project: str
    username: str
    password: str
    ssl_verify: bool
    is_global: bool
    extra: dict[str, Any]


class AbstractPerProjectRegistryQuotaRepository(abc.ABC):
    async def fetch_container_registry_row(
        self, scope_id: ProjectScope
    ) -> ContainerRegistryRowInfo:
        raise NotImplementedError


class PerProjectRegistryQuotaRepository(AbstractPerProjectRegistryQuotaRepository):
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

    @override
    async def fetch_container_registry_row(
        self, scope_id: ProjectScope
    ) -> ContainerRegistryRowInfo:
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
                    f"Container registry info does not exist or is invalid in the group. (group: {project_id})"
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
                    f"Container registry row not found. (registry: {registry_name}, group: {project})"
                )

            return ContainerRegistryRowInfo(
                id=registry.id,
                url=registry.url,
                registry_name=registry.registry_name,
                type=registry.type,
                project=registry.project,
                username=registry.username,
                password=registry.password,
                ssl_verify=registry.ssl_verify,
                is_global=registry.is_global,
                extra=registry.extra,
            )
