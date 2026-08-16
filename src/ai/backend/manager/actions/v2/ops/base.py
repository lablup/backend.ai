from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, override

from ai.backend.common.data.entity.types import EntityID
from ai.backend.common.data.entity.types import EntityID as OwnerEntityID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.creator import (
    EntityCreator,
    FieldCreator,
    GlobalEntityCreator,
    RoleManagedEntityCreator,
)
from ai.backend.manager.models.specs.lookup import DataLookup
from ai.backend.manager.models.specs.purger import (
    DataBatchPurger,
    EntityPurger,
    FieldPurger,
)
from ai.backend.manager.models.specs.querier import DataQuerier
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.models.specs.upserter import (
    EntityUpserter,
    FieldUpserter,
    GlobalEntityUpserter,
)

__all__ = (
    "OpsBackendAction",
    "GetOpsAction",
    "LookupOpsAction",
    "SearchOpsAction",
    "GlobalSearchOpsAction",
    "GlobalEntityCreateOpsAction",
    "GlobalEntityWithFieldsCreateOpsAction",
    "EntityCreateOpsAction",
    "RoleManagedEntityCreateOpsAction",
    "FieldCreateOpsAction",
    "GlobalEntityAtomicCreateOpsAction",
    "EntityAtomicCreateOpsAction",
    "RoleManagedEntityAtomicCreateOpsAction",
    "FieldAtomicCreateOpsAction",
    "EntityPurgeOpsAction",
    "FieldPurgeOpsAction",
    "GlobalEntityPartialBulkPurgeOpsAction",
    "EntityPartialBulkPurgeOpsAction",
    "FieldPartialBulkPurgeOpsAction",
    "GlobalEntityUpsertOpsAction",
    "EntityUpsertOpsAction",
    "FieldUpsertOpsAction",
    "UpdateOpsAction",
    "PartialBulkUpdateOpsAction",
    "BatchUpdateOpsAction",
    "GlobalBatchUpdateOpsAction",
    "BatchPurgeOpsAction",
    "GlobalBatchPurgeOpsAction",
    "LookupEntityOpsAction",
    "GetSingleEntityOpsAction",
    "OperationScopeOpsAction",
    "SearchGlobalOpsAction",
    "CreateGlobalOpsAction",
    "CreateGlobalWithFieldsOpsAction",
    "CreateEntityOpsAction",
    "CreateRoleManagedEntityOpsAction",
    "CreateFieldOpsAction",
    "AtomicCreateGlobalEntityOpsAction",
    "AtomicCreateEntityOpsAction",
    "AtomicCreateRoleManagedEntityOpsAction",
    "AtomicCreateFieldOpsAction",
    "PurgeEntityOpsAction",
    "PurgeFieldOpsAction",
    "PartialBulkPurgeGlobalEntityOpsAction",
    "PartialBulkPurgeEntityOpsAction",
    "PartialBulkPurgeFieldOpsAction",
    "UpsertGlobalOpsAction",
    "UpsertEntityOpsAction",
    "UpsertFieldOpsAction",
    "UpdateGlobalOpsAction",
    "UpdateSingleEntityOpsAction",
    "DeleteSingleEntityOpsAction",
    "RestoreSingleEntityOpsAction",
    "UpdatePartialBulkOpsAction",
    "DeletePartialBulkOpsAction",
    "RestorePartialBulkOpsAction",
    "BatchUpdateScopeOpsAction",
    "BatchUpdateGlobalOpsAction",
    "BatchPurgeScopeOpsAction",
    "BatchPurgeGlobalOpsAction",
    "GetGlobalOpsAction",
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
    def to_lookup(self) -> DataLookup[TRow, TData]:
        """Return the key-resolution spec this action executes."""
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


class GlobalEntityCreateOpsAction[TRow: Base, TData](OpsBackendAction):
    """Carries the global insert spec; no scope membership involved."""

    @abstractmethod
    def to_creator(self) -> GlobalEntityCreator[TRow, TData]:
        """Return the insert spec this action executes."""
        raise NotImplementedError


class GlobalEntityWithFieldsCreateOpsAction[TRow: Base, TData, TFieldRow: Base, TFieldData](
    OpsBackendAction
):
    """Carries a global insert spec together with the field specs it owns.

    One action so the two writes share a transaction: split apart, the parent could
    survive a failed field row.
    """

    @abstractmethod
    def to_creator(self) -> GlobalEntityCreator[TRow, TData]:
        """Return the insert spec for the owning row."""
        raise NotImplementedError

    @abstractmethod
    def to_field_creators(self) -> Sequence[FieldCreator[Any, TFieldRow, TFieldData]]:
        """Return one insert spec per field row created under the owner."""
        raise NotImplementedError


class EntityCreateOpsAction[TRow: Base, TData](OpsBackendAction):
    """Carries the entity insert spec: creating provisions the row's own virtual
    scope and joins its declared memberships. No roles are involved."""

    @abstractmethod
    def to_creator(self) -> EntityCreator[TRow, TData]:
        """Return the insert spec this action executes."""
        raise NotImplementedError


class RoleManagedEntityCreateOpsAction[TRow: Base, TData](OpsBackendAction):
    """Carries the role-managed entity insert spec: the entity create plus the
    preset-role provisioning the combined spec declares."""

    @abstractmethod
    def to_creator(self) -> RoleManagedEntityCreator[TRow, TData]:
        """Return the insert spec this action executes."""
        raise NotImplementedError


class FieldCreateOpsAction[TOwnerID: OwnerEntityID, TRow: Base, TData](OpsBackendAction):
    """Carries the field insert spec plus the owner's identifier.

    The owner id is declared here rather than leaning on the shape's
    ``entity_id()``: the shape names the RBAC target (the owner), while this axis
    supplies the execution input — the same split ``SearchOpsAction.operation_scopes``
    keeps from ``scope_targets``.
    """

    @abstractmethod
    def to_creator(self) -> FieldCreator[TOwnerID, TRow, TData]:
        """Return the insert spec this action executes."""
        raise NotImplementedError

    @abstractmethod
    def owner_id(self) -> TOwnerID:
        """Return the owning entity's identifier the row is built under."""
        raise NotImplementedError


class GlobalEntityAtomicCreateOpsAction[TRow: Base, TData](OpsBackendAction):
    """A create of several global rows at once, atomically; nothing is registered."""

    @abstractmethod
    def to_creators(self) -> Sequence[GlobalEntityCreator[TRow, TData]]:
        """Return one insert spec per row this action creates."""
        raise NotImplementedError


class EntityAtomicCreateOpsAction[TRow: Base, TData](OpsBackendAction):
    """A create of several entity rows at once, atomically; each row's scope is
    provisioned with it."""

    @abstractmethod
    def to_creators(self) -> Sequence[EntityCreator[TRow, TData]]:
        """Return one insert spec per row this action creates."""
        raise NotImplementedError


class RoleManagedEntityAtomicCreateOpsAction[TRow: Base, TData](OpsBackendAction):
    """An atomic create of several role-managed entity rows, preset roles included."""

    @abstractmethod
    def to_creators(self) -> Sequence[RoleManagedEntityCreator[TRow, TData]]:
        """Return one insert spec per row this action creates."""
        raise NotImplementedError


class FieldAtomicCreateOpsAction[TOwnerID: OwnerEntityID, TRow: Base, TData](OpsBackendAction):
    """A create of several field rows sharing one owner, atomically."""

    @abstractmethod
    def to_creators(self) -> Sequence[FieldCreator[TOwnerID, TRow, TData]]:
        """Return one insert spec per row this action creates."""
        raise NotImplementedError

    @abstractmethod
    def owner_id(self) -> TOwnerID:
        """Return the owning entity's identifier the rows are built under."""
        raise NotImplementedError


class EntityPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """Carries the delete spec of one entity named by id."""

    @abstractmethod
    def to_purger(self) -> EntityPurger[TRow, TData]:
        """Return the hard-delete spec this action executes."""
        raise NotImplementedError


class FieldPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """Carries the field delete spec; authorized through the owner the
    shape names, like an update to the owning entity."""

    @abstractmethod
    def to_purger(self) -> FieldPurger[TRow, TData]:
        """Return the hard-delete spec this action executes."""
        raise NotImplementedError


class GlobalEntityPartialBulkPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """A hard delete of global entities the caller named, each answered for
    separately; no membership involved."""

    @abstractmethod
    def to_purgers(self) -> Mapping[EntityID, EntityPurger[TRow, TData]]:
        """Return the delete spec for each entity this action names."""
        raise NotImplementedError


class EntityPartialBulkPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """A hard delete of entities the caller named, each answered for separately;
    every row's scope is torn down with it."""

    @abstractmethod
    def to_purgers(self) -> Mapping[EntityID, EntityPurger[TRow, TData]]:
        """Return the delete spec for each entity this action names."""
        raise NotImplementedError


class FieldPartialBulkPurgeOpsAction[TRow: Base, TData](OpsBackendAction):
    """A hard delete of field rows the caller named, each answered for
    separately; authorized through the owner the shape names."""

    @abstractmethod
    def to_purgers(self) -> Mapping[EntityID, FieldPurger[TRow, TData]]:
        """Return the delete spec for each entity this action names."""
        raise NotImplementedError


class GlobalEntityUpsertOpsAction[TRow: Base, TData](OpsBackendAction):
    """A create-or-update of a global entity; nothing is registered either way."""

    @abstractmethod
    def to_upserter(self) -> GlobalEntityUpserter[TRow, TData]:
        """Return the upsert spec this action executes."""
        raise NotImplementedError


class EntityUpsertOpsAction[TRow: Base, TData](OpsBackendAction):
    """A create-or-update of an entity; the scope stays provisioned idempotently."""

    @abstractmethod
    def to_upserter(self) -> EntityUpserter[TRow, TData]:
        """Return the upsert spec this action executes."""
        raise NotImplementedError


class FieldUpsertOpsAction[TOwnerID: OwnerEntityID, TRow: Base, TData](OpsBackendAction):
    """A create-or-update of a field row under its owner's settled identifier."""

    @abstractmethod
    def to_upserter(self) -> FieldUpserter[TOwnerID, TRow, TData]:
        """Return the upsert spec this action executes."""
        raise NotImplementedError

    @abstractmethod
    def owner_id(self) -> TOwnerID:
        """Return the owning entity's identifier the row is built under."""
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


class PartialBulkUpdateOpsAction[TRow: Base, TData](OpsBackendAction):
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


class LookupEntityOpsAction[TRow: Base, TData](BaseLookupAction, LookupOpsAction[TRow, TData], ABC):
    """A key resolution backed by ops: the lookup shape paired with its spec.

    Declares nothing further — the shape fixes the operation, and the spec carries
    the key's columns and the conversion.
    """


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


class OperationScopeOpsAction[TRow: Base, TData](
    BaseScopeAction, SearchOpsAction[TRow, TData], ABC
):
    """A page read from within the scopes the action names."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


class SearchGlobalOpsAction[TRow: Base, TData](
    BaseGlobalAction, GlobalSearchOpsAction[TRow, TData], ABC
):
    """A page read across the whole table."""

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


class CreateGlobalWithFieldsOpsAction[TRow: Base, TData, TFieldRow: Base, TFieldData](
    BaseGlobalAction,
    GlobalEntityWithFieldsCreateOpsAction[TRow, TData, TFieldRow, TFieldData],
    ABC,
):
    """An insert of one row of system-wide state together with the rows it owns."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class CreateEntityOpsAction[TRow: Base, TData](
    BaseScopeAction, EntityCreateOpsAction[TRow, TData], ABC
):
    """An insert of one entity row.

    Scope-shaped: the new entity's id does not exist until the row does, so the
    action targets the scope context it creates in rather than an entity.
    """

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class CreateRoleManagedEntityOpsAction[TRow: Base, TData](
    BaseScopeAction, RoleManagedEntityCreateOpsAction[TRow, TData], ABC
):
    """An insert of one role-managed entity row."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class CreateFieldOpsAction[TOwnerID: OwnerEntityID, TRow: Base, TData](
    BaseSingleEntityAction, FieldCreateOpsAction[TOwnerID, TRow, TData], ABC
):
    """An insert of a field row, authorized against its owner.

    The single-entity shape's target is the owner entity — creating a field row is
    answered for like an update to the owner — so ``entity_id()`` names the owner.
    """

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class AtomicCreateGlobalEntityOpsAction[TRow: Base, TData](
    BaseGlobalAction, GlobalEntityAtomicCreateOpsAction[TRow, TData], ABC
):
    """An atomic insert of several rows of system-wide state."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class AtomicCreateEntityOpsAction[TRow: Base, TData](
    BaseScopeAction, EntityAtomicCreateOpsAction[TRow, TData], ABC
):
    """An atomic insert of several entity rows."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class AtomicCreateRoleManagedEntityOpsAction[TRow: Base, TData](
    BaseScopeAction, RoleManagedEntityAtomicCreateOpsAction[TRow, TData], ABC
):
    """An atomic insert of several role-managed entity rows."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class AtomicCreateFieldOpsAction[TOwnerID: OwnerEntityID, TRow: Base, TData](
    BaseSingleEntityAction, FieldAtomicCreateOpsAction[TOwnerID, TRow, TData], ABC
):
    """An atomic insert of several field rows, authorized against their one owner."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


class PurgeEntityOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, EntityPurgeOpsAction[TRow, TData], ABC
):
    """A hard delete of an entity row, tearing its scope down with it."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class PurgeFieldOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, FieldPurgeOpsAction[TRow, TData], ABC
):
    """A hard delete of a field row, authorized against its owner."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class PartialBulkPurgeGlobalEntityOpsAction[TRow: Base, TData](
    BaseBulkAction, GlobalEntityPartialBulkPurgeOpsAction[TRow, TData], ABC
):
    """A hard delete over the global entities the caller named."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class PartialBulkPurgeEntityOpsAction[TRow: Base, TData](
    BaseBulkAction, EntityPartialBulkPurgeOpsAction[TRow, TData], ABC
):
    """A hard delete over the entities the caller named."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class PartialBulkPurgeFieldOpsAction[TRow: Base, TData](
    BaseBulkAction, FieldPartialBulkPurgeOpsAction[TRow, TData], ABC
):
    """A hard delete over the field rows the caller named."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class UpsertGlobalOpsAction[TRow: Base, TData](
    BaseGlobalAction, GlobalEntityUpsertOpsAction[TRow, TData], ABC
):
    """A create-or-update of one row of system-wide state."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPSERT


class UpsertEntityOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, EntityUpsertOpsAction[TRow, TData], ABC
):
    """A single-entity create-or-update, backed by ops."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPSERT


class UpsertFieldOpsAction[TOwnerID: OwnerEntityID, TRow: Base, TData](
    BaseSingleEntityAction, FieldUpsertOpsAction[TOwnerID, TRow, TData], ABC
):
    """A create-or-update of a field row, authorized against its owner."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPSERT


class GetGlobalOpsAction[TRow: Base, TData](BaseGlobalAction, GetOpsAction[TRow, TData], ABC):
    """A read of one row of system-wide state, named by the key its querier carries.

    Global rather than single-entity for the same reason the update is: the row
    belongs to no RBAC scope, and the catalogs this shape serves are keyed by a
    name the caller passes as-is.
    """

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


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


class UpdateSingleEntityOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, UpdateOpsAction[TRow, TData], ABC
):
    """A single-entity write, backed by ops. A soft delete carries this too."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


class DeleteSingleEntityOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, UpdateOpsAction[TRow, TData], ABC
):
    """A single-entity soft delete: a status transition, so it carries an updater."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


class RestoreSingleEntityOpsAction[TRow: Base, TData](
    BaseSingleEntityAction, UpdateOpsAction[TRow, TData], ABC
):
    """A single-entity restore: the soft delete run backwards, so it carries an
    updater too. Recorded as ``RESTORE`` while checking the soft-delete permission —
    undoing a delete reaches nothing the deleter could not already reach."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.RESTORE


class UpdatePartialBulkOpsAction[TRow: Base, TData](
    BaseBulkAction, PartialBulkUpdateOpsAction[TRow, TData], ABC
):
    """A write over the entities the caller named. A bulk soft delete carries this too."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


class DeletePartialBulkOpsAction[TRow: Base, TData](
    BaseBulkAction, PartialBulkUpdateOpsAction[TRow, TData], ABC
):
    """A soft delete over the entities the caller named."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


class RestorePartialBulkOpsAction[TRow: Base, TData](
    BaseBulkAction, PartialBulkUpdateOpsAction[TRow, TData], ABC
):
    """A restore over the entities the caller named."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.RESTORE


class BatchUpdateScopeOpsAction[TRow: Base, TData](
    BaseScopeAction, BatchUpdateOpsAction[TRow, TData], ABC
):
    """A write over every row matching the action's condition."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


class BatchUpdateGlobalOpsAction[TRow: Base, TData](
    BaseGlobalAction, GlobalBatchUpdateOpsAction[TRow, TData], ABC
):
    """A write over every matching row of system-wide state."""

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


class BatchPurgeGlobalOpsAction[TRow: Base, TData](
    BaseGlobalAction, GlobalBatchPurgeOpsAction[TRow, TData], ABC
):
    """A hard delete of every matching row of system-wide state."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE
