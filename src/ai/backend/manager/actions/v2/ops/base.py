from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.manager.models.base import Base
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.base.creator import DataCreator
from ai.backend.manager.repositories.base.purger import DataBatchPurger, DataPurger
from ai.backend.manager.repositories.base.querier import DataFinder, DataQuerier
from ai.backend.manager.repositories.base.searcher import Searcher
from ai.backend.manager.repositories.base.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.repositories.base.upserter import DataUpserter

__all__ = (
    "OpsBackendAction",
    "GetOpsAction",
    "LookupOpsAction",
    "CreateOpsAction",
    "BulkCreateOpsAction",
    "BatchUpdateOpsAction",
    "BatchPurgeOpsAction",
    "UpdateOpsAction",
    "UpsertOpsAction",
    "PurgeOpsAction",
    "SearchOpsAction",
)


class OpsBackendAction(ABC):
    """Executed directly against repository ops; no service method needed.

    Mixed in alongside the shape axis (``BaseScopeAction``, ``BaseSingleEntityAction``,
    ...), which stays responsible for RBAC and audit. This axis only says how the action
    is backed: it carries the repository spec instead of a hand-written service method.
    Promote the action to a real service method as soon as it grows a branch.

    Not a new contract: actions across the codebase already hold a ``Creator`` /
    ``Updater`` / ``Purger`` / ``Upserter`` as a field. This names that contract so a
    generic service can execute it.

    There is deliberately no ``delete`` variant. A soft delete is a status transition,
    so it carries a ``DataUpdater`` like any other write and runs through the update
    service; ``repositories/base/`` has no deleter spec because there is no delete
    operation to generalize.
    """


class GetOpsAction[TRow: Base, TData](OpsBackendAction):
    """A read by id.

    Carries a spec rather than leaning on ``BaseSingleEntityAction.entity_id()``: the id
    alone cannot say which table to read or how the row becomes data, and putting either
    at the wiring site would spread the domain across two places.
    """

    @abstractmethod
    def to_querier(self) -> DataQuerier[TRow, TData]:
        """Return the read spec this action executes."""
        raise NotImplementedError


class LookupOpsAction[TRow: Base, TData](OpsBackendAction):
    """A read by a key that is not the entity's id.

    The lookup shape's whole point is producing an id, so the spec has to say which
    columns the key is and how the row becomes data; there is nothing on the action for
    it to lean on the way the single-entity shape leans on ``entity_id()``.
    """

    @abstractmethod
    def to_finder(self) -> DataFinder[TRow, TData]:
        """Return the key-resolution spec this action executes."""
        raise NotImplementedError


class CreateOpsAction[TRow: Base, TData](OpsBackendAction):
    @abstractmethod
    def to_creator(self) -> DataCreator[TRow, TData]:
        """Return the insert spec this action executes."""
        raise NotImplementedError


class BulkCreateOpsAction[TRow: Base, TData](OpsBackendAction):
    """A create of several rows at once, atomically."""

    @abstractmethod
    def to_creators(self) -> Sequence[DataCreator[TRow, TData]]:
        """Return one insert spec per row this action creates."""
        raise NotImplementedError


class BatchUpdateOpsAction[TRow: Base, TData](OpsBackendAction):
    """An update of every row matching a condition, rather than of one named row."""

    @abstractmethod
    def to_batch_updater(self) -> DataBatchUpdater[TRow, TData]:
        """Return the batch update spec this action executes."""
        raise NotImplementedError


class BatchPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """A hard delete of every row matching a condition."""

    @abstractmethod
    def to_batch_purger(self) -> DataBatchPurger[TRow, TData]:
        """Return the batch delete spec this action executes."""
        raise NotImplementedError


class UpdateOpsAction[TRow: Base, TData](OpsBackendAction):
    @abstractmethod
    def to_updater(self) -> DataUpdater[TRow, TData]:
        """Return the update spec this action executes.

        A soft delete uses this too: which column marks a row deleted is domain
        knowledge, so a delete action declares ``operation_type() == DELETE`` and hands
        over the updater that performs the transition.
        """
        raise NotImplementedError


class UpsertOpsAction[TRow: Base, TData](OpsBackendAction):
    """A create-or-update, the one write outside the standard six.

    ``ActionOperationType`` has no ``upsert``, so the action still declares itself as a
    create or an update for RBAC and the audit trail; only the write underneath differs.
    """

    @abstractmethod
    def to_upserter(self) -> DataUpserter[TRow, TData]:
        """Return the upsert spec this action executes."""
        raise NotImplementedError


class PurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    @abstractmethod
    def to_purger(self) -> DataPurger[TRow, TData]:
        """Return the hard-delete spec this action executes."""
        raise NotImplementedError


class SearchOpsAction[TRow: Base, TData](OpsBackendAction):
    """A list read backed by a :class:`Searcher`, not a ``BatchQuerier``.

    ``Searcher`` carries the SELECT, the row conversion and the query options in one
    object, so the ORM row never leaves the repository layer and the generic service
    has nothing left to convert.
    """

    @abstractmethod
    def to_searcher(self) -> Searcher[TRow, TData]:
        """Return the search spec this action executes."""
        raise NotImplementedError

    @abstractmethod
    def search_scopes(self) -> Sequence[SearchScope]:
        """Return the scopes the search is restricted to, empty for a global search.

        These are the models-layer query scopes, distinct from the RBAC
        ``scope_targets()`` the shape axis declares. Whether an empty sequence is
        allowed at all is the domain repository's call, since only it knows if the
        path carries the authority for an unscoped scan.
        """
        raise NotImplementedError
