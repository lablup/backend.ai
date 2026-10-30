from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptRevisionData
from ai.backend.manager.models.bootstrap_script_revision.creators import (
    BootstrapScriptRevisionCreator,
)
from ai.backend.manager.services.user.bootstrap_script.actions.lookup_owner import (
    LookupBootstrapScriptOwnerAction,
)


@dataclass(frozen=True)
class AddBootstrapScriptRevisionAction(BaseSingleFieldAction[BootstrapScriptID, UserID]):
    """Append the next revision to the live bootstrap script the creator names, default
    or not. The creator's ``creator_id`` is the impersonated owner under act-as."""

    creator: BootstrapScriptRevisionCreator

    @override
    def to_owner_lookup_action(self) -> LookupBootstrapScriptOwnerAction:
        return LookupBootstrapScriptOwnerAction(script_id=self.creator.script_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "add_bootstrap_script_revision"


@dataclass(frozen=True)
class AddBootstrapScriptRevisionActionResult:
    revision: BootstrapScriptRevisionData
