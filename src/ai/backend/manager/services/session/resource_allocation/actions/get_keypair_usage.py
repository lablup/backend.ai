from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.resource_allocation.types import ScopeUsageData


@dataclass(frozen=True)
class GetKeypairUsageAction(BaseSingleEntityAction):
    """Read what a user's default keypair is currently using."""

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
        return "get_keypair_usage"


@dataclass(frozen=True)
class GetKeypairUsageActionResult:
    usage: ScopeUsageData
