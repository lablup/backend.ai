from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.config import ModelDefinitionDraft
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class RuntimeVariantUpdaterSpec(UpdaterSpec[RuntimeVariantRow]):
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    reads_vfolder_config_files: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    default_model_definition: OptionalState[ModelDefinitionDraft] = field(
        default_factory=OptionalState[ModelDefinitionDraft].nop
    )

    @property
    @override
    def row_class(self) -> type[RuntimeVariantRow]:
        return RuntimeVariantRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.reads_vfolder_config_files.update_dict(to_update, "reads_vfolder_config_files")
        self.default_model_definition.update_dict(to_update, "default_model_definition")
        return to_update
