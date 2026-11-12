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
    script: BootstrapScript


@dataclass(frozen=True)
class UpdateDefaultBootstrapScriptAction(BaseSingleEntityAction):
    """Append a revision to the user's default bootstrap script. A user with no default
    gets a new script, set as the default."""

    user_id: UserID
    script: BootstrapScript
    # Recorded on the revision. Under act-as this is the impersonated owner, not the caller.
    creator_id: UserID

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
