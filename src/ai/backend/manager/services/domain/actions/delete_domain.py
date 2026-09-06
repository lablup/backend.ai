from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeleteSingleEntityGuardedOpsAction
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.updaters import DomainSoftDeleteUpdater


@dataclass(frozen=True)
class DeleteDomainAction(DeleteSingleEntityGuardedOpsAction[DomainRow, DomainData]):
    """Retire one domain."""

    updater: DomainSoftDeleteUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.domain_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_domain"

    @override
    def to_updater(self) -> DomainSoftDeleteUpdater:
        return self.updater
