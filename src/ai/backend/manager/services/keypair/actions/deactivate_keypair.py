from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.keypair.types import KeyPairData

from .base import KeyPairAction


@dataclass
class DeactivateKeyPairAction(KeyPairAction):
    """Action to deactivate a keypair."""

    access_key: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return self.access_key


@dataclass
class DeactivateKeyPairActionResult(BaseActionResult):
    """Result of deactivating a keypair."""

    keypair_data: KeyPairData

    @override
    def entity_id(self) -> str | None:
        return str(self.keypair_data.access_key)
