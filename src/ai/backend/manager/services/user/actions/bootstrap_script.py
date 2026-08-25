"""Actions for the bootstrap script a keypair carries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass(frozen=True)
class GetBootstrapScriptAction(BaseSingleEntityAction):
    """Read the bootstrap script a keypair carries."""

    user_id: UserID
    access_key: AccessKey

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
class GetBootstrapScriptActionResult:
    script: str


@dataclass(frozen=True)
class UpdateBootstrapScriptAction(BaseSingleEntityAction):
    """Rewrite the bootstrap script a keypair carries."""

    user_id: UserID
    access_key: AccessKey
    script: str

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
class UpdateBootstrapScriptActionResult:
    pass
