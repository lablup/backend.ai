from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.field.ops import PurgeFieldOpsAction
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.purgers import NonDefaultBootstrapScriptPurger
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.services.user.bootstrap_script.actions.lookup_owner import (
    LookupBootstrapScriptOwnerAction,
)


@dataclass
class PurgeBootstrapScriptAction(
    PurgeFieldOpsAction[BootstrapScriptID, UserID, BootstrapScriptRow, BootstrapScriptData]
):
    """Remove one bootstrap script. The default one is refused until the default moves."""

    script_id: BootstrapScriptID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_bootstrap_script"

    @override
    def to_owner_lookup_action(self) -> LookupBootstrapScriptOwnerAction:
        return LookupBootstrapScriptOwnerAction(script_id=self.script_id)

    @override
    def to_purger(self) -> NonDefaultBootstrapScriptPurger:
        return NonDefaultBootstrapScriptPurger(script_id=self.script_id)
