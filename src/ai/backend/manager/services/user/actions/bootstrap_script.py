"""Actions for a user's default bootstrap script."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass(frozen=True)
class GetDefaultBootstrapScriptAction(BaseSingleEntityAction):
    """Read the user's default bootstrap script."""

    user_id: UserID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_bootstrap_script"


@dataclass(frozen=True)
class GetDefaultBootstrapScriptActionResult:
    script: str


@dataclass(frozen=True)
class UpdateDefaultBootstrapScriptAction(BaseSingleEntityAction):
    """Rewrite the script of the user's default bootstrap script."""

    user_id: UserID
    script: BootstrapScript

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
        return "update_bootstrap_script"


@dataclass(frozen=True)
class UpdateDefaultBootstrapScriptActionResult:
    pass
