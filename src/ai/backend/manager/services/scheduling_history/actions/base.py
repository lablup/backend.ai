from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseAction


@dataclass
class SchedulingHistoryAction(BaseAction):
    """Base action class for scheduling history operations."""

    @classmethod
    @abstractmethod
    @override
    def entity_type(cls) -> str:
        raise NotImplementedError

    @abstractmethod
    @override
    def entity_id(self) -> Optional[str]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    @override
    def operation_type(cls) -> str:
        raise NotImplementedError
