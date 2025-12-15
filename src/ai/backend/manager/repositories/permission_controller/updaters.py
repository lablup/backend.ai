from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from typing_extensions import override

from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState

from ...data.permission.status import RoleStatus
from ...data.permission.types import RoleSource


@dataclass
class RoleUpdaterSpec(UpdaterSpec[RoleRow]):
    """UpdaterSpec for role updates."""

    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    source: OptionalState[RoleSource] = field(default_factory=OptionalState.nop)
    status: OptionalState[RoleStatus] = field(default_factory=OptionalState.nop)
    description: TriState[str] = field(default_factory=TriState.nop)

    @property
    @override
    def row_class(self) -> type[RoleRow]:
        return RoleRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.source.update_dict(to_update, "source")
        self.status.update_dict(to_update, "status")
        self.description.update_dict(to_update, "description")
        return to_update
