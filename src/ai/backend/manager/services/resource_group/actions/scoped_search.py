"""Resource-group search over the domains, projects and users they are associated with."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.scopes import ResourceGroupTarget
from ai.backend.manager.models.resource_group.searchers import ResourceGroupSearcher
from ai.backend.manager.models.scopes import OperationScope

__all__ = ("ScopedSearchResourceGroupsAction",)


@dataclass(frozen=True)
class ScopedSearchResourceGroupsAction(
    OperationScopeOpsAction[ResourceGroupRow, ResourceGroupData]
):
    """Page through the resource groups the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    targets: Sequence[ResourceGroupTarget]
    searcher: ResourceGroupSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ResourceGroupEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_resource_groups"

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets

    @override
    def to_searcher(self) -> ResourceGroupSearcher:
        return self.searcher
