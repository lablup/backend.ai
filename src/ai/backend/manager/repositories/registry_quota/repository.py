"""
Repository for fetching container registry information for quota management.

This repository was migrated from `ai.backend.manager.service.container_registry.base`.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, cast, override
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import load_only

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass
class ContainerRegistryRowInfo:
    id: UUID
    url: str
    registry_name: str
    type: ContainerRegistryType
    project: str
    username: str
    password: str
    ssl_verify: bool
    is_global: bool
    extra: dict[str, Any]


class AbstractRegistryQuotaRepository(abc.ABC):
    @abc.abstractmethod
    async def fetch_container_registry_row(
        self, scope_id: ProjectScope
    ) -> ContainerRegistryRowInfo:
        raise NotImplementedError


class RegistryQuotaRepository(AbstractRegistryQuotaRepository):
    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @classmethod
    def _is_valid_group_row(cls, group_row: GroupRow | None) -> bool:
        if group_row is None:
            return False
        container_registry = group_row.container_registry
        if not container_registry:
            return False
        return "registry" in container_registry and "project" in container_registry

    @override
    async def fetch_container_registry_row(
        self, scope_id: ProjectScope
    ) -> ContainerRegistryRowInfo:
        async with self._db.begin_readonly_session() as db_sess:
            project_id = scope_id.project_id
            group_query = (
                sa.select(GroupRow)
                .where(GroupRow.id == project_id)
                .options(load_only(GroupRow.container_registry))
            )
            result = await db_sess.execute(group_query)
            group_row = result.scalar_one_or_none()

            if not RegistryQuotaRepository._is_valid_group_row(group_row):
                raise ContainerRegistryNotFound(
                    f"Container registry info does not exist or is invalid in the group. (group: {project_id})"
                )

            assert group_row is not None
            container_registry = group_row.container_registry
            assert container_registry is not None
            registry_name, project = (
                container_registry["registry"],
                container_registry["project"],
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
                type=cast(ContainerRegistryType, registry.type),
                project=registry.project or "",
                username=registry.username,
                password=registry.password,
                ssl_verify=registry.ssl_verify,
                is_global=registry.is_global,
                extra=registry.extra,
            )
