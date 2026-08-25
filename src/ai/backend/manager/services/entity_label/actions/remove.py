from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_label import EntityLabelID
from ai.backend.manager.actions.v2.field.lookup import LookupRuntimeFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.ops import RuntimePurgeFieldOpsAction
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.entity_label.purgers import EntityLabelPurger
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.services.entity_label.actions.lookup_owner import (
    LookupEntityLabelOwnerAction,
)


@dataclass
class RemoveEntityLabelAction(
    RuntimePurgeFieldOpsAction[EntityLabelID, EntityLabelRow, EntityLabelData]
):
    """Take one label off, named by its own id.

    Which entity answers for it is what the owner lookup reads first; the label row
    itself carries the type beside the id, so the answer is a whole identifier.
    """

    label_id: EntityLabelID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "remove_entity_label"

    @override
    def to_owner_lookup_action(self) -> LookupRuntimeFieldOwnerOpsAction[EntityLabelID]:
        return LookupEntityLabelOwnerAction(label_id=self.label_id)

    @override
    def to_purger(self) -> EntityLabelPurger:
        return EntityLabelPurger(label_id=self.label_id)
