"""Domain search over the resource groups they are associated with."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.scopes import ResourceGroupDomainTarget
from ai.backend.manager.models.domain.searchers import DomainSearcher
from ai.backend.manager.models.scopes import OperationScope

__all__ = ("ScopedSearchDomainsAction",)


@dataclass(frozen=True)
class ScopedSearchDomainsAction(OperationScopeOpsAction[DomainRow, DomainData]):
    """Page through the domains the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    targets: Sequence[ResourceGroupDomainTarget]
    searcher: DomainSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DomainEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_domains"

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets

    @override
    def to_searcher(self) -> DomainSearcher:
        return self.searcher
