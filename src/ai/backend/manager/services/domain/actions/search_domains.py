from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.searchers import DomainSearcher


@dataclass(frozen=True)
class GlobalSearchDomainsAction(SearchGlobalOpsAction[DomainRow, DomainData]):
    """Page through every domain in the installation."""

    searcher: DomainSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DOMAIN_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_domains"

    @override
    def to_searcher(self) -> DomainSearcher:
        return self.searcher
