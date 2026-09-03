"""Creator specs for the groups table."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
from ai.backend.manager.models.specs.creator import RoleManagedEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ProjectCreator(RoleManagedEntityCreator[ProjectRow, ProjectData]):
    """Registers a project under a domain."""

    name: str
    domain_id: DomainID
    domain_name: str
    type: ProjectType | None = None
    description: str | None = None
    is_active: bool | None = None
    total_resource_slots: ResourceSlot | None = None
    allowed_vfolder_hosts: VFolderHostPermissionMap | None = None
    integration_name: str | None = None
    resource_policy: str | None = None
    container_registry: dict[str, str] | None = None
    dotfiles: bytes | None = None

    @classmethod
    def model_store(cls, domain_id: DomainID, domain_name: str) -> ProjectCreator:
        """The model-store project a domain is registered with."""
        return cls(
            name="model-store",
            domain_id=domain_id,
            domain_name=domain_name,
            description="Model Store",
            resource_policy="default",
            type=ProjectType.MODEL_STORE,
        )

    @override
    def entity_id(self, row: ProjectRow) -> EntityIdentifier:
        return ProjectID(row.id)

    @override
    def created_in(self, row: ProjectRow) -> Collection[EntityIdentifier]:
        return (self.domain_id,)

    @override
    def template_value(self, row: ProjectRow) -> ScopeTemplateValue:
        return ScopeTemplateValue(id=row.id, name=row.name, type=PROJECT_SCOPE_TYPE)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=InvalidAPIParameters(
                    f"Group with name '{self.name}' already exists in domain '{self.domain_name}'"
                ),
                constraint_name="uq_groups_name_domain_name",
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=InvalidAPIParameters(
                    f"Cannot create group: Domain '{self.domain_name}' does not exist"
                ),
                constraint_name="fk_groups_domain_name_domains",
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=InvalidAPIParameters(
                    f"Cannot create group: Resource policy '{self.resource_policy}' does not exist"
                ),
                constraint_name="fk_groups_resource_policy_project_resource_policies",
            ),
        )

    @override
    def build_row(self) -> ProjectRow:
        return ProjectRow(
            name=self.name,
            domain_name=self.domain_name,
            type=self.type or ProjectType.GENERAL,
            description=self.description,
            is_active=self.is_active if self.is_active is not None else True,
            total_resource_slots=self.total_resource_slots or ResourceSlot(),
            allowed_vfolder_hosts=self.allowed_vfolder_hosts or VFolderHostPermissionMap(),
            integration_id=self.integration_name,  # DB column is integration_id
            resource_policy=self.resource_policy,
            dotfiles=self.dotfiles,
            container_registry=self.container_registry,
        )

    @override
    def to_data(self, row: ProjectRow) -> ProjectData:
        return row.to_data()
