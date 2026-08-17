from abc import ABC, abstractmethod

from ai.backend.common.data.entity.types import FieldIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction


class BaseSingleFieldAction(ABC):
    """Base for actions that operate on a single, already-identified field row.

    A field row is absent from the RBAC graph, so this action names no entity. It names
    the lookup that reads one instead, and that entity answers for the operation.
    """

    @classmethod
    @abstractmethod
    def operation_type(cls) -> ActionOperationType:
        """Return the operation that this action performs on the field row."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def action_name(cls) -> str:
        """Return the name recorded on audit rows: a lowercase snake_case verb phrase,
        declared rather than derived so a class rename cannot split the recorded
        history. Naming rule: services/AGENTS.md."""
        raise NotImplementedError

    @abstractmethod
    def field_id(self) -> FieldIdentifier:
        """Return the id of the field row that this action applies to."""
        raise NotImplementedError

    @abstractmethod
    def to_owner_lookup_action(self) -> LookupFieldOwnerOpsAction:
        """Return the lookup that reads the entity owning this row."""
        raise NotImplementedError
