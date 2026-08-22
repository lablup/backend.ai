from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.queriers import DomainQuerier
from ai.backend.manager.models.domain.row import DomainRow


@dataclass(frozen=True)
class GetDomainAction(GetSingleEntityOpsAction[DomainRow, DomainData]):
    """Read one domain by its id."""

    domain_id: DomainID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_domain"

    @override
    def to_querier(self) -> DomainQuerier:
        return DomainQuerier(domain_id=self.domain_id)
