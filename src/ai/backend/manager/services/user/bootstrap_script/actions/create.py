from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptRevisionData


@dataclass(frozen=True)
class CreateBootstrapScriptAction(BaseSingleEntityAction):
    """Add a non-default bootstrap script to a user, with its first revision."""

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
        return "create_bootstrap_script"


@dataclass(frozen=True)
class CreateBootstrapScriptActionResult:
    revision: BootstrapScriptRevisionData
