from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.services.user.bootstrap_script.actions.lookup_owner import (
    LookupBootstrapScriptOwnerAction,
)


@dataclass(frozen=True)
class SwitchDefaultBootstrapScriptAction(BaseSingleFieldAction[BootstrapScriptID, UserID]):
    """Move the default mark among a user's bootstrap scripts onto one script."""

    script_id: BootstrapScriptID

    @override
    def to_owner_lookup_action(self) -> LookupBootstrapScriptOwnerAction:
        return LookupBootstrapScriptOwnerAction(script_id=self.script_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "switch_default_bootstrap_script"


@dataclass(frozen=True)
class SwitchDefaultBootstrapScriptActionResult:
    script: BootstrapScriptData
