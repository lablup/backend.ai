from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import override

from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.entity import EntityID as OwnerEntityID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.creator import (
    FieldEntityCreator,
    GlobalEntityCreator,
    ScopedEntityCreator,
)
from ai.backend.manager.models.specs.purger import (
    FieldEntityPurger,
    GlobalEntityPurger,
    ScopedEntityPurger,
)
from ai.backend.manager.models.specs.upserter import ScopedEntityUpserter
from ai.backend.manager.repositories.base.purger import DataBatchPurger
from ai.backend.manager.repositories.base.querier import DataFinder, DataQuerier
from ai.backend.manager.repositories.base.searcher import Searcher
from ai.backend.manager.repositories.base.updater import DataBatchUpdater, DataUpdater

__all__ = (
    "OpsBackendAction",
    "GetOpsAction",
    "LookupOpsAction",
    "GlobalEntityCreateOpsAction",
    "ScopedEntityCreateOpsAction",
    "FieldEntityCreateOpsAction",
    "FieldEntityPurgeOpsAction",
    "ScopedEntityBulkCreateOpsAction",
    "BulkUpdateOpsAction",
    "ScopedEntityBulkPurgeOpsAction",
    "BatchUpdateOpsAction",
    "GlobalBatchUpdateOpsAction",
    "BatchPurgeOpsAction",
    "GlobalBatchPurgeOpsAction",
    "UpdateOpsAction",
    "ScopedEntityUpsertOpsAction",
    "GlobalEntityPurgeOpsAction",
    "ScopedEntityPurgeOpsAction",
    "SearchOpsAction",
    "GlobalSearchOpsAction",
    "GetSingleEntityOpsAction",
    "UpdateSingleEntityOpsAction",
    "DeleteSingleEntityOpsAction",
    "UpsertSingleEntityOpsAction",
    "PurgeSingleEntityOpsAction",
    "CreateFieldEntityOpsAction",
    "PurgeFieldEntityOpsAction",
    "UpdateBulkOpsAction",
    "DeleteBulkOpsAction",
    "PurgeBulkOpsAction",
    "CreateScopeOpsAction",
    "BulkCreateScopeOpsAction",
    "BatchUpdateScopeOpsAction",
    "BatchPurgeScopeOpsAction",
    "BatchUpdateGlobalOpsAction",
    "BatchPurgeGlobalOpsAction",
    "OperationScopeOpsAction",
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


class GlobalEntityCreateOpsAction[TRow: Base, TData](OpsBackendAction):
    """Carries the global-family insert spec; no scope membership involved."""

    @abstractmethod
    def to_creator(self) -> GlobalEntityCreator[TRow, TData]:
        """Return the insert spec this action executes."""
        raise NotImplementedError


class ScopedEntityCreateOpsAction[TRow: Base, TData](OpsBackendAction):
    """Carries the scoped-family insert spec: creating registers the entity's
    declared membership, so the spec has to answer it."""

    @abstractmethod
    def to_creator(self) -> ScopedEntityCreator[TRow, TData]:
        """Return the insert spec this action executes."""
        raise NotImplementedError


class ScopedEntityBulkCreateOpsAction[TRow: Base, TData](OpsBackendAction):
    """A create of several scoped rows at once, atomically."""

    @abstractmethod
    def to_creators(self) -> Sequence[ScopedEntityCreator[TRow, TData]]:
        """Return one insert spec per row this action creates."""
        raise NotImplementedError


class FieldEntityCreateOpsAction[TOwnerID: OwnerEntityID, TRow: Base, TData](OpsBackendAction):
    """Carries the field-family insert spec plus the owner's identifier.

    The owner id is declared here rather than leaning on the shape's
    ``entity_id()``: the shape names the RBAC target (the owner), while this axis
    supplies the execution input — the same split ``SearchOpsAction.operation_scopes``
    keeps from ``scope_targets``.
    """

    @abstractmethod
    def to_creator(self) -> FieldEntityCreator[TOwnerID, TRow, TData]:
        """Return the insert spec this action executes."""
        raise NotImplementedError

    @abstractmethod
    def owner_id(self) -> TOwnerID:
        """Return the owning entity's identifier the row is built under."""
        raise NotImplementedError


class FieldEntityPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """Carries the field-family delete spec; authorized through the owner the
    shape names, like an update to the owning entity."""

    @abstractmethod
    def to_purger(self) -> FieldEntityPurger[TRow, TData]:
        """Return the hard-delete spec this action executes."""
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


class ScopedEntityBulkPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """A hard delete of scoped entities the caller named, each answered for
    separately; every row's membership is removed with it."""

    @abstractmethod
    def to_purgers(self) -> Mapping[EntityID, ScopedEntityPurger[TRow, TData]]:
        """Return the delete spec for each entity this action names."""
        raise NotImplementedError


class BatchUpdateOpsAction[TRow: Base, TData](OpsBackendAction):
    """An update of every row matching a condition within the scopes it names.

    The scopes are injected into the statement itself, the way the scoped search
    injects them into its query — the spec's conditions cannot widen the write
    past them.
    """

    @abstractmethod
    def to_batch_updater(self) -> DataBatchUpdater[TRow, TData]:
        """Return the batch update spec this action executes."""
        raise NotImplementedError

    @abstractmethod
    def operation_scopes(self) -> Sequence[OperationScope]:
        """Return the scopes the write is restricted to. Never empty.

        Same contract as ``SearchOpsAction.operation_scopes``: distinct from the RBAC
        ``scope_targets()`` the shape axis declares, and an empty sequence is
        rejected rather than widened into an unscoped sweep.
        """
        raise NotImplementedError


class GlobalBatchUpdateOpsAction[TRow: Base, TData](OpsBackendAction):
    """An update of every matching row across the table, with no scope filter."""

    @abstractmethod
    def to_batch_updater(self) -> DataBatchUpdater[TRow, TData]:
        """Return the batch update spec this action executes."""
        raise NotImplementedError


class BatchPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """A hard delete of every row matching a condition within the scopes it names."""

    @abstractmethod
    def to_batch_purger(self) -> DataBatchPurger[TRow, TData]:
        """Return the batch delete spec this action executes."""
        raise NotImplementedError

    @abstractmethod
    def operation_scopes(self) -> Sequence[OperationScope]:
        """Return the scopes the delete is restricted to. Never empty."""
        raise NotImplementedError


class GlobalBatchPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """A hard delete of every matching row across the table, with no scope filter."""

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


class ScopedEntityUpsertOpsAction[TRow: Base, TData](OpsBackendAction):
    """A create-or-update of a scoped entity, registering under the create rule."""

    @abstractmethod
    def to_upserter(self) -> ScopedEntityUpserter[TRow, TData]:
        """Return the upsert spec this action executes."""
        raise NotImplementedError


class GlobalEntityPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """Carries the global-family delete spec; no membership to remove."""

    @abstractmethod
    def to_purger(self) -> GlobalEntityPurger[TRow, TData]:
        """Return the hard-delete spec this action executes."""
        raise NotImplementedError


class ScopedEntityPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """Carries the scoped-family delete spec: purging removes the entity's
    membership symmetrically with the create."""

    @abstractmethod
    def to_purger(self) -> ScopedEntityPurger[TRow, TData]:
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
    def operation_scopes(self) -> Sequence[OperationScope]:
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
    BaseSingleEntityAction, ScopedEntityUpsertOpsAction[TRow, TData], ABC
):
    """A single-entity create-or-update, backed by ops."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPSERT


class PurgeSingleEntityOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, ScopedEntityPurgeOpsAction[TRow, TData], ABC
):
    """A single-entity hard delete, backed by ops."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class CreateFieldEntityOpsAction[TOwnerID: OwnerEntityID, TRow: Base, TData](
    BaseSingleEntityAction, FieldEntityCreateOpsAction[TOwnerID, TRow, TData], ABC
):
    """An insert of a field row, authorized against its owner.

    The single-entity shape's target is the owner entity — creating a field row is
    answered for like an update to the owner — so ``entity_id()`` names the owner.
    """

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class PurgeFieldEntityOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, FieldEntityPurgeOpsAction[TRow, TData], ABC
):
    """A hard delete of a field row, authorized against its owner."""

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


class PurgeBulkOpsAction[TRow: Base, TData](
    BaseBulkAction, ScopedEntityBulkPurgeOpsAction[TRow, TData], ABC
):
    """A hard delete over the entities the caller named."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class CreateScopeOpsAction[TRow: Base, TData](
    BaseScopeAction, ScopedEntityCreateOpsAction[TRow, TData], ABC
):
    """An insert of one row into the scope the action names."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class BulkCreateScopeOpsAction[TRow: Base, TData](
    BaseScopeAction, ScopedEntityBulkCreateOpsAction[TRow, TData], ABC
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


class OperationScopeOpsAction[TRow: Base, TData](
    BaseScopeAction, SearchOpsAction[TRow, TData], ABC
):
    """A page read from within the scopes the action names."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


class CreateGlobalOpsAction[TRow: Base, TData](
    BaseGlobalAction, GlobalEntityCreateOpsAction[TRow, TData], ABC
):
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


class PurgeGlobalOpsAction[TRow: Base, TData](
    BaseGlobalAction, GlobalEntityPurgeOpsAction[TRow, TData], ABC
):
    """A hard delete of one row of system-wide state."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class BatchUpdateGlobalOpsAction[TRow: Base, TData](
    BaseGlobalAction, GlobalBatchUpdateOpsAction[TRow, TData], ABC
):
    """A write over every matching row of system-wide state."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


class BatchPurgeGlobalOpsAction[TRow: Base, TData](
    BaseGlobalAction, GlobalBatchPurgeOpsAction[TRow, TData], ABC
):
    """A hard delete of every matching row of system-wide state."""

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
