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
    FieldOwnerLookup,
    RuntimeFieldOwnerLookup,
)

__all__ = (
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
