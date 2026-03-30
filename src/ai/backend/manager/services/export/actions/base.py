"""Base action class for export operations."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.types import ActionOperationType


@dataclass
class ExportAction(BaseAction):
    """Base action class for export operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.EXPORT

    @abstractmethod
    @override
    def entity_id(self) -> str | None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        raise NotImplementedError
