from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import KeyPairAction


@dataclass
class SearchKeyPairsAction(KeyPairAction):
    """Action to search keypairs."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchKeyPairsActionResult(BaseActionResult):
    """Result of searching keypairs."""

    keypairs: list[KeyPairData]
    total_count: int

    @override
    def entity_id(self) -> str | None:
        return None
