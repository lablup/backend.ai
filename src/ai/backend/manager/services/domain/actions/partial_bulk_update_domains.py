from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.updaters import DomainUpdater


@dataclass(frozen=True)
class PartialBulkUpdateDomainsAction(UpdatePartialBulkOpsAction[DomainRow, DomainData]):
    """Edit the named domains' settings, answering for each one."""

    updaters: Sequence[DomainUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_domains"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.domain_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, DomainUpdater]:
        return {updater.domain_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.domain_id in allowed]
        )
