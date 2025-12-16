from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from typing_extensions import override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class GroupUpdaterSpec(UpdaterSpec[GroupRow]):
    """UpdaterSpec for group updates."""

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
    integration_id: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    resource_policy: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    container_registry: TriState[dict[str, str]] = field(
        default_factory=TriState[dict[str, str]].nop
    )

    @property
    @override
    def row_class(self) -> type[GroupRow]:
        return GroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.is_active.update_dict(to_update, "is_active")
        self.domain_name.update_dict(to_update, "domain_name")
        self.total_resource_slots.update_dict(to_update, "total_resource_slots")
        self.allowed_vfolder_hosts.update_dict(to_update, "allowed_vfolder_hosts")
        self.integration_id.update_dict(to_update, "integration_id")
        self.resource_policy.update_dict(to_update, "resource_policy")
        self.container_registry.update_dict(to_update, "container_registry")
        return to_update
