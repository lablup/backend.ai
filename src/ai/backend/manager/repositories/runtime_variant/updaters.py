from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class RuntimeVariantUpdaterSpec(UpdaterSpec[RuntimeVariantRow]):
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[RuntimeVariantRow]:
        return RuntimeVariantRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        return to_update
