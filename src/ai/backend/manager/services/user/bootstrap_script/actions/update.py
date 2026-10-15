from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript, BootstrapScriptID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.field.ops import UpdateFieldOpsAction
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.bootstrap_script.updaters import BootstrapScriptContentUpdater
from ai.backend.manager.services.user.bootstrap_script.actions.lookup_owner import (
    LookupBootstrapScriptOwnerAction,
)
from ai.backend.manager.types import OptionalState


@dataclass
class UpdateBootstrapScriptAction(
    UpdateFieldOpsAction[BootstrapScriptID, UserID, BootstrapScriptRow, BootstrapScriptData]
):
    """Rewrite the script of one bootstrap script."""

    script_id: BootstrapScriptID
    script: OptionalState[BootstrapScript]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_bootstrap_script_by_id"

    @override
    def to_owner_lookup_action(self) -> LookupBootstrapScriptOwnerAction:
        return LookupBootstrapScriptOwnerAction(script_id=self.script_id)

    @override
    def to_updater(self) -> BootstrapScriptContentUpdater:
        return BootstrapScriptContentUpdater(script_id=self.script_id, script=self.script)
