from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.model_card.types import MinResourceSpec
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ModelCardUpdaterSpec(UpdaterSpec[ModelCardRow]):
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    author: TriState[str] = field(default_factory=TriState[str].nop)
    title: TriState[str] = field(default_factory=TriState[str].nop)
    model_version: TriState[str] = field(default_factory=TriState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    task: TriState[str] = field(default_factory=TriState[str].nop)
    category: TriState[str] = field(default_factory=TriState[str].nop)
    architecture: TriState[str] = field(default_factory=TriState[str].nop)
    framework: OptionalState[list[str]] = field(default_factory=OptionalState[list[str]].nop)
    label: OptionalState[list[str]] = field(default_factory=OptionalState[list[str]].nop)
    license: TriState[str] = field(default_factory=TriState[str].nop)
    min_resource: TriState[MinResourceSpec] = field(default_factory=TriState[MinResourceSpec].nop)
    readme: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[ModelCardRow]:
        return ModelCardRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.author.update_dict(to_update, "author")
        self.title.update_dict(to_update, "title")
        self.model_version.update_dict(to_update, "model_version")
        self.description.update_dict(to_update, "description")
        self.task.update_dict(to_update, "task")
        self.category.update_dict(to_update, "category")
        self.architecture.update_dict(to_update, "architecture")
        self.framework.update_dict(to_update, "framework")
        self.label.update_dict(to_update, "label")
        self.license.update_dict(to_update, "license")
        self.min_resource.update_dict(to_update, "min_resource")
        self.readme.update_dict(to_update, "readme")
        return to_update
