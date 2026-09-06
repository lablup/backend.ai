"""Update specs for the domains table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.domain.types import DomainData, DomainStatus
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.conditions import DomainConditions
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater, GuardedDataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class DomainUpdater(GuardedDataUpdater[DomainRow, DomainData]):
    """Edits a domain's settings; refuses while a purge is working through it."""

    domain_id: DomainID
    new_name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    total_resource_slots: TriState[ResourceSlot] = field(default_factory=TriState[ResourceSlot].nop)
    allowed_vfolder_hosts: OptionalState[dict[str, list[str]]] = field(
        default_factory=OptionalState[dict[str, list[str]]].nop
    )
    allowed_docker_registries: OptionalState[list[str]] = field(
        default_factory=OptionalState[list[str]].nop
    )
    integration_name: TriState[str] = field(default_factory=TriState[str].nop)
    dotfiles: OptionalState[bytes] = field(default_factory=OptionalState[bytes].nop)

    @property
    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return DomainRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.domain_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        return [DomainConditions.not_being_purged()]

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.new_name.update_dict(to_update, "name")
        self.dotfiles.update_dict(to_update, "dotfiles")
        self.description.update_dict(to_update, "description")
        self.is_active.update_dict(to_update, "is_active")
        self.total_resource_slots.update_dict(to_update, "total_resource_slots")
        self.allowed_vfolder_hosts.update_dict(to_update, "allowed_vfolder_hosts")
        self.allowed_docker_registries.update_dict(to_update, "allowed_docker_registries")
        # Field is named integration_name above model layer; DB column remains integration_id.
        self.integration_name.update_dict(to_update, "integration_id")
        return to_update

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return row.to_data()


@dataclass
class DomainDotfilesUpdater(DataUpdater[DomainRow, DomainData]):
    """Replaces the packed dotfile entries a domain hands to its sessions."""

    domain_id: DomainID
    dotfiles: bytes

    @property
    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return DomainRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.domain_id

    @override
    def build_values(self) -> dict[str, Any]:
        return {"dotfiles": self.dotfiles}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return row.to_data()


@dataclass
class DomainSoftDeleteUpdater(GuardedDataUpdater[DomainRow, DomainData]):
    """Retires a domain; refuses while a purge is working through it."""

    domain_id: DomainID

    @property
    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return DomainRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.domain_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        return [DomainConditions.not_being_purged()]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_active": False, "status": DomainStatus.DELETED}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return row.to_data()


@dataclass
class DomainRestoreUpdater(GuardedDataUpdater[DomainRow, DomainData]):
    """Puts a retired domain back in service; refuses while a purge is working
    through it."""

    domain_id: DomainID

    @property
    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return DomainRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.domain_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        return [DomainConditions.not_being_purged()]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_active": True, "status": DomainStatus.ACTIVE}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return row.to_data()
