from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.repositories.base.updater import Updater

from .base import KeyPairAction

if TYPE_CHECKING:
    from ai.backend.manager.models.keypair import KeyPairRow


@dataclass
class UpdateKeyPairAction(KeyPairAction):
    """Action to update a keypair."""

    updater: Updater[KeyPairRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)


@dataclass
class UpdateKeyPairActionResult(BaseActionResult):
    """Result of updating a keypair."""

    keypair_data: KeyPairData

    @override
    def entity_id(self) -> str | None:
        return str(self.keypair_data.access_key)
