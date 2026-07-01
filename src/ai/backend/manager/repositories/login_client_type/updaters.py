"""UpdaterSpec implementations for login_client_type repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class LoginClientTypeUpdaterSpec(UpdaterSpec[LoginClientTypeRow]):
    """UpdaterSpec for login client type updates."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[LoginClientTypeRow]:
        return LoginClientTypeRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        return to_update
