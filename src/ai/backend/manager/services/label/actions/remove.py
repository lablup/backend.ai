from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.label import LabelID
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.ops import PurgeFieldOpsAction
from ai.backend.manager.data.label.types import LabelData
from ai.backend.manager.models.label.purgers import LabelPurger
from ai.backend.manager.models.label.row import LabelRow
from ai.backend.manager.services.label.actions.lookup_owner import LookupLabelOwnerAction


@dataclass
class RemoveLabelAction(PurgeFieldOpsAction[LabelID, RuntimeEntityID, LabelRow, LabelData]):
    """Take one label off, named by its own id.

    Which entity answers for it is what the owner lookup reads first; the label row
    itself carries the type beside the id, so the answer is a whole identifier.
    """

    label_id: LabelID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "remove_label"

    @override
    def to_owner_lookup_action(self) -> LookupFieldOwnerOpsAction[LabelID, RuntimeEntityID]:
        return LookupLabelOwnerAction(label_id=self.label_id)

    @override
    def to_purger(self) -> LabelPurger:
        return LabelPurger(label_id=self.label_id)
