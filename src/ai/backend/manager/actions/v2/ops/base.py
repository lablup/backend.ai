from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import override

from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
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
    "BulkUpdateOpsAction",
    "BulkPurgeOpsAction",
    "BatchUpdateOpsAction",
    "BatchPurgeOpsAction",
    "UpdateOpsAction",
    "UpsertOpsAction",
    "PurgeOpsAction",
    "SearchOpsAction",
    "GlobalSearchOpsAction",
    "GetSingleEntityOpsAction",
    "UpdateSingleEntityOpsAction",
    "DeleteSingleEntityOpsAction",
    "UpsertSingleEntityOpsAction",
    "PurgeSingleEntityOpsAction",
    "UpdateBulkOpsAction",
    "DeleteBulkOpsAction",
    "PurgeBulkOpsAction",
    "CreateScopeOpsAction",
    "BulkCreateScopeOpsAction",
    "BatchUpdateScopeOpsAction",
    "BatchPurgeScopeOpsAction",
    "SearchScopeOpsAction",
    "CreateGlobalOpsAction",
    "UpdateGlobalOpsAction",
    "PurgeGlobalOpsAction",
    "SearchGlobalOpsAction",
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


class BulkUpdateOpsAction[TRow: Base, TData](OpsBackendAction):
    """An update of entities the caller named, each answered for separately.

    A mapping rather than a list: the bulk shape reports per entity, and pairing the
    specs to ``BaseBulkAction.entity_ids()`` by position would be an invariant nothing
    enforces — one that fails by attributing an error to the wrong entity. A domain
    action returns ``tuple(self.to_updaters())`` for its ids and the two cannot drift.

    Soft deletes use this too, as the single-entity path does.
    """

    @abstractmethod
    def to_updaters(self) -> Mapping[EntityID, DataUpdater[TRow, TData]]:
        """Return the update spec for each entity this action names."""
        raise NotImplementedError


class BulkPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """A hard delete of entities the caller named, each answered for separately."""

    @abstractmethod
    def to_purgers(self) -> Mapping[EntityID, DataPurger[TRow, TData]]:
        """Return the delete spec for each entity this action names."""
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
    """A create-or-update."""

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
        """Return the scopes the search is restricted to. Never empty.

        These are the models-layer query scopes, distinct from the RBAC
        ``scope_targets()`` the shape axis declares. An empty sequence is rejected
        rather than widened into an unscoped scan: a caller whose RBAC resolution came
        back empty would otherwise be handed every row. Searching without a scope is
        :class:`GlobalSearchOpsAction`, which says so in the shape it declares.
        """
        raise NotImplementedError


class GlobalSearchOpsAction[TRow: Base, TData](OpsBackendAction):
    """A list read across an entire table, with no scope filter.

    Mixed in alongside ``BaseGlobalAction``, whose SUPERADMIN gate is what makes an
    unscoped scan answerable for. Kept apart from :class:`SearchOpsAction` rather than
    signalled by an empty scope list, so the authority a query needs is visible in the
    action's shape instead of in the value of one of its fields.
    """

    @abstractmethod
    def to_searcher(self) -> Searcher[TRow, TData]:
        """Return the search spec this action executes."""
        raise NotImplementedError


class GetSingleEntityOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, GetOpsAction[TRow, TData], ABC
):
    """A single-entity read, backed by ops.

    The two axes named together, because the registry has to bound them together: a
    processor built by ``single_get_ops`` takes an action that is single-entity shaped
    *and* carries a querier, and Python has no intersection type to say both.
    """

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


class UpdateSingleEntityOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, UpdateOpsAction[TRow, TData], ABC
):
    """A single-entity write, backed by ops. A soft delete carries this too."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


class UpsertSingleEntityOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, UpsertOpsAction[TRow, TData], ABC
):
    """A single-entity create-or-update, backed by ops."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPSERT


class PurgeSingleEntityOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, PurgeOpsAction[TRow, TData], ABC
):
    """A single-entity hard delete, backed by ops."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class UpdateBulkOpsAction[TRow: Base, TData](BaseBulkAction, BulkUpdateOpsAction[TRow, TData], ABC):
    """A write over the entities the caller named. A bulk soft delete carries this too."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


class PurgeBulkOpsAction[TRow: Base, TData](BaseBulkAction, BulkPurgeOpsAction[TRow, TData], ABC):
    """A hard delete over the entities the caller named."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class CreateScopeOpsAction[TRow: Base, TData](BaseScopeAction, CreateOpsAction[TRow, TData], ABC):
    """An insert of one row into the scope the action names."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class BulkCreateScopeOpsAction[TRow: Base, TData](
    BaseScopeAction, BulkCreateOpsAction[TRow, TData], ABC
):
    """An atomic insert of several rows into the scope the action names."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class BatchUpdateScopeOpsAction[TRow: Base, TData](
    BaseScopeAction, BatchUpdateOpsAction[TRow, TData], ABC
):
    """A write over every row matching the action's condition."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


class BatchPurgeScopeOpsAction[TRow: Base, TData](
    BaseScopeAction, BatchPurgeOpsAction[TRow, TData], ABC
):
    """A hard delete of every row matching the action's condition."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class SearchScopeOpsAction[TRow: Base, TData](BaseScopeAction, SearchOpsAction[TRow, TData], ABC):
    """A page read from within the scopes the action names."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


class CreateGlobalOpsAction[TRow: Base, TData](BaseGlobalAction, CreateOpsAction[TRow, TData], ABC):
    """An insert of one row of system-wide state."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class UpdateGlobalOpsAction[TRow: Base, TData](BaseGlobalAction, UpdateOpsAction[TRow, TData], ABC):
    """A write to one row of system-wide state, named by a key that is not an ``EntityID``.

    Global rather than single-entity because the row it names belongs to no RBAC scope:
    the SUPERADMIN gate is what answers for the write, and the catalogs this shape
    serves are keyed by a name that the caller passes as-is.
    """

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


class PurgeGlobalOpsAction[TRow: Base, TData](BaseGlobalAction, PurgeOpsAction[TRow, TData], ABC):
    """A hard delete of one row of system-wide state."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class SearchGlobalOpsAction[TRow: Base, TData](
    BaseGlobalAction, GlobalSearchOpsAction[TRow, TData], ABC
):
    """A page read across the whole table."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


class DeleteSingleEntityOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, UpdateOpsAction[TRow, TData], ABC
):
    """A single-entity soft delete: a status transition, so it carries an updater."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


class DeleteBulkOpsAction[TRow: Base, TData](BaseBulkAction, BulkUpdateOpsAction[TRow, TData], ABC):
    """A soft delete over the entities the caller named."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE
