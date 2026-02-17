from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import KeyPairAction


@dataclass
class DeleteKeyPairAction(KeyPairAction):
    """Action to delete keypairs."""

    access_keys: list[str]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def entity_id(self) -> str | None:
        return ",".join(self.access_keys)


@dataclass
class DeleteKeyPairActionResult(BaseActionResult):
    """Result of deleting keypairs."""

    deleted: bool

    @override
    def entity_id(self) -> str | None:
        return None
