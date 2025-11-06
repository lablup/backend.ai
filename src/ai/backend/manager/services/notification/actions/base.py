from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseAction


@dataclass
class NotificationAction(BaseAction):
    """Base action class for notification operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "notification"

    @abstractmethod
    @override
    def entity_id(self) -> Optional[str]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    @override
    def operation_type(cls) -> str:
        raise NotImplementedError
