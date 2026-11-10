from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData


@dataclass(frozen=True)
class SwitchDefaultBootstrapScriptAction(BaseSingleEntityAction):
    """Point the user's default at one of the user's live bootstrap scripts."""

    user_id: UserID
    script_id: BootstrapScriptID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

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
