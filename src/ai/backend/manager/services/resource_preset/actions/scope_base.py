from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.models.resource_preset.scopes import ResourcePresetTarget


@dataclass
class ResourcePresetScopeAction(BaseScopeAction):
    """Base for the preset reads answered within the scopes the caller names.

    A preset bound to no resource group is read at public, one bound to a group at that
    group, so naming a group the caller holds no permission at refuses the read.
    """

    targets: Sequence[ResourcePresetTarget]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ResourcePresetEntityType()

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]
