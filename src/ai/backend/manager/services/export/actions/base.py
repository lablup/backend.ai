"""Base action class for export operations."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction


@dataclass
class ExportAction(BaseAction):
    """Base action class for export operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "export"

    @abstractmethod
    @override
    def entity_id(self) -> str | None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    @override
    def operation_type(cls) -> str:
        raise NotImplementedError
