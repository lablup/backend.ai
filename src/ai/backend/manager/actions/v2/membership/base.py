from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType

__all__ = ("BaseMembershipAction",)


class BaseMembershipAction(ABC):
    """Base for actions that move one entity into scopes or out of them.

    The entity and every scope named have to permit the operation.
    """

    @classmethod
    @abstractmethod
    def operation_type(cls) -> ActionOperationType:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def action_name(cls) -> str:
        """The name recorded on audit rows. Naming rule: services/AGENTS.md."""
        raise NotImplementedError

    @abstractmethod
    def entity(self) -> EntityIdentifier:
        """The entity that enters or leaves the scopes."""
        raise NotImplementedError

    @abstractmethod
    def scopes(self) -> Sequence[EntityIdentifier]:
        """The scopes the entity enters or leaves."""
        raise NotImplementedError
