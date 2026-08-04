"""CreatorSpec implementations for container registry repository."""

from __future__ import annotations

import uuid
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.common.data.entity.container_registry import CONTAINER_REGISTRY_SCOPE_TYPE
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.exception import ContainerRegistryGroupsAlreadyAssociated
from ai.backend.common.identifier.container_registry import ContainerRegistryID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck
from ai.backend.manager.repositories.ops.rbac.provider import ScopeCreation
from ai.backend.manager.repositories.permission_controller.role_manager import (
    ScopeSystemRoleData,
)


@dataclass
class ContainerRegistryCreatorSpec(CreatorSpec[ContainerRegistryRow]):
    """CreatorSpec for container registry creation."""

    url: str
    type: ContainerRegistryType
    registry_name: str
    is_global: bool | None = None
    project: str | None = None
    username: str | None = None
    password: str | None = None
    ssl_verify: bool | None = None
    extra: dict[str, Any] | None = None
    allowed_groups: AllowedGroupsModel | None = None

    @property
    def has_allowed_groups(self) -> bool:
        """Check if allowed_groups is set and has values to process."""
        return self.allowed_groups is not None and len(self.allowed_groups.add) > 0

    @override
    def build_row(self) -> ContainerRegistryRow:
        return ContainerRegistryRow(
            id=uuid.uuid4(),
            url=self.url,
            type=self.type,
            registry_name=self.registry_name,
            is_global=self.is_global,
            project=self.project,
            username=self.username,
            password=self.password,
            ssl_verify=self.ssl_verify,
            extra=self.extra,
        )


@dataclass
class ContainerRegistryScopeCreation(ScopeCreation[ContainerRegistryRow]):
    """Creates a container registry row and the owner scope the registry becomes.

    The registry row itself binds to no parent scope (a plain insert); project
    reachability is granted separately by binding allowed projects to the
    registry's virtual scope."""

    spec: ContainerRegistryCreatorSpec

    @override
    def creator(self) -> RBACEntityCreator[ContainerRegistryRow]:
        return RBACEntityCreator(
            spec=self.spec,
            element_type=RBACElementType.CONTAINER_REGISTRY,
            scope_ref=None,
        )

    @override
    def scope_of(self, row: ContainerRegistryRow) -> ScopeRef:
        return ScopeRef(scope_type=CONTAINER_REGISTRY_SCOPE_TYPE, scope_id=row.id)

    @override
    def system_roles_of(self, row: ContainerRegistryRow) -> Collection[ScopeSystemRoleData]:
        return ()


@dataclass
class ContainerRegistryGroupCreatorSpec(
    CreatorSpec[AssociationContainerRegistriesGroupsRow],
):
    """CreatorSpec for container registry group association."""

    registry_id: ContainerRegistryID
    group_id: ProjectID

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_registry_id_group_id",
                error=ContainerRegistryGroupsAlreadyAssociated(
                    f"Already associated groups for registry_id: {self.registry_id}, group_id: {self.group_id}"
                ),
            ),
        )

    @override
    def build_row(self) -> AssociationContainerRegistriesGroupsRow:
        return AssociationContainerRegistriesGroupsRow(
            registry_id=self.registry_id,
            group_id=self.group_id,
        )
