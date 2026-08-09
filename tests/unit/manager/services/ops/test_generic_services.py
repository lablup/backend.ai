"""A pass-through domain wires all six operations without a single service method.

Every class below is either an action or one of the domain's specs. There is no
``services/<domain>/service.py`` in the chain, which is the whole point: 344 of the 535
action-taking service methods do nothing but forward a spec and re-wrap the answer.

``OpsRepository`` is exercised against a database in
``tests/unit/manager/repositories/ops/test_ops_repository.py`` and mocked here, so what
these tests pin down is that each service hands the action's own spec object through
untouched — anything rebuilt in between would be domain logic creeping back into the
generic path — and lands the answer in the shared result.
"""

from __future__ import annotations

import uuid
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, override
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.types import EntityData, EntityType, ScopeRef, ScopeType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction, LookupKey
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.base import (
    BatchPurgeOpsAction,
    BatchUpdateOpsAction,
    BulkUpdateOpsAction,
    EntityBulkCreateOpsAction,
    EntityBulkPurgeOpsAction,
    EntityCreateOpsAction,
    EntityPurgeOpsAction,
    EntityUpsertOpsAction,
    FieldEntityBulkCreateOpsAction,
    FieldEntityBulkPurgeOpsAction,
    FieldEntityUpsertOpsAction,
    GetOpsAction,
    GlobalEntityBulkCreateOpsAction,
    GlobalEntityBulkPurgeOpsAction,
    GlobalEntityUpsertOpsAction,
    GlobalSearchOpsAction,
    LookupOpsAction,
    RoleManagedEntityBulkCreateOpsAction,
    RoleManagedEntityCreateOpsAction,
    RoleManagedEntityUpsertOpsAction,
    SearchOpsAction,
    UpdateOpsAction,
)
from ai.backend.manager.actions.v2.ops.result import (
    CreatedEntityOpsResult,
    EntitiesOpsResult,
    EntityOpsResult,
    LookupOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.specs.creator import (
    EntityCreator,
    FieldEntityCreator,
    GlobalEntityCreator,
    RoleManagedEntityCreator,
)
from ai.backend.manager.models.specs.lookup import DataLookup
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.specs.purger import (
    DataBatchPurger,
    EntityPurger,
    FieldEntityPurger,
    GlobalEntityPurger,
)
from ai.backend.manager.models.specs.querier import DataQuerier
from ai.backend.manager.models.specs.searcher import Searcher, SearcherResult
from ai.backend.manager.models.specs.types import (
    BulkResultWithFailures,
    ConflictCheck,
    IntegrityErrorCheck,
)
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.models.specs.upserter import (
    EntityUpserter,
    FieldEntityUpserter,
    GlobalEntityUpserter,
    RoleManagedEntityUpserter,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.ops.service import (
    BatchPurgeService,
    BatchUpdateService,
    BulkDeleteService,
    BulkUpdateService,
    DeleteService,
    EntityBulkCreateService,
    EntityBulkPurgeService,
    EntityCreateService,
    EntityPurgeService,
    EntityUpsertService,
    FieldBulkCreateService,
    FieldBulkPurgeService,
    FieldUpsertService,
    GetService,
    GlobalBulkCreateService,
    GlobalBulkPurgeService,
    GlobalSearchService,
    GlobalUpsertService,
    LookupService,
    RoleManagedEntityBulkCreateService,
    RoleManagedEntityCreateService,
    RoleManagedEntityUpsertService,
    SearchService,
    UpdateService,
)

_ENTITY_TYPE = EntityType("role_preset")
_SCOPE_TYPE = ScopeType(_ENTITY_TYPE)


# =============================================================================
# The domain's own types: a `data/` value and its specs.
# =============================================================================


@dataclass(frozen=True)
class _PresetData(EntityData):
    """What the repository returns. Names itself because ``create`` has to report it."""

    id: uuid.UUID
    name: str

    @override
    def entity_id(self) -> EntityID:
        return self.id


@dataclass
class _PresetQuerier(DataQuerier[RolePresetRow, _PresetData]):
    target: uuid.UUID

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.target

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


class _PresetCreator(EntityCreator[RolePresetRow, _PresetData]):
    @override
    def scope_type(self) -> ScopeType:
        return _SCOPE_TYPE

    @override
    def scope_id(self, row: RolePresetRow) -> ScopeID:
        return row.id

    @override
    def member_of(self, row: RolePresetRow) -> Collection[ScopeRef]:
        return ()

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> RolePresetRow:
        return RolePresetRow()

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


class _PresetRoleManagedCreator(RoleManagedEntityCreator[RolePresetRow, _PresetData]):
    @override
    def scope_type(self) -> ScopeType:
        return _SCOPE_TYPE

    @override
    def scope_id(self, row: RolePresetRow) -> ScopeID:
        return row.id

    @override
    def member_of(self, row: RolePresetRow) -> Collection[ScopeRef]:
        return ()

    @override
    def template_value(self, row: RolePresetRow) -> ScopeTemplateValue:
        return ScopeTemplateValue(id=row.id, name=row.name, type="role_preset")

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> RolePresetRow:
        return RolePresetRow()

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetUpdater(DataUpdater[RolePresetRow, _PresetData]):
    target: uuid.UUID
    values: dict[str, Any] = field(default_factory=lambda: {"name": "renamed"})

    @property
    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.target

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return self.values

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetPurger(EntityPurger[RolePresetRow, _PresetData]):
    target: uuid.UUID

    @override
    def scope_of(self) -> ScopeRef:
        return ScopeRef(scope_type=_SCOPE_TYPE, scope_id=self.target)

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.target

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetByName(DataLookup[RolePresetRow, _PresetData]):
    name: str

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: RolePresetRow.name == self.name]

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetBatchUpdater(DataBatchUpdater[RolePresetRow, _PresetData]):
    @property
    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [lambda: sa.true()]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"deleted": True}

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetBatchPurger(DataBatchPurger[RolePresetRow, _PresetData]):
    @override
    def build_subquery(self) -> sa.sql.Select[tuple[RolePresetRow]]:
        return sa.select(RolePresetRow)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetUpserter(EntityUpserter[RolePresetRow, _PresetData]):
    target: uuid.UUID

    @override
    def scope_type(self) -> ScopeType:
        return _SCOPE_TYPE

    @override
    def scope_id(self, row: RolePresetRow) -> ScopeID:
        return row.id

    @override
    def member_of(self, row: RolePresetRow) -> Collection[ScopeRef]:
        return ()

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.target, "name": "default"}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"name": "default"}

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


class _PresetGlobalCreator(GlobalEntityCreator[RolePresetRow, _PresetData]):
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> RolePresetRow:
        return RolePresetRow()

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


class _PresetFieldCreator(FieldEntityCreator[uuid.UUID, RolePresetRow, _PresetData]):
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: uuid.UUID) -> RolePresetRow:
        return RolePresetRow()

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetGlobalPurger(GlobalEntityPurger[RolePresetRow, _PresetData]):
    target: uuid.UUID

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.target

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetFieldPurger(FieldEntityPurger[RolePresetRow, _PresetData]):
    target: uuid.UUID

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.target

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetGlobalUpserter(GlobalEntityUpserter[RolePresetRow, _PresetData]):
    target: uuid.UUID

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.target, "name": "default"}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"name": "default"}

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetFieldUpserter(FieldEntityUpserter[uuid.UUID, RolePresetRow, _PresetData]):
    target: uuid.UUID

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self, owner_id: uuid.UUID) -> dict[str, Any]:
        return {"id": self.target, "name": "default"}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"name": "default"}

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetRoleManagedUpserter(RoleManagedEntityUpserter[RolePresetRow, _PresetData]):
    target: uuid.UUID

    @override
    def scope_type(self) -> ScopeType:
        return _SCOPE_TYPE

    @override
    def scope_id(self, row: RolePresetRow) -> ScopeID:
        return row.id

    @override
    def member_of(self, row: RolePresetRow) -> Collection[ScopeRef]:
        return ()

    @override
    def template_value(self, row: RolePresetRow) -> ScopeTemplateValue:
        return ScopeTemplateValue(id=row.id, name=row.name, type="role_preset")

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.target, "name": "default"}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"name": "default"}

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetSearcher(Searcher[RolePresetRow, _PresetData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RolePresetRow)

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass(frozen=True)
class _ProjectScope(OperationScope):
    project_id: uuid.UUID

    @override
    def to_condition(self) -> QueryCondition:
        return lambda: sa.true()

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


# =============================================================================
# The domain's actions: a shape base for RBAC/audit, an ops base for the spec.
# =============================================================================


@dataclass
class _GetAction(BaseSingleEntityAction, GetOpsAction[RolePresetRow, _PresetData]):
    target: EntityID
    querier: _PresetQuerier

    @override
    def to_querier(self) -> DataQuerier[RolePresetRow, _PresetData]:
        return self.querier

    @override
    def entity_id(self) -> EntityID:
        return self.target

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @classmethod
    @override
    def action_name(cls) -> str:
        return "get_role_preset"


@dataclass
class _DeleteAction(BaseSingleEntityAction, UpdateOpsAction[RolePresetRow, _PresetData]):
    """A soft delete: declared as DELETE, written as an update of the deleted flag."""

    target: EntityID
    updater: _PresetUpdater

    @override
    def to_updater(self) -> DataUpdater[RolePresetRow, _PresetData]:
        return self.updater

    @override
    def entity_id(self) -> EntityID:
        return self.target

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "delete_role_preset"


@dataclass
class _CreateAction(BaseScopeAction, EntityCreateOpsAction[RolePresetRow, _PresetData]):
    scope: ScopeRef
    creator: _PresetCreator

    @override
    def to_creator(self) -> EntityCreator[RolePresetRow, _PresetData]:
        return self.creator

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.scope,)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "create_role_preset"


@dataclass
class _UpdateAction(BaseSingleEntityAction, UpdateOpsAction[RolePresetRow, _PresetData]):
    target: EntityID
    updater: _PresetUpdater

    @override
    def to_updater(self) -> DataUpdater[RolePresetRow, _PresetData]:
        return self.updater

    @override
    def entity_id(self) -> EntityID:
        return self.target

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "update_role_preset"


@dataclass
class _PurgeAction(BaseSingleEntityAction, EntityPurgeOpsAction[RolePresetRow, _PresetData]):
    target: EntityID
    purger: _PresetPurger

    @override
    def to_purger(self) -> EntityPurger[RolePresetRow, _PresetData]:
        return self.purger

    @override
    def entity_id(self) -> EntityID:
        return self.target

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "purge_role_preset"


@dataclass
class _UpsertAction(BaseSingleEntityAction, EntityUpsertOpsAction[RolePresetRow, _PresetData]):
    """Declares itself an UPDATE: ``ActionOperationType`` has no upsert."""

    target: EntityID
    upserter: _PresetUpserter

    @override
    def to_upserter(self) -> EntityUpserter[RolePresetRow, _PresetData]:
        return self.upserter

    @override
    def entity_id(self) -> EntityID:
        return self.target

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "upsert_role_preset"


@dataclass(frozen=True)
class _NameKey(LookupKey):
    name: str

    @override
    def kind(self) -> str:
        return "name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}


@dataclass
class _LookupAction(BaseLookupAction, LookupOpsAction[RolePresetRow, _PresetData]):
    """Declares no target: producing one is the whole point of the run."""

    lookup: _PresetByName

    @override
    def to_lookup(self) -> DataLookup[RolePresetRow, _PresetData]:
        return self.lookup

    @override
    def lookup_key(self) -> LookupKey:
        return _NameKey(name=self.lookup.name)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "lookup_role_preset"


@dataclass
class _BulkUpdateAction(BaseBulkAction, BulkUpdateOpsAction[RolePresetRow, _PresetData]):
    updaters: dict[EntityID, _PresetUpdater]

    @override
    def to_updaters(self) -> Mapping[EntityID, DataUpdater[RolePresetRow, _PresetData]]:
        return self.updaters

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        # Read off the same mapping, so the two cannot drift.
        return tuple(self.updaters)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "update_role_presets"


@dataclass
class _BulkPurgeAction(BaseBulkAction, EntityBulkPurgeOpsAction[RolePresetRow, _PresetData]):
    purgers: dict[EntityID, _PresetPurger]

    @override
    def to_purgers(self) -> Mapping[EntityID, EntityPurger[RolePresetRow, _PresetData]]:
        return self.purgers

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        return tuple(self.purgers)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "purge_role_presets"


@dataclass
class _BulkCreateAction(BaseScopeAction, EntityBulkCreateOpsAction[RolePresetRow, _PresetData]):
    scope: ScopeRef
    creators: list[_PresetCreator]

    @override
    def to_creators(self) -> Sequence[EntityCreator[RolePresetRow, _PresetData]]:
        return self.creators

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.scope,)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "create_role_presets"


@dataclass
class _GlobalUpsertAction(
    BaseGlobalAction, GlobalEntityUpsertOpsAction[RolePresetRow, _PresetData]
):
    upserter: _PresetGlobalUpserter

    @override
    def to_upserter(self) -> GlobalEntityUpserter[RolePresetRow, _PresetData]:
        return self.upserter

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPSERT

    @classmethod
    @override
    def action_name(cls) -> str:
        return "upsert_global_role_preset"


@dataclass
class _BulkCreateGlobalAction(
    BaseGlobalAction, GlobalEntityBulkCreateOpsAction[RolePresetRow, _PresetData]
):
    creators: list[_PresetGlobalCreator]

    @override
    def to_creators(self) -> Sequence[GlobalEntityCreator[RolePresetRow, _PresetData]]:
        return self.creators

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "create_global_role_presets"


@dataclass
class _BulkPurgeGlobalAction(
    BaseBulkAction, GlobalEntityBulkPurgeOpsAction[RolePresetRow, _PresetData]
):
    purgers: dict[EntityID, _PresetGlobalPurger]

    @override
    def to_purgers(self) -> Mapping[EntityID, GlobalEntityPurger[RolePresetRow, _PresetData]]:
        return self.purgers

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        return tuple(self.purgers)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "purge_global_role_presets"


@dataclass
class _BulkCreateFieldAction(
    BaseSingleEntityAction, FieldEntityBulkCreateOpsAction[uuid.UUID, RolePresetRow, _PresetData]
):
    owner: uuid.UUID
    creators: list[_PresetFieldCreator]

    @override
    def to_creators(self) -> Sequence[FieldEntityCreator[uuid.UUID, RolePresetRow, _PresetData]]:
        return self.creators

    @override
    def owner_id(self) -> uuid.UUID:
        return self.owner

    @override
    def entity_id(self) -> EntityID:
        return self.owner

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "create_field_role_presets"


@dataclass
class _BulkPurgeFieldAction(
    BaseBulkAction, FieldEntityBulkPurgeOpsAction[RolePresetRow, _PresetData]
):
    purgers: dict[EntityID, _PresetFieldPurger]

    @override
    def to_purgers(self) -> Mapping[EntityID, FieldEntityPurger[RolePresetRow, _PresetData]]:
        return self.purgers

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        return tuple(self.purgers)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "purge_field_role_presets"


@dataclass
class _FieldUpsertAction(
    BaseSingleEntityAction, FieldEntityUpsertOpsAction[uuid.UUID, RolePresetRow, _PresetData]
):
    owner: uuid.UUID
    upserter: _PresetFieldUpserter

    @override
    def to_upserter(self) -> FieldEntityUpserter[uuid.UUID, RolePresetRow, _PresetData]:
        return self.upserter

    @override
    def owner_id(self) -> uuid.UUID:
        return self.owner

    @override
    def entity_id(self) -> EntityID:
        return self.owner

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPSERT

    @classmethod
    @override
    def action_name(cls) -> str:
        return "upsert_field_role_preset"


@dataclass
class _RoleManagedCreateAction(
    BaseScopeAction, RoleManagedEntityCreateOpsAction[RolePresetRow, _PresetData]
):
    scope: ScopeRef
    creator: _PresetRoleManagedCreator

    @override
    def to_creator(self) -> RoleManagedEntityCreator[RolePresetRow, _PresetData]:
        return self.creator

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.scope,)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "create_role_managed_role_preset"


@dataclass
class _RoleManagedBulkCreateAction(
    BaseScopeAction, RoleManagedEntityBulkCreateOpsAction[RolePresetRow, _PresetData]
):
    scope: ScopeRef
    creators: list[_PresetRoleManagedCreator]

    @override
    def to_creators(self) -> Sequence[RoleManagedEntityCreator[RolePresetRow, _PresetData]]:
        return self.creators

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.scope,)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "create_role_managed_role_presets"


@dataclass
class _RoleManagedUpsertAction(
    BaseSingleEntityAction, RoleManagedEntityUpsertOpsAction[RolePresetRow, _PresetData]
):
    target: EntityID
    upserter: _PresetRoleManagedUpserter

    @override
    def to_upserter(self) -> RoleManagedEntityUpserter[RolePresetRow, _PresetData]:
        return self.upserter

    @override
    def entity_id(self) -> EntityID:
        return self.target

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "upsert_role_managed_role_preset"


@dataclass
class _BatchUpdateAction(BaseScopeAction, BatchUpdateOpsAction[RolePresetRow, _PresetData]):
    scope: ScopeRef
    updater: _PresetBatchUpdater
    scopes: list[OperationScope] = field(default_factory=list)

    @override
    def to_batch_updater(self) -> DataBatchUpdater[RolePresetRow, _PresetData]:
        return self.updater

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.scopes

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.scope,)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "batch_update_role_presets"


@dataclass
class _BatchPurgeAction(BaseScopeAction, BatchPurgeOpsAction[RolePresetRow, _PresetData]):
    scope: ScopeRef
    purger: _PresetBatchPurger
    scopes: list[OperationScope] = field(default_factory=list)

    @override
    def to_batch_purger(self) -> DataBatchPurger[RolePresetRow, _PresetData]:
        return self.purger

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.scopes

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.scope,)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "batch_purge_role_presets"


@dataclass
class _GlobalSearchAction(BaseGlobalAction, GlobalSearchOpsAction[RolePresetRow, _PresetData]):
    """Declares no scope at all: the SUPERADMIN gate is what answers for the scan."""

    searcher: _PresetSearcher

    @override
    def to_searcher(self) -> Searcher[RolePresetRow, _PresetData]:
        return self.searcher

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @classmethod
    @override
    def action_name(cls) -> str:
        return "admin_search_role_presets"


@dataclass
class _SearchAction(BaseScopeAction, SearchOpsAction[RolePresetRow, _PresetData]):
    scope: ScopeRef
    searcher: _PresetSearcher
    scopes: list[OperationScope] = field(default_factory=list)

    @override
    def to_searcher(self) -> Searcher[RolePresetRow, _PresetData]:
        return self.searcher

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.scopes

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.scope,)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @classmethod
    @override
    def action_name(cls) -> str:
        return "search_role_presets"


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def stored() -> _PresetData:
    return _PresetData(id=uuid.uuid4(), name="default")


@pytest.fixture
def repository(stored: _PresetData) -> MagicMock:
    mock = MagicMock(spec=OpsRepository)
    for operation in (
        "get",
        "lookup",
        "create_entity",
        "create_role_managed_entity",
        "upsert_field_entity",
        "upsert_global_entity",
        "update",
        "upsert_entity",
        "upsert_role_managed_entity",
        "purge_entity",
    ):
        setattr(mock, operation, AsyncMock(return_value=stored))
    for operation in (
        "bulk_create_entities",
        "bulk_create_role_managed_entities",
        "bulk_create_global_entities",
        "bulk_create_field_entities",
        "batch_update_in_scopes",
        "batch_update_in_global",
        "batch_purge_in_scopes",
        "batch_purge_in_global",
    ):
        setattr(mock, operation, AsyncMock(return_value=[stored]))
    for operation in (
        "bulk_update",
        "bulk_purge_entities",
        "bulk_purge_global_entities",
        "bulk_purge_field_entities",
    ):
        setattr(
            mock,
            operation,
            AsyncMock(
                return_value=BulkResultWithFailures(successes={stored.id: stored}, errors={})
            ),
        )
    mock.search_in_global = AsyncMock(
        return_value=SearcherResult(
            items=[stored], total_count=1, has_next_page=False, has_previous_page=True
        )
    )
    mock.search_in_scopes = AsyncMock(
        return_value=SearcherResult(
            items=[stored], total_count=1, has_next_page=False, has_previous_page=True
        )
    )
    return mock


@pytest.fixture
def authenticated_user() -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


@pytest.fixture
def scope() -> ScopeRef:
    return ScopeRef(scope_type=ScopeType(EntityType("project")), scope_id=uuid.uuid4())


@pytest.fixture
def searcher() -> _PresetSearcher:
    return _PresetSearcher(pagination=OffsetPagination(offset=0, limit=20))


# =============================================================================
# The six operations, each wired with no domain service and no domain repository.
# =============================================================================


async def test_get_forwards_the_action_s_querier(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: GetService[_PresetData] = GetService(repository)
    querier = _PresetQuerier(target=stored.id)

    result = await service.execute(_GetAction(target=stored.id, querier=querier))

    assert result.data == stored
    repository.get.assert_awaited_once_with(querier)


async def test_delete_applies_the_action_s_updater(
    repository: MagicMock, stored: _PresetData
) -> None:
    # A soft delete writes through the update path; only the action says it is a delete.
    service: DeleteService[_PresetData] = DeleteService(repository)
    updater = _PresetUpdater(target=stored.id, values={"deleted": True})
    action = _DeleteAction(target=stored.id, updater=updater)

    result = await service.execute(action)

    assert action.operation_type() is ActionOperationType.DELETE
    assert result.data == stored
    repository.update.assert_awaited_once_with(updater)


async def test_create_forwards_the_action_s_creator(
    repository: MagicMock, stored: _PresetData, scope: ScopeRef
) -> None:
    service: EntityCreateService[_PresetData] = EntityCreateService(repository)
    creator = _PresetCreator()

    result = await service.execute(_CreateAction(scope=scope, creator=creator))

    assert result.data == stored
    repository.create_entity.assert_awaited_once_with(creator)


async def test_update_forwards_the_action_s_updater(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: UpdateService[_PresetData] = UpdateService(repository)
    updater = _PresetUpdater(target=stored.id)

    result = await service.execute(_UpdateAction(target=stored.id, updater=updater))

    assert result.data == stored
    repository.update.assert_awaited_once_with(updater)


async def test_upsert_forwards_the_action_s_upserter(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: EntityUpsertService[_PresetData] = EntityUpsertService(repository)
    upserter = _PresetUpserter(target=stored.id)

    result = await service.execute(_UpsertAction(target=stored.id, upserter=upserter))

    assert result.data == stored
    repository.upsert_entity.assert_awaited_once_with(upserter)


async def test_purge_forwards_the_action_s_purger(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: EntityPurgeService[_PresetData] = EntityPurgeService(repository)
    purger = _PresetPurger(target=stored.id)

    result = await service.execute(_PurgeAction(target=stored.id, purger=purger))

    assert result.data == stored
    repository.purge_entity.assert_awaited_once_with(purger)


async def test_lookup_forwards_the_action_s_lookup_spec(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: LookupService[_PresetData] = LookupService(repository)
    lookup = _PresetByName(name="default")

    result = await service.execute(_LookupAction(lookup=lookup))

    assert result.data == stored
    assert result.resolved_entity_id() == stored.id
    repository.lookup.assert_awaited_once_with(lookup)


async def test_lookup_runs_under_the_lookup_processor(
    repository: MagicMock, stored: _PresetData, authenticated_user: UserData
) -> None:
    # The lookup processor always puts the authentication gate first, so the run needs
    # a user in context even though the action declares no target.
    service: LookupService[_PresetData] = LookupService(repository)
    processor: LookupActionProcessor[_LookupAction, LookupOpsResult[_PresetData]] = (
        LookupActionProcessor(service.execute)
    )

    with with_user(authenticated_user):
        result = await processor.run(_LookupAction(lookup=_PresetByName(name="default")))

    # The id the key resolved to is what reaches the audit trail.
    assert result.resolved_entity_id() == stored.id


async def test_bulk_create_forwards_every_creator(
    repository: MagicMock, stored: _PresetData, scope: ScopeRef
) -> None:
    service: EntityBulkCreateService[_PresetData] = EntityBulkCreateService(repository)
    creators = [_PresetCreator(), _PresetCreator()]

    result = await service.execute(_BulkCreateAction(scope=scope, creators=creators))

    assert result.items == [stored]
    repository.bulk_create_entities.assert_awaited_once_with(creators)


async def test_bulk_update_answers_for_every_named_entity(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: BulkUpdateService[_PresetData] = BulkUpdateService(repository)
    updaters = {stored.id: _PresetUpdater(target=stored.id)}

    result = await service.execute(_BulkUpdateAction(updaters=updaters))

    assert [r.entity_id for r in result.entity_results()] == [stored.id]
    repository.bulk_update.assert_awaited_once_with(updaters)


async def test_bulk_delete_writes_through_the_update_path(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: BulkDeleteService[_PresetData] = BulkDeleteService(repository)
    updaters = {stored.id: _PresetUpdater(target=stored.id, values={"deleted": True})}

    result = await service.execute(_BulkUpdateAction(updaters=updaters))

    assert [r.entity_id for r in result.entity_results()] == [stored.id]
    repository.bulk_update.assert_awaited_once_with(updaters)


async def test_bulk_purge_answers_for_every_named_entity(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: EntityBulkPurgeService[_PresetData] = EntityBulkPurgeService(repository)
    purgers = {stored.id: _PresetPurger(target=stored.id)}

    result = await service.execute(_BulkPurgeAction(purgers=purgers))

    assert [r.entity_id for r in result.entity_results()] == [stored.id]
    repository.bulk_purge_entities.assert_awaited_once_with(purgers)


async def test_role_managed_create_forwards_the_action_s_creator(
    repository: MagicMock, stored: _PresetData, scope: ScopeRef
) -> None:
    service: RoleManagedEntityCreateService[_PresetData] = RoleManagedEntityCreateService(
        repository
    )
    creator = _PresetRoleManagedCreator()

    result = await service.execute(_RoleManagedCreateAction(scope=scope, creator=creator))

    assert result.data == stored
    repository.create_role_managed_entity.assert_awaited_once_with(creator)


async def test_role_managed_bulk_create_forwards_every_creator(
    repository: MagicMock, stored: _PresetData, scope: ScopeRef
) -> None:
    service: RoleManagedEntityBulkCreateService[_PresetData] = RoleManagedEntityBulkCreateService(
        repository
    )
    creators = [_PresetRoleManagedCreator(), _PresetRoleManagedCreator()]

    result = await service.execute(_RoleManagedBulkCreateAction(scope=scope, creators=creators))

    assert result.items == [stored]
    repository.bulk_create_role_managed_entities.assert_awaited_once_with(creators)


async def test_role_managed_upsert_forwards_the_action_s_upserter(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: RoleManagedEntityUpsertService[_PresetData] = RoleManagedEntityUpsertService(
        repository
    )
    upserter = _PresetRoleManagedUpserter(target=stored.id)

    result = await service.execute(_RoleManagedUpsertAction(target=stored.id, upserter=upserter))

    assert result.data == stored
    repository.upsert_role_managed_entity.assert_awaited_once_with(upserter)


async def test_global_upsert_forwards_the_action_s_upserter(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: GlobalUpsertService[_PresetData] = GlobalUpsertService(repository)
    upserter = _PresetGlobalUpserter(target=stored.id)

    result = await service.execute(_GlobalUpsertAction(upserter=upserter))

    assert result.data == stored
    repository.upsert_global_entity.assert_awaited_once_with(upserter)


async def test_global_bulk_create_forwards_every_creator(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: GlobalBulkCreateService[_PresetData] = GlobalBulkCreateService(repository)
    creators = [_PresetGlobalCreator(), _PresetGlobalCreator()]

    result = await service.execute(_BulkCreateGlobalAction(creators=creators))

    assert result.items == [stored]
    repository.bulk_create_global_entities.assert_awaited_once_with(creators)


async def test_field_bulk_create_forwards_owner_and_creators(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: FieldBulkCreateService[_PresetData] = FieldBulkCreateService(repository)
    owner = uuid.uuid4()
    creators = [_PresetFieldCreator(), _PresetFieldCreator()]

    result = await service.execute(_BulkCreateFieldAction(owner=owner, creators=creators))

    assert result.items == [stored]
    repository.bulk_create_field_entities.assert_awaited_once_with(owner, creators)


async def test_global_bulk_purge_answers_for_every_named_entity(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: GlobalBulkPurgeService[_PresetData] = GlobalBulkPurgeService(repository)
    purgers = {stored.id: _PresetGlobalPurger(target=stored.id)}

    result = await service.execute(_BulkPurgeGlobalAction(purgers=purgers))

    assert [r.entity_id for r in result.entity_results()] == [stored.id]
    repository.bulk_purge_global_entities.assert_awaited_once_with(purgers)


async def test_field_bulk_purge_answers_for_every_named_entity(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: FieldBulkPurgeService[_PresetData] = FieldBulkPurgeService(repository)
    purgers = {stored.id: _PresetFieldPurger(target=stored.id)}

    result = await service.execute(_BulkPurgeFieldAction(purgers=purgers))

    assert [r.entity_id for r in result.entity_results()] == [stored.id]
    repository.bulk_purge_field_entities.assert_awaited_once_with(purgers)


async def test_field_upsert_forwards_owner_and_upserter(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: FieldUpsertService[_PresetData] = FieldUpsertService(repository)
    owner = uuid.uuid4()
    upserter = _PresetFieldUpserter(target=stored.id)

    result = await service.execute(_FieldUpsertAction(owner=owner, upserter=upserter))

    assert result.data == stored
    repository.upsert_field_entity.assert_awaited_once_with(owner, upserter)


async def test_batch_update_names_what_it_wrote(
    repository: MagicMock, stored: _PresetData, scope: ScopeRef
) -> None:
    service: BatchUpdateService[_PresetData] = BatchUpdateService(repository)
    updater = _PresetBatchUpdater()
    search_scope = _ProjectScope(project_id=uuid.uuid4())

    result = await service.execute(
        _BatchUpdateAction(scope=scope, updater=updater, scopes=[search_scope])
    )

    assert result.entity_ids() == (stored.id,)
    repository.batch_update_in_scopes.assert_awaited_once_with([search_scope], updater)


async def test_batch_purge_names_what_it_removed(
    repository: MagicMock, stored: _PresetData, scope: ScopeRef
) -> None:
    service: BatchPurgeService[_PresetData] = BatchPurgeService(repository)
    purger = _PresetBatchPurger()
    search_scope = _ProjectScope(project_id=uuid.uuid4())

    result = await service.execute(
        _BatchPurgeAction(scope=scope, purger=purger, scopes=[search_scope])
    )

    assert result.entity_ids() == (stored.id,)
    repository.batch_purge_in_scopes.assert_awaited_once_with([search_scope], purger)


async def test_search_forwards_the_searcher_and_its_scopes(
    repository: MagicMock,
    stored: _PresetData,
    scope: ScopeRef,
    searcher: _PresetSearcher,
) -> None:
    service: SearchService[_PresetData] = SearchService(repository)
    project_scope = _ProjectScope(project_id=uuid.uuid4())

    result = await service.execute(
        _SearchAction(scope=scope, searcher=searcher, scopes=[project_scope])
    )

    assert result.items == [stored]
    assert result.total_count == 1
    assert result.has_next_page is False
    assert result.has_previous_page is True
    repository.search_in_scopes.assert_awaited_once_with([project_scope], searcher)


async def test_global_search_takes_no_scopes_at_all(
    repository: MagicMock, stored: _PresetData, searcher: _PresetSearcher
) -> None:
    # The unscoped read is a different service reached from a different action shape,
    # not the empty case of the scoped one.
    service: GlobalSearchService[_PresetData] = GlobalSearchService(repository)

    result = await service.execute(_GlobalSearchAction(searcher=searcher))

    assert result.items == [stored]
    repository.search_in_global.assert_awaited_once_with(searcher)
    repository.search_in_scopes.assert_not_awaited()


# =============================================================================
# The same services under the real processors — nothing else is needed to wire them.
#
# The processor is parameterized with the concrete action because the two axes stay
# independent: the service only knows the ops half, and only the domain knows that its
# action is both. Naming it here is what keeps a service from having to.
# =============================================================================


async def test_create_runs_under_the_scope_processor(
    repository: MagicMock, stored: _PresetData, scope: ScopeRef
) -> None:
    service: EntityCreateService[_PresetData] = EntityCreateService(repository)
    processor: ScopeActionProcessor[_CreateAction, CreatedEntityOpsResult[_PresetData]] = (
        ScopeActionProcessor(service.execute)
    )

    result = await processor.run(_CreateAction(scope=scope, creator=_PresetCreator()))

    # The created entity reaches the audit trail through the shared result.
    assert result.entity_ids() == (stored.id,)


async def test_search_names_what_it_read_under_the_scope_processor(
    repository: MagicMock, stored: _PresetData, scope: ScopeRef, searcher: _PresetSearcher
) -> None:
    service: SearchService[_PresetData] = SearchService(repository)
    processor: ScopeActionProcessor[_SearchAction, ScopedBatchOpsResult[_PresetData]] = (
        ScopeActionProcessor(service.execute)
    )

    result = await processor.run(_SearchAction(scope=scope, searcher=searcher))

    assert result.entity_ids() == (stored.id,)


async def test_batch_purge_runs_under_the_scope_processor(
    repository: MagicMock, stored: _PresetData, scope: ScopeRef
) -> None:
    service: BatchPurgeService[_PresetData] = BatchPurgeService(repository)
    processor: ScopeActionProcessor[_BatchPurgeAction, EntitiesOpsResult[_PresetData]] = (
        ScopeActionProcessor(service.execute)
    )

    result = await processor.run(
        _BatchPurgeAction(
            scope=scope,
            purger=_PresetBatchPurger(),
            scopes=[_ProjectScope(project_id=uuid.uuid4())],
        )
    )

    # Every entity the run removed reaches the audit trail.
    assert result.entity_ids() == (stored.id,)


async def test_update_runs_under_the_single_entity_processor(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: UpdateService[_PresetData] = UpdateService(repository)
    processor: SingleEntityActionProcessor[_UpdateAction, EntityOpsResult[_PresetData]] = (
        SingleEntityActionProcessor(service.execute)
    )

    result = await processor.run(
        _UpdateAction(target=stored.id, updater=_PresetUpdater(target=stored.id))
    )

    assert result.data == stored
