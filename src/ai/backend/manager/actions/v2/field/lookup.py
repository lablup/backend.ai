from abc import ABC, abstractmethod

from ai.backend.common.data.entity.types import EntityIdentifier, FieldIdentifier
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.ops.backend import OpsBackendAction
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup

__all__ = (
    "FieldOwnerLookupOpsAction",
    "LookupFieldOwnerOpsAction",
)


class FieldOwnerLookupOpsAction[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](
    OpsBackendAction
):
    """A read of the entity that owns a field row, keyed by that row's id.

    Answers with an id alone, never with the owner's data: the value exists to name
    the RBAC target and the audit row of the operation that follows.
    """

    @abstractmethod
    def field_id(self) -> TFieldID:
        """Return the id of the field row whose owner is read."""
        raise NotImplementedError

    @abstractmethod
    def to_owner_lookup(self) -> FieldOwnerLookup[TFieldID, TOwnerID]:
        """Return the spec this action executes."""
        raise NotImplementedError


class LookupFieldOwnerOpsAction[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](
    BaseLookupAction, FieldOwnerLookupOpsAction[TFieldID, TOwnerID], ABC
):
    """The owner resolution seen as what it is: the field row's id is the external key.

    ``lookup_key()`` names that key, which only the domain can write: which column
    identifies a field row differs per table.
    """
