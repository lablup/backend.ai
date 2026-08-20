from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.resource_preset import RESOURCE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.lookups import ResourcePresetNameLookup
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow


@dataclass(frozen=True)
class ResourcePresetNameKey(LookupKey):
    """The name a caller passes instead of the preset's id, with the resource group
    it applies within."""

    name: str
    resource_group_name: str | None = None

    @override
    def kind(self) -> str:
        return "resource_preset_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "scaling_group_name": self.resource_group_name}


@dataclass
class LookupResourcePresetAction(LookupEntityOpsAction[ResourcePresetRow, ResourcePresetData]):
    """Resolve a preset's name into the preset it names."""

    name: str
    resource_group_name: str | None = None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_resource_preset"

    @override
    def lookup_key(self) -> ResourcePresetNameKey:
        return ResourcePresetNameKey(name=self.name, resource_group_name=self.resource_group_name)

    @override
    def to_lookup(self) -> ResourcePresetNameLookup:
        return ResourcePresetNameLookup(
            name=self.name, resource_group_name=self.resource_group_name
        )
