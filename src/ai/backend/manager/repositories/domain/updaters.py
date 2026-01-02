from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from typing_extensions import override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class DomainUpdaterSpec(UpdaterSpec[DomainRow]):
    """UpdaterSpec for domain updates."""

    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    description: TriState[str] = field(default_factory=TriState.nop)
    is_active: OptionalState[bool] = field(default_factory=OptionalState.nop)
    total_resource_slots: TriState[ResourceSlot] = field(default_factory=TriState.nop)
    allowed_vfolder_hosts: OptionalState[dict[str, list[str]]] = field(
        default_factory=OptionalState.nop
    )
    allowed_docker_registries: OptionalState[list[str]] = field(default_factory=OptionalState.nop)
    integration_id: TriState[str] = field(default_factory=TriState.nop)

    @property
    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.is_active.update_dict(to_update, "is_active")
        self.total_resource_slots.update_dict(to_update, "total_resource_slots")
        self.allowed_vfolder_hosts.update_dict(to_update, "allowed_vfolder_hosts")
        self.allowed_docker_registries.update_dict(to_update, "allowed_docker_registries")
        self.integration_id.update_dict(to_update, "integration_id")
        return to_update


@dataclass
class DomainNodeUpdaterSpec(UpdaterSpec[DomainRow]):
    """UpdaterSpec for domain node updates."""

    description: TriState[str] = field(default_factory=TriState[str].nop)
    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    total_resource_slots: TriState[ResourceSlot] = field(default_factory=TriState[ResourceSlot].nop)
    allowed_vfolder_hosts: OptionalState[dict[str, list[str]]] = field(
        default_factory=OptionalState[dict[str, list[str]]].nop
    )
    allowed_docker_registries: OptionalState[list[str]] = field(
        default_factory=OptionalState[list[str]].nop
    )
    integration_id: TriState[str] = field(default_factory=TriState[str].nop)
    dotfiles: OptionalState[bytes] = field(default_factory=OptionalState[bytes].nop)

    @property
    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.description.update_dict(to_update, "description")
        self.is_active.update_dict(to_update, "is_active")
        self.total_resource_slots.update_dict(to_update, "total_resource_slots")
        self.allowed_vfolder_hosts.update_dict(to_update, "allowed_vfolder_hosts")
        self.allowed_docker_registries.update_dict(to_update, "allowed_docker_registries")
        self.integration_id.update_dict(to_update, "integration_id")
        self.dotfiles.update_dict(to_update, "dotfiles")
        return to_update
