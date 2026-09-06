from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestoreSingleEntityGuardedOpsAction
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.updaters import DomainRestoreUpdater


@dataclass(frozen=True)
class RestoreDomainAction(RestoreSingleEntityGuardedOpsAction[DomainRow, DomainData]):
    """Put one retired domain back in service."""

    updater: DomainRestoreUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.domain_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_domain"

    @override
    def to_updater(self) -> DomainRestoreUpdater:
        return self.updater
