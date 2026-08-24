from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityGuardedOpsAction
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.updaters import DomainUpdater


@dataclass(frozen=True)
class UpdateDomainAction(UpdateSingleEntityGuardedOpsAction[DomainRow, DomainData]):
    """Edit one domain's settings.

    Takes both axes: ``domain_id`` is what the operation is answered for, while the
    updater keys on the name, which is the table's primary key.
    """

    updater: DomainUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.domain_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_domain"

    @override
    def to_updater(self) -> DomainUpdater:
        return self.updater
