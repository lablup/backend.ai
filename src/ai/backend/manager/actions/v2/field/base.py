from abc import ABC, abstractmethod

from ai.backend.common.data.entity.types import EntityIdentifier, FieldIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.lookup import (
    LookupFieldOwnerOpsAction,
    LookupRuntimeFieldOwnerOpsAction,
)


class BaseSingleFieldAction[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](ABC):
    """Base for actions that operate on a single, already-identified field row.

    Every operation is answered for by an entity, and a field row carries no membership
    of its own — what it belongs to is only knowable through its owner. So this action
    names the lookup that reads that entity rather than an entity of its own.
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
    def to_owner_lookup_action(self) -> LookupFieldOwnerOpsAction[TFieldID, TOwnerID]:
        """Return the lookup that reads the entity owning this row."""
        raise NotImplementedError


class BaseRuntimeSingleFieldAction[TFieldID: FieldIdentifier](ABC):
    """Base for actions on a single field row whose owning entity is polymorphic.

    What :class:`BaseSingleFieldAction` is for a row owned by a fixed kind of entity.
    Separate because the lookup it names is the other root, executed by its own ops
    method.
    """

    @classmethod
    @abstractmethod
    def operation_type(cls) -> ActionOperationType:
        """Return the operation that this action performs on the field row."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def action_name(cls) -> str:
        """Return the name recorded on audit rows: a lowercase snake_case verb phrase."""
        raise NotImplementedError

    @abstractmethod
    def to_owner_lookup_action(self) -> LookupRuntimeFieldOwnerOpsAction[TFieldID]:
        """Return the lookup that reads the entity owning this row."""
        raise NotImplementedError
