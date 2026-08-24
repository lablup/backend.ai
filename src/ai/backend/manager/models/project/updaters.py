"""Update specs for the groups table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.project.types import ProjectData, ProjectStatus
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.project.conditions import ProjectConditions
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater, GuardedDataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ProjectUpdater(GuardedDataUpdater[ProjectRow, ProjectData]):
    """Edits a project's settings; refuses while a purge is working through it."""

    project_id: ProjectID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    domain_name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    total_resource_slots: OptionalState[ResourceSlot] = field(
        default_factory=OptionalState[ResourceSlot].nop
    )
    allowed_vfolder_hosts: OptionalState[dict[str, str]] = field(
        default_factory=OptionalState[dict[str, str]].nop
    )
    integration_name: TriState[str] = field(default_factory=TriState[str].nop)
    resource_policy: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    container_registry: TriState[dict[str, str]] = field(
        default_factory=TriState[dict[str, str]].nop
    )
    dotfiles: OptionalState[bytes] = field(default_factory=OptionalState[bytes].nop)

    @property
    @override
    def row_class(self) -> type[ProjectRow]:
        return ProjectRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ProjectRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.project_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        return [ProjectConditions.not_being_purged()]

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.is_active.update_dict(to_update, "is_active")
        self.domain_name.update_dict(to_update, "domain_name")
        self.total_resource_slots.update_dict(to_update, "total_resource_slots")
        self.allowed_vfolder_hosts.update_dict(to_update, "allowed_vfolder_hosts")
        # Field is named integration_name above model layer; DB column remains integration_id.
        self.integration_name.update_dict(to_update, "integration_id")
        self.resource_policy.update_dict(to_update, "resource_policy")
        self.container_registry.update_dict(to_update, "container_registry")
        self.dotfiles.update_dict(to_update, "dotfiles")
        return to_update

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: ProjectRow) -> ProjectData:
        return row.to_data()


@dataclass
class ProjectDotfilesUpdater(DataUpdater[ProjectRow, ProjectData]):
    """Replaces the packed dotfile entries a project hands to its sessions."""

    project_id: ProjectID
    dotfiles: bytes

    @property
    @override
    def row_class(self) -> type[ProjectRow]:
        return ProjectRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ProjectRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.project_id

    @override
    def build_values(self) -> dict[str, Any]:
        return {"dotfiles": self.dotfiles}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: ProjectRow) -> ProjectData:
        return row.to_data()


@dataclass
class ProjectSoftDeleteUpdater(GuardedDataUpdater[ProjectRow, ProjectData]):
    """Retires a project; refuses while a purge is working through it."""

    project_id: ProjectID

    @property
    @override
    def row_class(self) -> type[ProjectRow]:
        return ProjectRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ProjectRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.project_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        return [ProjectConditions.not_being_purged()]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_active": False, "status": ProjectStatus.DELETED}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: ProjectRow) -> ProjectData:
        return row.to_data()


@dataclass
class ProjectRestoreUpdater(GuardedDataUpdater[ProjectRow, ProjectData]):
    """Puts a retired project back in service; refuses while a purge is working
    through it."""

    project_id: ProjectID

    @property
    @override
    def row_class(self) -> type[ProjectRow]:
        return ProjectRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ProjectRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.project_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        return [ProjectConditions.not_being_purged()]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_active": True, "status": ProjectStatus.ACTIVE}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: ProjectRow) -> ProjectData:
        return row.to_data()
