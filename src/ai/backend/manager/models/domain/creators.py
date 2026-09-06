"""Creator specs for the domains table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar, override

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE, DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.specs.creator import RoleManagedGlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class DomainCreator(RoleManagedGlobalEntityCreator[DomainRow, DomainData]):
    """Registers a domain, the top-level scope everything else is created under."""

    name: str
    description: str | None = None
    is_active: bool | None = None
    total_resource_slots: ResourceSlot | None = None
    allowed_vfolder_hosts: dict[str, list[str]] | None = None
    allowed_docker_registries: list[str] | None = None
    integration_name: str | None = None
    dotfiles: bytes | None = None

    _MAX_NAME_LENGTH: ClassVar[int] = 64

    def __post_init__(self) -> None:
        candidate = self.name.strip()
        if candidate == "" or len(candidate) > self._MAX_NAME_LENGTH:
            raise InvalidAPIParameters(
                f"Domain name cannot be empty or exceed {self._MAX_NAME_LENGTH} characters."
            )

    @override
    def entity_id(self, row: DomainRow) -> EntityIdentifier:
        return DomainID(row.id)

    @override
    def template_value(self, row: DomainRow) -> ScopeTemplateValue:
        return ScopeTemplateValue(id=row.id, name=row.name, type=DOMAIN_SCOPE_TYPE)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=InvalidAPIParameters(f"Domain with name '{self.name}' already exists"),
            ),
        )

    @override
    def build_row(self) -> DomainRow:
        return DomainRow(
            name=self.name,
            description=self.description,
            is_active=self.is_active if self.is_active is not None else True,
            total_resource_slots=self.total_resource_slots
            if self.total_resource_slots
            else ResourceSlot(),
            allowed_vfolder_hosts=self.allowed_vfolder_hosts
            if self.allowed_vfolder_hosts
            else VFolderHostPermissionMap(),
            allowed_docker_registries=self.allowed_docker_registries
            if self.allowed_docker_registries
            else [],
            integration_id=self.integration_name,  # DB column is integration_id
            dotfiles=self.dotfiles if self.dotfiles else b"\x90",
        )

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return row.to_data()
