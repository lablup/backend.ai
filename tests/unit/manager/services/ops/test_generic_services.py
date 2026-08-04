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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, override
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.types import EntityData, EntityType, ScopeRef, ScopeType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction, LookupKey
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.base import (
    BatchPurgeOpsAction,
    BatchUpdateOpsAction,
    BulkCreateOpsAction,
    BulkPurgeOpsAction,
    BulkUpdateOpsAction,
    CreateOpsAction,
    GetOpsAction,
    LookupOpsAction,
    PurgeOpsAction,
    SearchOpsAction,
    UpdateOpsAction,
    UpsertOpsAction,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntitiesOpsResult,
    EntityOpsResult,
    LookupOpsResult,
)
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.scopes import ExistenceCheck, SearchScope
from ai.backend.manager.repositories.base.creator import DataCreator
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.base.purger import DataBatchPurger, DataPurger
from ai.backend.manager.repositories.base.querier import DataFinder, DataQuerier
from ai.backend.manager.repositories.base.searcher import Searcher, SearcherResult
from ai.backend.manager.repositories.base.types import BulkResultWithFailures, ConflictCheck
from ai.backend.manager.repositories.base.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.repositories.base.upserter import DataUpserter
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.ops.service import (
    BatchPurgeService,
    BatchUpdateService,
    BulkCreateService,
    BulkDeleteService,
    BulkPurgeService,
    BulkUpdateService,
    CreateService,
    DeleteService,
    GetService,
    LookupService,
    PurgeService,
    SearchService,
    UpdateService,
    UpsertService,
)

_ENTITY_TYPE = EntityType("role_preset")


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


class _PresetCreator(DataCreator[RolePresetRow, _PresetData]):
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

    @override
    def build_values(self) -> dict[str, Any]:
        return self.values

    @override
    def to_data(self, row: RolePresetRow) -> _PresetData:
        return _PresetData(id=row.id, name=row.name)


@dataclass
class _PresetPurger(DataPurger[RolePresetRow, _PresetData]):
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
class _PresetByName(DataFinder[RolePresetRow, _PresetData]):
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
class _PresetUpserter(DataUpserter[RolePresetRow, _PresetData]):
    target: uuid.UUID

    @property
    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

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
    def to_data(self, row: Any) -> _PresetData:
        preset_row: RolePresetRow = row.RolePresetRow
        return _PresetData(id=preset_row.id, name=preset_row.name)


@dataclass(frozen=True)
class _ProjectScope(SearchScope):
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


@dataclass
class _CreateAction(BaseScopeAction, CreateOpsAction[RolePresetRow, _PresetData]):
    scope: ScopeRef
    creator: _PresetCreator

    @override
    def to_creator(self) -> DataCreator[RolePresetRow, _PresetData]:
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


@dataclass
class _PurgeAction(BaseSingleEntityAction, PurgeOpsAction[RolePresetRow, _PresetData]):
    target: EntityID
    purger: _PresetPurger

    @override
    def to_purger(self) -> DataPurger[RolePresetRow, _PresetData]:
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


@dataclass
class _UpsertAction(BaseSingleEntityAction, UpsertOpsAction[RolePresetRow, _PresetData]):
    """Declares itself an UPDATE: ``ActionOperationType`` has no upsert."""

    target: EntityID
    upserter: _PresetUpserter

    @override
    def to_upserter(self) -> DataUpserter[RolePresetRow, _PresetData]:
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

    finder: _PresetByName

    @override
    def to_finder(self) -> DataFinder[RolePresetRow, _PresetData]:
        return self.finder

    @override
    def lookup_key(self) -> LookupKey:
        return _NameKey(name=self.finder.name)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE


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


@dataclass
class _BulkPurgeAction(BaseBulkAction, BulkPurgeOpsAction[RolePresetRow, _PresetData]):
    purgers: dict[EntityID, _PresetPurger]

    @override
    def to_purgers(self) -> Mapping[EntityID, DataPurger[RolePresetRow, _PresetData]]:
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


@dataclass
class _BulkCreateAction(BaseScopeAction, BulkCreateOpsAction[RolePresetRow, _PresetData]):
    scope: ScopeRef
    creators: list[_PresetCreator]

    @override
    def to_creators(self) -> Sequence[DataCreator[RolePresetRow, _PresetData]]:
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


@dataclass
class _BatchUpdateAction(BaseScopeAction, BatchUpdateOpsAction[RolePresetRow, _PresetData]):
    scope: ScopeRef
    updater: _PresetBatchUpdater

    @override
    def to_batch_updater(self) -> DataBatchUpdater[RolePresetRow, _PresetData]:
        return self.updater

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


@dataclass
class _BatchPurgeAction(BaseScopeAction, BatchPurgeOpsAction[RolePresetRow, _PresetData]):
    scope: ScopeRef
    purger: _PresetBatchPurger

    @override
    def to_batch_purger(self) -> DataBatchPurger[RolePresetRow, _PresetData]:
        return self.purger

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


@dataclass
class _SearchAction(BaseScopeAction, SearchOpsAction[RolePresetRow, _PresetData]):
    scope: ScopeRef
    searcher: _PresetSearcher
    scopes: list[SearchScope] = field(default_factory=list)

    @override
    def to_searcher(self) -> Searcher[RolePresetRow, _PresetData]:
        return self.searcher

    @override
    def search_scopes(self) -> Sequence[SearchScope]:
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


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def stored() -> _PresetData:
    return _PresetData(id=uuid.uuid4(), name="default")


@pytest.fixture
def repository(stored: _PresetData) -> MagicMock:
    mock = MagicMock(spec=OpsRepository)
    for operation in ("get", "find", "search", "create", "update", "upsert", "purge"):
        setattr(mock, operation, AsyncMock(return_value=stored))
    for operation in ("bulk_create", "batch_update", "batch_purge"):
        setattr(mock, operation, AsyncMock(return_value=[stored]))
    for operation in ("bulk_update", "bulk_purge"):
        setattr(
            mock,
            operation,
            AsyncMock(
                return_value=BulkResultWithFailures(successes={stored.id: stored}, errors={})
            ),
        )
    mock.search = AsyncMock(
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
    )


@pytest.fixture
def scope() -> ScopeRef:
    return ScopeRef(scope_type=ScopeType("project"), scope_id=uuid.uuid4())


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
    service: CreateService[_PresetData] = CreateService(repository)
    creator = _PresetCreator()

    result = await service.execute(_CreateAction(scope=scope, creator=creator))

    assert result.data == stored
    repository.create.assert_awaited_once_with(creator)


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
    service: UpsertService[_PresetData] = UpsertService(repository)
    upserter = _PresetUpserter(target=stored.id)

    result = await service.execute(_UpsertAction(target=stored.id, upserter=upserter))

    assert result.data == stored
    repository.upsert.assert_awaited_once_with(upserter)


async def test_purge_forwards_the_action_s_purger(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: PurgeService[_PresetData] = PurgeService(repository)
    purger = _PresetPurger(target=stored.id)

    result = await service.execute(_PurgeAction(target=stored.id, purger=purger))

    assert result.data == stored
    repository.purge.assert_awaited_once_with(purger)


async def test_lookup_forwards_the_action_s_finder(
    repository: MagicMock, stored: _PresetData
) -> None:
    service: LookupService[_PresetData] = LookupService(repository)
    finder = _PresetByName(name="default")

    result = await service.execute(_LookupAction(finder=finder))

    assert result.data == stored
    assert result.resolved_entity_id() == stored.id
    repository.find.assert_awaited_once_with(finder)


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
        result = await processor.run(_LookupAction(finder=_PresetByName(name="default")))

    # The id the key resolved to is what reaches the audit trail.
    assert result.resolved_entity_id() == stored.id


async def test_bulk_create_forwards_every_creator(
    repository: MagicMock, stored: _PresetData, scope: ScopeRef
) -> None:
    service: BulkCreateService[_PresetData] = BulkCreateService(repository)
    creators = [_PresetCreator(), _PresetCreator()]

    result = await service.execute(_BulkCreateAction(scope=scope, creators=creators))

    assert result.items == [stored]
    repository.bulk_create.assert_awaited_once_with(creators)


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
    service: BulkPurgeService[_PresetData] = BulkPurgeService(repository)
    purgers = {stored.id: _PresetPurger(target=stored.id)}

    result = await service.execute(_BulkPurgeAction(purgers=purgers))

    assert [r.entity_id for r in result.entity_results()] == [stored.id]
    repository.bulk_purge.assert_awaited_once_with(purgers)


async def test_batch_update_names_what_it_wrote(
    repository: MagicMock, stored: _PresetData, scope: ScopeRef
) -> None:
    service: BatchUpdateService[_PresetData] = BatchUpdateService(repository)
    updater = _PresetBatchUpdater()

    result = await service.execute(_BatchUpdateAction(scope=scope, updater=updater))

    assert result.entity_ids() == (stored.id,)
    repository.batch_update.assert_awaited_once_with(updater)


async def test_batch_purge_names_what_it_removed(
    repository: MagicMock, stored: _PresetData, scope: ScopeRef
) -> None:
    service: BatchPurgeService[_PresetData] = BatchPurgeService(repository)
    purger = _PresetBatchPurger()

    result = await service.execute(_BatchPurgeAction(scope=scope, purger=purger))

    assert result.entity_ids() == (stored.id,)
    repository.batch_purge.assert_awaited_once_with(purger)


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
    repository.search.assert_awaited_once_with(searcher, [project_scope])


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
    service: CreateService[_PresetData] = CreateService(repository)
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
    processor: ScopeActionProcessor[_SearchAction, BatchOpsResult[_PresetData]] = (
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

    result = await processor.run(_BatchPurgeAction(scope=scope, purger=_PresetBatchPurger()))

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
