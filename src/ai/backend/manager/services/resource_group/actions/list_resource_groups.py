from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.row import ResourceGroupRow


@dataclass(frozen=True)
class SearchResourceGroupsAction(GlobalSearcherOpsAction[ResourceGroupRow, ResourceGroupData]):
    """Page through every resource group in the installation."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ResourceGroupEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_resource_groups"
