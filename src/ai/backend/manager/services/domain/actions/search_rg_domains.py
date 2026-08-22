from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.searchers import DomainSearcher


@dataclass(frozen=True)
class SearchRGDomainsAction(SearchGlobalOpsAction[DomainRow, DomainData]):
    """Page through the domains a resource group serves.

    A resource group is not a scope domains sit under, so the association is a
    condition on the searcher rather than a scope the read is restricted to.
    """

    searcher: DomainSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DOMAIN_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_rg_domains"

    @override
    def to_searcher(self) -> DomainSearcher:
        return self.searcher
