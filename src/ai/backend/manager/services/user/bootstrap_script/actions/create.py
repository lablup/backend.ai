from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.ops.base import CreateFieldOpsAction
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.creators import BootstrapScriptCreator
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow


@dataclass
class CreateBootstrapScriptAction(
    CreateFieldOpsAction[UserID, BootstrapScriptRow, BootstrapScriptData]
):
    """Add a bootstrap script to a user, answered for like an update to that user."""

    user_id: UserID
    creator: BootstrapScriptCreator

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def owner_id(self) -> UserID:
        return self.user_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_bootstrap_script"

    @override
    def to_creator(self) -> BootstrapScriptCreator:
        return self.creator
