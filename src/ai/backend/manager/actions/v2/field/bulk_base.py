from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.entity.types import EntityIdentifier, FieldIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction


class BaseBulkFieldAction[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](ABC):
    """Base for actions that operate on an explicit set of field rows.

    The caller names field rows, whose membership is only knowable through their
    owners; those entities are read in one go and each is answered for.
    """

    @classmethod
    @abstractmethod
    def operation_type(cls) -> ActionOperationType:
        """Return the operation that this action performs on the rows."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def action_name(cls) -> str:
        """Return the name recorded on audit rows: a lowercase snake_case verb phrase,
        declared rather than derived so a class rename cannot split the recorded
        history. Naming rule: services/AGENTS.md."""
        raise NotImplementedError

    @abstractmethod
    def field_ids(self) -> Sequence[TFieldID]:
        """Return the ids of the field rows that this action applies to."""
        raise NotImplementedError

    @abstractmethod
    def to_owner_lookup_action(self) -> LookupBulkFieldOwnerOpsAction[TFieldID, TOwnerID]:
        """Return the lookup that reads the entity owning each row."""
        raise NotImplementedError
