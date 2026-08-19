from abc import ABC, abstractmethod

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType, ActionSpec


class BaseGlobalAction(ABC):
    """Base for super-admin actions on system-wide state.

    Declares no target and no permission: a global action belongs to no RBAC scope,
    so authorization is the SUPERADMIN role gate rather than scope resolution.
    """

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        """Return the type of entity that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def operation_type(cls) -> ActionOperationType:
        """Return the operation that this action performs."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def action_name(cls) -> str:
        """Return the name recorded on audit rows: a lowercase snake_case verb phrase,
        declared rather than derived so a class rename cannot split the recorded
        history. Naming rule: services/AGENTS.md."""
        raise NotImplementedError

    @classmethod
    def spec(cls) -> ActionSpec:
        """Return the "entity:operation" spec keying reporter subscriptions and audit records."""
        return ActionSpec(
            entity_type=cls.entity_type(),
            operation_type=cls.operation_type(),
        )
