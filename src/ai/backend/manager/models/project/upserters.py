"""Upsert specs for the groups table."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_policy import ProjectResourcePolicyUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import ResourceSlot, VFolderHostPermission
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
from ai.backend.manager.models.project.searchable_fields import ProjectSearchableFields
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("ProjectUpserter",)


@dataclass
class ProjectUpserter(EntityUpserter[ProjectRow, ProjectData]):
    """Write a project under its stated id, created in its domain and `global` as the
    project creator does. Conflict key: id. The domain, named by id, the type and the
    creator are written on insert only."""

    id: ProjectID
    domain_id: DomainID
    project_type: ProjectType
    creator_id: UserID | None
    name: str
    resource_policy_id: ProjectResourcePolicyUUID
    description: str | None
    is_active: bool
    total_resource_slots: ResourceSlot
    allowed_vfolder_hosts: dict[str, list[VFolderHostPermission]]

    @override
    def entity_id(self, row: ProjectRow) -> ProjectID:
        return ProjectID(row.id)

    @override
    def created_in(self, row: ProjectRow) -> Collection[EntityIdentifier]:
        return (self.domain_id, global_entity_id(GlobalEntityName.GLOBAL))

    @override
    def row_class(self) -> type[ProjectRow]:
        return ProjectRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        """A domain or resource policy id naming no row leaves its name column NULL,
        which the column refuses."""
        return {
            "id": self.id,
            "domain_name": sa.select(DomainRow.name)
            .where(DomainRow.id == self.domain_id)
            .scalar_subquery(),
            "type": self.project_type,
            "creator_id": self.creator_id,
            **self._values(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "resource_policy": sa.select(ProjectResourcePolicyRow.name)
            .where(ProjectResourcePolicyRow.uuid == self.resource_policy_id)
            .scalar_subquery(),
            "description": self.description,
            "is_active": self.is_active,
            "total_resource_slots": self.total_resource_slots,
            "allowed_vfolder_hosts": self.allowed_vfolder_hosts,
        }

    @override
    def to_data(self, row: ProjectRow) -> ProjectData:
        return ProjectSearchableFields.own.to_data(row)
