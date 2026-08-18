"""Update specs for the domains table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class DomainUpdater(DataUpdater[DomainRow, DomainData]):
    """Edits a domain's settings. The name is the primary key, so a rename keys on
    the old one."""

    name: str
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
    def pk_value(self) -> str:
        return self.name

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

    name: str
    dotfiles: bytes

    @property
    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def pk_value(self) -> str:
        return self.name

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
class DomainSoftDeleteUpdater(DataUpdater[DomainRow, DomainData]):
    """Retires a domain by clearing its active flag."""

    name: str

    @property
    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_active": False}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return row.to_data()


@dataclass
class DomainRestoreUpdater(DataUpdater[DomainRow, DomainData]):
    """Puts a retired domain back in service."""

    name: str

    @property
    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_active": True}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return row.to_data()
