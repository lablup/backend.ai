from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestorePartialBulkOpsAction
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.updaters import DomainRestoreUpdater


@dataclass(frozen=True)
class PartialBulkRestoreDomainsAction(RestorePartialBulkOpsAction[DomainRow, DomainData]):
    """Put the named retired domains back in service, answering for each one."""

    ids: Sequence[DomainID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_restore_domains"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, DomainRestoreUpdater]:
        return {domain_id: DomainRestoreUpdater(domain_id=domain_id) for domain_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[domain_id for domain_id in self.ids if domain_id in allowed])
