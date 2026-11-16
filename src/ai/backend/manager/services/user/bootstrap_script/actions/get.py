from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.manager.actions.v2.field.ops import RuntimeGetFieldOpsAction
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.queriers import BootstrapScriptQuerier
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.services.user.bootstrap_script.actions.lookup_owner import (
    LookupBootstrapScriptOwnerAction,
)


@dataclass
class GetBootstrapScriptAction(
    RuntimeGetFieldOpsAction[BootstrapScriptID, BootstrapScriptRow, BootstrapScriptData]
):
    """Read one bootstrap script, authorized against the entity it is set on."""

    script_id: BootstrapScriptID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_bootstrap_script_by_id"

    @override
    def to_owner_lookup_action(self) -> LookupBootstrapScriptOwnerAction:
        return LookupBootstrapScriptOwnerAction(script_id=self.script_id)

    @override
    def to_querier(self) -> BootstrapScriptQuerier:
        return BootstrapScriptQuerier(script_id=self.script_id)
