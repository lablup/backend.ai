from abc import abstractmethod
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.types import ActionOperationType


@dataclass
class KeyPairAction(BaseAction):
    """Base action class for keypair operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.AUTH_SSH_KEYPAIR

    @abstractmethod
    @override
    def entity_id(self) -> str | None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        raise NotImplementedError
