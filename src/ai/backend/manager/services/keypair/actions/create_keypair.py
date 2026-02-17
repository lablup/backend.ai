from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.keypair.types import KeyPairData

from .base import KeyPairAction


@dataclass
class CreateKeyPairAction(KeyPairAction):
    """Action to create a keypair."""

    user_id: str
    is_active: bool
    is_admin: bool
    resource_policy: str
    rate_limit: int

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return self.user_id


@dataclass
class CreateKeyPairActionResult(BaseActionResult):
    """Result of creating a keypair."""

    keypair_data: KeyPairData

    @override
    def entity_id(self) -> str | None:
        return str(self.keypair_data.access_key)
