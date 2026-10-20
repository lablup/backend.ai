from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.manager.actions.v2.field.lookup import LookupRuntimeFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.ops import RuntimePurgeFieldOpsAction
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.dotfile.purgers import DotfilePurger
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.services.dotfile.actions.lookup_owner import LookupDotfileOwnerAction


@dataclass
class PurgeDotfileAction(RuntimePurgeFieldOpsAction[DotfileID, DotfileRow, DotfileData]):
    """Remove one dotfile, named by its own id; its owner answers for it."""

    dotfile_id: DotfileID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_dotfile"

    @override
    def to_owner_lookup_action(self) -> LookupRuntimeFieldOwnerOpsAction[DotfileID]:
        return LookupDotfileOwnerAction(dotfile_id=self.dotfile_id)

    @override
    def to_purger(self) -> DotfilePurger:
        return DotfilePurger(dotfile_id=self.dotfile_id)
