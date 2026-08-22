from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass(frozen=True)
class ResolveKeypairContextAction(BaseSingleEntityAction):
    """Read the access key and resource policy a user's default keypair carries."""

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
        return "resolve_keypair_context"


@dataclass(frozen=True)
class ResolveKeypairContextActionResult:
    access_key: AccessKey
    resource_policy: Mapping[str, Any]
