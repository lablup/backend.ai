from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, FieldIdentifier
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.lookup.bulk_base import (
    BaseBulkLookupAction,
    BaseBulkLookupActionResult,
    BulkLookupKeyResult,
)
from ai.backend.manager.actions.v2.ops.backend import OpsBackendAction
from ai.backend.manager.models.specs.lookup import (
    BulkFieldKeyLookup,
    FieldOwnerLookup,
    RuntimeFieldOwnerLookup,
)

__all__ = (
    "BulkFieldKeyLookupOpsAction",
    "LookupBulkFieldByKeyOpsAction",
    "BulkFieldKeyLookupOpsResult",
    "BulkFieldOwnerLookupOpsAction",
    "BulkRuntimeFieldOwnerLookupOpsAction",
    "LookupBulkRuntimeFieldOwnerOpsAction",
    "LookupBulkFieldOwnerOpsAction",
    "BulkFieldOwnerLookupOpsResult",
)


class BulkFieldOwnerLookupOpsAction[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](
    OpsBackendAction
):
    """A read of the entities owning several field rows, keyed by those rows' ids."""

    @abstractmethod
    def field_ids(self) -> Sequence[TFieldID]:
        """Return the ids of the field rows whose owners are read."""
        raise NotImplementedError

    @abstractmethod
    def to_owner_lookup(self) -> FieldOwnerLookup[TFieldID, TOwnerID]:
        """Return the spec this action executes."""
        raise NotImplementedError


class LookupBulkFieldOwnerOpsAction[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](
    BaseBulkLookupAction, BulkFieldOwnerLookupOpsAction[TFieldID, TOwnerID], ABC
):
    """The owner read of several rows, seen as what it is: their ids are the keys.

    ``lookup_keys()`` is derived, so a key and the row it stands for cannot come apart.
    """

    @abstractmethod
    def to_lookup_key(self, field_id: TFieldID) -> LookupKey:
        """Return the key that names one row, for the record."""
        raise NotImplementedError

    @override
    def lookup_keys(self) -> Sequence[LookupKey]:
        return tuple(self.to_lookup_key(field_id) for field_id in self.field_ids())


class BulkRuntimeFieldOwnerLookupOpsAction[TFieldID: FieldIdentifier](OpsBackendAction):
    """A read of the polymorphic entities owning several field rows."""

    @abstractmethod
    def field_ids(self) -> Sequence[TFieldID]:
        """Return the ids of the field rows whose owners are read."""
        raise NotImplementedError

    @abstractmethod
    def to_owner_lookup(self) -> RuntimeFieldOwnerLookup[TFieldID]:
        """Return the spec this action executes."""
        raise NotImplementedError


class LookupBulkRuntimeFieldOwnerOpsAction[TFieldID: FieldIdentifier](
    BaseBulkLookupAction, BulkRuntimeFieldOwnerLookupOpsAction[TFieldID], ABC
):
    """The polymorphic owner read of several rows, keyed by their ids."""

    @abstractmethod
    def to_lookup_key(self, field_id: TFieldID) -> LookupKey:
        """Return the key that names one row, for the record."""
        raise NotImplementedError

    @override
    def lookup_keys(self) -> Sequence[LookupKey]:
        return tuple(self.to_lookup_key(field_id) for field_id in self.field_ids())


class BulkFieldOwnerLookupOpsResult[TFieldID: FieldIdentifier](BaseBulkLookupActionResult):
    """Which entity owns each row that was found, and which rows were not.

    A row that is gone is one failed key, so the operation that follows can answer for
    it alongside the rest rather than being refused as a whole.
    """

    _owners: Mapping[TFieldID, EntityIdentifier]
    _key_results: Sequence[BulkLookupKeyResult]

    def __init__(
        self,
        owners: Mapping[TFieldID, EntityIdentifier],
        key_results: Sequence[BulkLookupKeyResult],
    ) -> None:
        self._owners = owners
        self._key_results = key_results

    @property
    def owners(self) -> Mapping[TFieldID, EntityIdentifier]:
        return self._owners

    @property
    def found_any(self) -> bool:
        return bool(self._owners)

    @override
    def key_results(self) -> Sequence[BulkLookupKeyResult]:
        return self._key_results

    @property
    def missing_status(self) -> OperationStatus:
        return OperationStatus.ERROR


class BulkFieldKeyLookupOpsAction[TKey, TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](
    OpsBackendAction
):
    """A read of the field rows several caller-facing keys name, and of their owners."""

    @abstractmethod
    def keys(self) -> Sequence[TKey]:
        """Return the keys being resolved."""
        raise NotImplementedError

    @abstractmethod
    def to_field_lookup(self) -> BulkFieldKeyLookup[TKey, TFieldID, TOwnerID]:
        """Return the spec this action executes."""
        raise NotImplementedError


class LookupBulkFieldByKeyOpsAction[TKey, TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](
    BaseBulkLookupAction, BulkFieldKeyLookupOpsAction[TKey, TFieldID, TOwnerID], ABC
):
    """The row resolution of several keys; ``lookup_keys()`` is derived from ``keys()``."""

    @abstractmethod
    def to_lookup_key(self, key: TKey) -> LookupKey:
        """Return the record's name for one key."""
        raise NotImplementedError

    @override
    def lookup_keys(self) -> Sequence[LookupKey]:
        return tuple(self.to_lookup_key(key) for key in self.keys())


class BulkFieldKeyLookupOpsResult[TKey, TFieldID: FieldIdentifier](BaseBulkLookupActionResult):
    """The field row each key names, and which keys named nothing.

    Each resolved key is recorded on the row's owner, as the single key lookup is.
    """

    _resolved: Mapping[TKey, TFieldID]
    _key_results: Sequence[BulkLookupKeyResult]

    def __init__(
        self,
        resolved: Mapping[TKey, TFieldID],
        key_results: Sequence[BulkLookupKeyResult],
    ) -> None:
        self._resolved = resolved
        self._key_results = key_results

    @property
    def resolved(self) -> Mapping[TKey, TFieldID]:
        return self._resolved

    @override
    def key_results(self) -> Sequence[BulkLookupKeyResult]:
        return self._key_results
