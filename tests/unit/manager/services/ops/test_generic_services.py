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
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role_preset import RolePresetEntityType, RolePresetID
from ai.backend.common.data.entity.types import (
    EntityData,
    EntityIdentifier,
    EntityType,
    FieldData,
    FieldIdentifier,
    FieldType,
)
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.ops.base import (
    BatchPurgeOpsAction,
    BatchUpdateOpsAction,
    EntityAtomicCreateOpsAction,
    EntityUpsertOpsAction,
    FieldAtomicCreateOpsAction,
    GlobalEntityAtomicCreateOpsAction,
    GlobalSearchOpsAction,
    PartialBulkUpdateOpsAction,
    RoleManagedEntityAtomicCreateOpsAction,
    RoleManagedEntityCreateOpsAction,
)
from ai.backend.manager.actions.v2.ops.result import (
    EntitiesOpsResult,
)
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.specs.creator import (
    EntityCreator,
    FieldCreator,
    GlobalEntityCreator,
    RoleManagedEntityCreator,
)
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.specs.purger import (
    EntityBatchPurger,
)
from ai.backend.manager.models.specs.searcher import Searcher, SearcherResult
from ai.backend.manager.models.specs.types import (
    BulkResultWithFailures,
    ConflictCheck,
    IntegrityErrorCheck,
)
from ai.backend.manager.models.specs.updater import (
    DataBatchUpdater,
    DataUpdater,
    GuardedDataUpdater,
)
from ai.backend.manager.models.specs.upserter import (
    EntityUpserter,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.ops.service import (
    BatchPurgeService,
    BatchUpdateService,
    EntityAtomicCreateService,
    EntityUpsertService,
    FieldAtomicCreateService,
    GlobalAtomicCreateService,
    GlobalSearchService,
    PartialBulkUpdateService,
    RoleManagedEntityAtomicCreateService,
    RoleManagedEntityCreateService,
)

_ENTITY_TYPE = RolePresetEntityType()


class _TestFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "test_field"

    @override
    @classmethod
    def description(cls) -> str:
        return "A field row of the test entity."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return RolePresetEntityType


_FIELD_TYPE = _TestFieldType()


class _FieldID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return _FIELD_TYPE


@dataclass(frozen=True)
class _PresetFieldData(FieldData):
    """What a field write returns; it names the entity owning the row."""

    id: _FieldID
    owner: _EntityID


class _EntityID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE


# =============================================================================
# The domain's own types: a `data/` value and its specs.
# =============================================================================


class _StubEntityID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFolderEntityType()


@dataclass(frozen=True)
class _PresetData(EntityData):
    """What the repository returns. Names itself because ``create`` has to report it."""

    id: EntityIdentifier
    name: str

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id


class _PresetCreator(EntityCreator[RolePresetRow, _PresetData]):
    @override
    def entity_id(self, row: RolePresetRow) -> EntityIdentifier:
        return _EntityID(row.id)

    @override
    def created_in(self, row: RolePresetRow) -> Collection[EntityIdentifier]:
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
    def entity_id(self, row: RolePresetRow) -> EntityIdentifier:
        return _EntityID(row.id)

    @override
    def created_in(self, row: RolePresetRow) -> Collection[EntityIdentifier]:
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
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RolePresetRow.id

    @override
    def target_id_value(self) -> EntityIdentifier:
        return _EntityID(self.target)

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
class _PresetBatchPurger(EntityBatchPurger[RolePresetRow, _PresetData]):
    @override
    def entity_id(self, row: RolePresetRow) -> RolePresetID:
        return RolePresetID(row.id)

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
    def entity_id(self, row: RolePresetRow) -> EntityIdentifier:
        return _EntityID(row.id)

    @override
    def created_in(self, row: RolePresetRow) -> Collection[EntityIdentifier]:
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
    def entity_id(self, row: RolePresetRow) -> RolePresetID:
        return RolePresetID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> RolePresetRow:
        return RolePresetRow()

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


class _PresetFieldCreator(FieldCreator[_EntityID, RolePresetRow, _PresetFieldData]):
    @override
    def field_id(self, row: RolePresetRow) -> _FieldID:
        return _FieldID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: uuid.UUID) -> RolePresetRow:
        return RolePresetRow()

    @override
    def to_data(self, row: RolePresetRow) -> _PresetFieldData:
        return _PresetFieldData(id=_FieldID(row.id), owner=_EntityID(row.id))


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
class _UpsertAction(BaseSingleEntityAction, EntityUpsertOpsAction[RolePresetRow, _PresetData]):
    """Declares itself an UPDATE: ``ActionOperationType`` has no upsert."""

    target: EntityIdentifier
    upserter: _PresetUpserter

    @override
    def to_upserter(self) -> EntityUpserter[RolePresetRow, _PresetData]:
        return self.upserter

    @override
    def entity_id(self) -> EntityIdentifier:
        return _StubEntityID(self.target)

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "upsert_role_preset"


@dataclass
class _BulkUpdateAction(BaseBulkAction, PartialBulkUpdateOpsAction[RolePresetRow, _PresetData]):
    updaters: dict[EntityIdentifier, _PresetUpdater]

    @override
    def to_updaters(
        self,
    ) -> Mapping[EntityIdentifier, GuardedDataUpdater[RolePresetRow, _PresetData]]:
        return self.updaters

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        # Read off the same mapping, so the two cannot drift.
        return tuple(self.updaters)

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "update_role_presets"


@dataclass
class _BulkCreateAction(BaseScopeAction, EntityAtomicCreateOpsAction[RolePresetRow, _PresetData]):
    scope: EntityIdentifier
    creators: list[_PresetCreator]

    @override
    def to_creators(self) -> Sequence[EntityCreator[RolePresetRow, _PresetData]]:
        return self.creators

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
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
class _BulkCreateGlobalAction(
    BaseGlobalAction, GlobalEntityAtomicCreateOpsAction[RolePresetRow, _PresetData]
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
class _BulkCreateFieldAction(
    BaseSingleEntityAction, FieldAtomicCreateOpsAction[_EntityID, RolePresetRow, _PresetFieldData]
):
    owner: uuid.UUID
    creators: list[_PresetFieldCreator]

    @override
    def to_creators(self) -> Sequence[FieldCreator[_EntityID, RolePresetRow, _PresetFieldData]]:
        return self.creators

    @override
    def owner_id(self) -> _EntityID:
        return _EntityID(self.owner)

    @override
    def entity_id(self) -> EntityIdentifier:
        return _StubEntityID(self.owner)

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "create_field_role_presets"


@dataclass
class _RoleManagedCreateAction(
    BaseScopeAction, RoleManagedEntityCreateOpsAction[RolePresetRow, _PresetData]
):
    scope: EntityIdentifier
    creator: _PresetRoleManagedCreator

    @override
    def to_creator(self) -> RoleManagedEntityCreator[RolePresetRow, _PresetData]:
        return self.creator

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
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
    BaseScopeAction, RoleManagedEntityAtomicCreateOpsAction[RolePresetRow, _PresetData]
):
    scope: EntityIdentifier
    creators: list[_PresetRoleManagedCreator]

    @override
    def to_creators(self) -> Sequence[RoleManagedEntityCreator[RolePresetRow, _PresetData]]:
        return self.creators

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
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
class _BatchUpdateAction(BaseScopeAction, BatchUpdateOpsAction[RolePresetRow, _PresetData]):
    scope: EntityIdentifier
    updater: _PresetBatchUpdater
    scopes: list[OperationScope] = field(default_factory=list)

    @override
    def to_batch_updater(self) -> DataBatchUpdater[RolePresetRow, _PresetData]:
        return self.updater

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.scopes

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
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
    scope: EntityIdentifier
    purger: _PresetBatchPurger
    scopes: list[OperationScope] = field(default_factory=list)

    @override
    def to_batch_purger(self) -> EntityBatchPurger[RolePresetRow, _PresetData]:
        return self.purger

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.scopes

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
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


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def stored() -> _PresetData:
    return _PresetData(id=_EntityID(uuid.uuid4()), name="default")


@pytest.fixture
def field_stored() -> _PresetFieldData:
    return _PresetFieldData(id=_FieldID(uuid.uuid4()), owner=_EntityID(uuid.uuid4()))


@pytest.fixture
def repository(stored: _PresetData) -> MagicMock:
    mock = MagicMock(spec=OpsRepository)
    for operation in (
        "get",
        "lookup",
        "create_entity",
        "create_role_managed_entity",
        "create_role_managed_global_entity",
        "upsert_field_entity",
        "update",
        "upsert_entity",
        "upsert_role_managed_entity",
        "purge_entity",
    ):
        setattr(mock, operation, AsyncMock(return_value=stored))
    for operation in (
        "atomic_create_entities",
        "atomic_create_role_managed_entities",
        "atomic_create_role_managed_global_entities",
        "atomic_create_global_entities",
        "atomic_create_field_entities",
        "batch_update_in_scopes",
        "batch_update_in_global",
        "batch_purge_entities_in_scopes",
        "batch_purge_entities_in_global",
    ):
        setattr(mock, operation, AsyncMock(return_value=[stored]))
    for operation in (
        "partial_bulk_update",
        "partial_bulk_purge_entities",
        "partial_bulk_purge_entities",
        "partial_bulk_purge_field_entities",
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
def scope() -> EntityIdentifier:
    return ProjectID(uuid.uuid4())


@pytest.fixture
def searcher() -> _PresetSearcher:
    return _PresetSearcher(pagination=OffsetPagination(offset=0, limit=20))


# =============================================================================
# The six operations, each wired with no domain service and no domain repository.
# =============================================================================


async def test_upsert_forwards_the_action_s_upserter(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: EntityUpsertService[_PresetData] = EntityUpsertService(repository)
    upserter = _PresetUpserter(target=stored.id)

    result = await service.execute(_UpsertAction(target=stored.id, upserter=upserter))

    assert result.data == stored
    repository.upsert_entity.assert_awaited_once_with(upserter)


async def test_atomic_create_forwards_every_creator(
    repository: MagicMock, stored: _PresetData, scope: EntityIdentifier
) -> None:
    service: EntityAtomicCreateService[_PresetData] = EntityAtomicCreateService(repository)
    creators = [_PresetCreator(), _PresetCreator()]

    result = await service.execute(_BulkCreateAction(scope=scope, creators=creators))

    assert result.items == [stored]
    repository.atomic_create_entities.assert_awaited_once_with(creators)


async def test_partial_bulk_update_answers_for_every_named_entity(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: PartialBulkUpdateService[_PresetData] = PartialBulkUpdateService(repository)
    updaters = {stored.id: _PresetUpdater(target=stored.id)}

    result = await service.execute(_BulkUpdateAction(updaters=updaters))

    assert list(result.values()) == [stored.id]
    repository.partial_bulk_update.assert_awaited_once_with(updaters)


async def test_role_managed_create_forwards_the_action_s_creator(
    repository: MagicMock, stored: _PresetData, scope: EntityIdentifier
) -> None:
    service: RoleManagedEntityCreateService[_PresetData] = RoleManagedEntityCreateService(
        repository
    )
    creator = _PresetRoleManagedCreator()

    result = await service.execute(_RoleManagedCreateAction(scope=scope, creator=creator))

    assert result.data == stored
    repository.create_role_managed_entity.assert_awaited_once_with(creator)


async def test_role_managed_atomic_create_forwards_every_creator(
    repository: MagicMock, stored: _PresetData, scope: EntityIdentifier
) -> None:
    service: RoleManagedEntityAtomicCreateService[_PresetData] = (
        RoleManagedEntityAtomicCreateService(repository)
    )
    creators = [_PresetRoleManagedCreator(), _PresetRoleManagedCreator()]

    result = await service.execute(_RoleManagedBulkCreateAction(scope=scope, creators=creators))

    assert result.items == [stored]
    repository.atomic_create_role_managed_entities.assert_awaited_once_with(creators)


async def test_global_atomic_create_forwards_every_creator(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: GlobalAtomicCreateService[_PresetData] = GlobalAtomicCreateService(repository)
    creators = [_PresetGlobalCreator(), _PresetGlobalCreator()]

    result = await service.execute(_BulkCreateGlobalAction(creators=creators))

    assert result.items == [stored]
    repository.atomic_create_global_entities.assert_awaited_once_with(creators)


async def test_field_atomic_create_forwards_owner_and_creators(
    repository: MagicMock, field_stored: _PresetFieldData
) -> None:
    service: FieldAtomicCreateService[_PresetFieldData] = FieldAtomicCreateService(repository)
    repository.atomic_create_field_entities.return_value = [field_stored]
    owner = uuid.uuid4()
    creators = [_PresetFieldCreator(), _PresetFieldCreator()]

    result = await service.execute(_BulkCreateFieldAction(owner=owner, creators=creators))

    assert result.items == [field_stored]
    repository.atomic_create_field_entities.assert_awaited_once_with(owner, creators)


async def test_batch_update_names_what_it_wrote(
    repository: MagicMock, stored: _PresetData, scope: EntityIdentifier
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
    repository: MagicMock, stored: _PresetData, scope: EntityIdentifier
) -> None:
    service: BatchPurgeService[_PresetData] = BatchPurgeService(repository)
    purger = _PresetBatchPurger()
    search_scope = _ProjectScope(project_id=uuid.uuid4())

    result = await service.execute(
        _BatchPurgeAction(scope=scope, purger=purger, scopes=[search_scope])
    )

    assert result.entity_ids() == (stored.id,)
    repository.batch_purge_entities_in_scopes.assert_awaited_once_with([search_scope], purger)


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


async def test_batch_purge_runs_under_the_scope_processor(
    repository: MagicMock, stored: _PresetData, scope: EntityIdentifier
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
