from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.manager.actions.v2.field.lookup import LookupRuntimeFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.ops import RuntimeUpdateFieldOpsAction
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.dotfile.updaters import DotfileUpdater
from ai.backend.manager.services.dotfile.actions.lookup_owner import LookupDotfileOwnerAction


@dataclass
class UpdateDotfileAction(RuntimeUpdateFieldOpsAction[DotfileID, DotfileRow, DotfileData]):
    """Rewrite one dotfile, named by its own id; its owner answers for it."""

    updater: DotfileUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_dotfile"

    @override
    def to_owner_lookup_action(self) -> LookupRuntimeFieldOwnerOpsAction[DotfileID]:
        return LookupDotfileOwnerAction(dotfile_id=self.updater.dotfile_id)

    @override
    def to_updater(self) -> DotfileUpdater:
        return self.updater
