from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.queriers import BulkDomainQuerier
from ai.backend.manager.models.domain.row import DomainRow


@dataclass
class BulkGetDomainsAction(PartialBulkGetEntityOpsAction[DomainRow, DomainData]):
    """Read the domains the caller named, answering for each id.

    Wired public: a regular user holds no read on the domain entity, and the domains
    a DataLoader names are the ones the caller's own rows already point at.
    """

    ids: Sequence[DomainID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_domains"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkDomainQuerier:
        return BulkDomainQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
