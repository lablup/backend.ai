from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.resource_allocation.types import ScopeUsageData


@dataclass(frozen=True)
class GetKeypairUsageAction(BaseSingleEntityAction):
    """Read what one keypair is currently using, answered for by its owner."""

    user_id: UserID
    access_key: AccessKey
    resource_policy: Mapping[str, Any]

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
