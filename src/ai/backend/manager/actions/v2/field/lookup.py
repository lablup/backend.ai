from abc import ABC, abstractmethod

from ai.backend.common.data.entity.types import EntityIdentifier, FieldIdentifier
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.ops.backend import OpsBackendAction
from ai.backend.manager.models.specs.lookup import (
    FieldKeyLookup,
    FieldOwnerKeyLookup,
    FieldOwnerLookup,
    RuntimeFieldOwnerLookup,
)

__all__ = (
    "FieldKeyLookupOpsAction",
    "FieldOwnerKeyLookupOpsAction",
    "FieldOwnerLookupOpsAction",
    "LookupRuntimeFieldOwnerOpsAction",
    "RuntimeFieldOwnerLookupOpsAction",
    "LookupFieldByKeyOpsAction",
    "LookupFieldOwnerByKeyOpsAction",
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


class RuntimeFieldOwnerLookupOpsAction[TFieldID: FieldIdentifier](OpsBackendAction):
    """A read of the polymorphic entity that owns a field row, keyed by that row's id.

    The counterpart of :class:`FieldOwnerLookupOpsAction` for the other lookup root; the
    two stay apart down to the ops method each is executed by.
    """

    @abstractmethod
    def field_id(self) -> TFieldID:
        """Return the id of the field row whose owner is read."""
        raise NotImplementedError

    @abstractmethod
    def to_owner_lookup(self) -> RuntimeFieldOwnerLookup[TFieldID]:
        """Return the spec this action executes."""
        raise NotImplementedError


class LookupRuntimeFieldOwnerOpsAction[TFieldID: FieldIdentifier](
    BaseLookupAction, RuntimeFieldOwnerLookupOpsAction[TFieldID], ABC
):
    """The polymorphic owner resolution seen as what it is: the field row's id is the
    external key."""


class FieldOwnerKeyLookupOpsAction[TOwnerID: EntityIdentifier](OpsBackendAction):
    """A read of the entity that owns a field row, keyed by the row's caller-facing key.

    The other direction of :class:`FieldOwnerLookupOpsAction`: a request that names a
    field row by an access key or a name reaches its owner this way, and the operation
    that follows is checked against that owner.
    """

    @abstractmethod
    def to_owner_lookup(self) -> FieldOwnerKeyLookup[TOwnerID]:
        """Return the spec this action executes."""
        raise NotImplementedError


class LookupFieldOwnerByKeyOpsAction[TOwnerID: EntityIdentifier](
    BaseLookupAction, FieldOwnerKeyLookupOpsAction[TOwnerID], ABC
):
    """The owner resolution seen as what it is: the field row's key is the external key."""


class FieldKeyLookupOpsAction[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](
    OpsBackendAction
):
    """A read of the field row a caller-facing key names, and of the entity owning it.

    What turns a request carrying an access key or a name into the row id every
    operation naming that row takes. The owner comes back with it because a field row is
    not an entity, so the run has to be recorded against something.
    """

    @abstractmethod
    def to_field_lookup(self) -> FieldKeyLookup[TFieldID, TOwnerID]:
        """Return the spec this action executes."""
        raise NotImplementedError


class LookupFieldByKeyOpsAction[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](
    BaseLookupAction, FieldKeyLookupOpsAction[TFieldID, TOwnerID], ABC
):
    """The row resolution seen as what it is: the field row's key is the external key."""
