"""Resource-group search over the domains, projects and users they are associated with."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.row import ResourceGroupRow

__all__ = ("ScopedSearchResourceGroupsAction",)


@dataclass(frozen=True)
class ScopedSearchResourceGroupsAction(ScopedSearchOpsAction[ResourceGroupRow, ResourceGroupData]):
    """Page through the resource groups the named scopes reach, combined with OR.

    Every scope is authorized and every using entity must be readable before the read
    runs, so a caller reaching for one they cannot see is refused rather than served the
    rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ResourceGroupEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_resource_groups"
