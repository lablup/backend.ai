"""CreatorSpec implementations for group repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import EntityType, RelationType, ScopeType
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class GroupCreatorSpec(CreatorSpec[GroupRow]):
    """CreatorSpec for group creation."""

    name: str
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

    @property
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
    def build_row(self) -> GroupRow:
        return GroupRow(
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


@dataclass
class ProjectUserMembershipCreatorSpec(CreatorSpec[AssociationScopesEntitiesRow]):
    """CreatorSpec for user-project membership (PROJECT/USER ASE row)."""

    user_id: UUID
    project_id: UUID

    @override
    def build_row(self) -> AssociationScopesEntitiesRow:
        return AssociationScopesEntitiesRow(
            scope_type=ScopeType.PROJECT,
            scope_id=str(self.project_id),
            entity_type=EntityType.USER,
            entity_id=str(self.user_id),
            relation_type=RelationType.AUTO,
        )
