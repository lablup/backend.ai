"""``OpsRepository`` runs a real domain's operations with no domain repository.

``role_preset`` is pass-through in all 11 of its operations, so it is what this drives.
Its existing specs already build the rows and name the targets; each one below adds a
single ``to_data`` and nothing else, which is the whole cost of moving a domain onto the
generic repository.

The last test carries that the whole way up: a search action reaches the database
through the generic service and the generic repository, and no file in between belongs
to the domain.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityData, EntityType, ScopeRef, ScopeType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.permission.types import ScopeType as RBACScopeType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.ops.base import SearchOpsAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.scopes import ExistenceCheck, SearchScope
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import DataCreator
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.base.purger import DataPurger
from ai.backend.manager.repositories.base.querier import DataQuerier
from ai.backend.manager.repositories.base.searcher import Searcher
from ai.backend.manager.repositories.base.updater import DataUpdater
from ai.backend.manager.repositories.base.upserter import DataUpserter
from ai.backend.manager.repositories.ops.base.provider import DBOpsProvider
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.role_preset.creators import RolePresetCreatorSpec
from ai.backend.manager.repositories.role_preset.purgers import RolePresetPurgerSpec
from ai.backend.manager.repositories.role_preset.updaters import (
    RolePresetDeletedFlagUpdaterSpec,
    RolePresetUpdaterSpec,
)
from ai.backend.manager.services.ops.service import SearchService
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables

# =============================================================================
# The domain's specs, each gaining one `to_data`.
#
# Subclassed here rather than edited in place so this demonstration changes no domain
# code; a domain adopting the generic repository would add the method to its own spec.
# =============================================================================


@dataclass
class _PresetCreator(RolePresetCreatorSpec, DataCreator[RolePresetRow, RolePresetData]):
    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()


@dataclass
class _PresetUpdater(RolePresetUpdaterSpec, DataUpdater[RolePresetRow, RolePresetData]):
    target: RolePresetID = RolePresetID(uuid.UUID(int=0))

    @override
    def pk_value(self) -> uuid.UUID:
        return self.target

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()


@dataclass
class _PresetDeleter(RolePresetDeletedFlagUpdaterSpec, DataUpdater[RolePresetRow, RolePresetData]):
    target: RolePresetID = RolePresetID(uuid.UUID(int=0))

    @override
    def pk_value(self) -> uuid.UUID:
        return self.target

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()


@dataclass
class _PresetPurger(RolePresetPurgerSpec, DataPurger[RolePresetRow, RolePresetData]):
    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()


@dataclass
class _PresetUpserter(DataUpserter[RolePresetRow, RolePresetData]):
    target: RolePresetID
    name: str

    @property
    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "id": self.target,
            "name": self.name,
            "scope_type": RBACScopeType.DOMAIN,
            "auto_assign": False,
            "deleted": False,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"name": self.name}

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()


@dataclass
class _PresetQuerier(DataQuerier[RolePresetRow, RolePresetData]):
    target: uuid.UUID

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.target

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return row.to_data()


@dataclass
class _PresetView(EntityData):
    """What the searcher yields.

    A local type only because ``RolePresetData`` has not adopted ``EntityData`` yet and
    this demonstration changes no domain code; adopting it is the one line a real domain
    adds to run searches through the generic service.
    """

    id: RolePresetID
    name: str

    @override
    def entity_id(self) -> EntityID:
        return self.id


@dataclass
class _PresetSearcher(Searcher[RolePresetRow, _PresetView]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RolePresetRow)

    @override
    def to_data(self, row: Any) -> _PresetView:
        preset_row: RolePresetRow = row.RolePresetRow
        return _PresetView(id=preset_row.id, name=preset_row.name)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, [RolePresetRow]):
        yield database_connection


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> OpsRepository[RolePresetData]:
    # The ops provider is the only thing it takes.
    return OpsRepository[RolePresetData](DBOpsProvider(database))


@pytest.fixture
def view_repository(database: ExtendedAsyncSAEngine) -> OpsRepository[_PresetView]:
    """The same generic repository, reading the entity as a lighter view."""
    return OpsRepository[_PresetView](DBOpsProvider(database))


@pytest.fixture
async def preset(repository: OpsRepository[RolePresetData]) -> RolePresetData:
    return await repository.create(_PresetCreator(name="default", scope_type=RBACScopeType.DOMAIN))


class TestCreate:
    async def test_create_returns_the_data_type(
        self, repository: OpsRepository[RolePresetData]
    ) -> None:
        created = await repository.create(
            _PresetCreator(name="analysts", scope_type=RBACScopeType.PROJECT)
        )

        assert isinstance(created, RolePresetData)
        assert created.name == "analysts"
        assert created.deleted is False

    async def test_created_row_is_readable_back(
        self, repository: OpsRepository[RolePresetData], preset: RolePresetData
    ) -> None:
        read_back = await repository.get(_PresetQuerier(target=preset.id))

        assert read_back.id == preset.id
        assert read_back.name == "default"


class TestGet:
    async def test_missing_row_raises(self, repository: OpsRepository[RolePresetData]) -> None:
        with pytest.raises(EntityNotFoundError):
            await repository.get(_PresetQuerier(target=uuid.uuid4()))


class TestUpdate:
    async def test_update_is_reflected(
        self, repository: OpsRepository[RolePresetData], preset: RolePresetData
    ) -> None:
        updated = await repository.update(
            _PresetUpdater(name=OptionalState.update("renamed"), target=preset.id)
        )

        assert updated.name == "renamed"
        read_back = await repository.get(_PresetQuerier(target=preset.id))
        assert read_back.name == "renamed"

    async def test_soft_delete_is_an_update(
        self, repository: OpsRepository[RolePresetData], preset: RolePresetData
    ) -> None:
        # What ``DeleteService`` runs: the domain's own deleted-flag updater, because
        # which column marks a row deleted is not something ops can know.
        deleted = await repository.update(_PresetDeleter(deleted=True, target=preset.id))

        assert deleted.deleted is True

    async def test_missing_row_raises(self, repository: OpsRepository[RolePresetData]) -> None:
        with pytest.raises(EntityNotFoundError):
            await repository.update(
                _PresetUpdater(name=OptionalState.update("x"), target=RolePresetID(uuid.uuid4()))
            )


class TestUpsert:
    async def test_upsert_inserts_when_absent(
        self, repository: OpsRepository[RolePresetData]
    ) -> None:
        target = RolePresetID(uuid.uuid4())

        upserted = await repository.upsert(_PresetUpserter(target=target, name="fresh"))

        assert upserted.id == target
        assert upserted.name == "fresh"

    async def test_upsert_updates_on_conflict(
        self, repository: OpsRepository[RolePresetData], preset: RolePresetData
    ) -> None:
        upserted = await repository.upsert(_PresetUpserter(target=preset.id, name="replaced"))

        assert upserted.id == preset.id
        assert upserted.name == "replaced"
        read_back = await repository.get(_PresetQuerier(target=preset.id))
        assert read_back.name == "replaced"


class TestPurge:
    async def test_purged_row_is_gone(
        self, repository: OpsRepository[RolePresetData], preset: RolePresetData
    ) -> None:
        purged = await repository.purge(_PresetPurger(preset_id=preset.id))

        assert purged.id == preset.id
        with pytest.raises(EntityNotFoundError):
            await repository.get(_PresetQuerier(target=preset.id))

    async def test_missing_row_raises(self, repository: OpsRepository[RolePresetData]) -> None:
        with pytest.raises(EntityNotFoundError):
            await repository.purge(_PresetPurger(preset_id=uuid.uuid4()))


# =============================================================================
# Search, and the whole stack above it.
# =============================================================================


@dataclass(frozen=True)
class _NamedScope(SearchScope):
    name: str

    @override
    def to_condition(self) -> QueryCondition:
        return lambda: RolePresetRow.name == self.name

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@dataclass
class _SearchPresetsAction(BaseScopeAction, SearchOpsAction[RolePresetRow, _PresetView]):
    """The only file a pass-through domain still writes: the action."""

    scope: ScopeRef
    scopes: tuple[SearchScope, ...] = ()

    @override
    def to_searcher(self) -> Searcher[RolePresetRow, _PresetView]:
        return _PresetSearcher(pagination=OffsetPagination(offset=0, limit=20))

    @override
    def search_scopes(self) -> Sequence[SearchScope]:
        return self.scopes

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.scope,)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType("role_preset")

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @classmethod
    @override
    def required_permission(cls) -> Permission:
        return Permission.READ


class TestSearch:
    async def test_global_search_returns_every_row(
        self, view_repository: OpsRepository[_PresetView], preset: RolePresetData
    ) -> None:
        result = await view_repository.search(
            _PresetSearcher(pagination=OffsetPagination(offset=0, limit=20)), scopes=()
        )

        assert result.total_count == 1
        assert result.items[0].id == preset.id

    async def test_scoped_search_filters(
        self,
        repository: OpsRepository[RolePresetData],
        view_repository: OpsRepository[_PresetView],
        preset: RolePresetData,
    ) -> None:
        await repository.create(_PresetCreator(name="other", scope_type=RBACScopeType.DOMAIN))

        result = await view_repository.search(
            _PresetSearcher(pagination=OffsetPagination(offset=0, limit=20)),
            scopes=[_NamedScope(name="default")],
        )

        assert [item.id for item in result.items] == [preset.id]


class TestFullStack:
    """Action to database with no domain service and no domain repository in between."""

    async def test_search_action_reaches_the_database(
        self, view_repository: OpsRepository[_PresetView], preset: RolePresetData
    ) -> None:
        service: SearchService[_PresetView] = SearchService(view_repository)
        processor: ScopeActionProcessor[_SearchPresetsAction, Any] = ScopeActionProcessor(
            service.execute
        )
        action = _SearchPresetsAction(
            scope=ScopeRef(scope_type=ScopeType("domain"), scope_id=uuid.uuid4())
        )

        result = await processor.run(action)

        assert [item.id for item in result.items] == [preset.id]
        assert result.total_count == 1
        # What the run reached reaches the audit trail; how much of it is recorded is
        # the audit policy's call.
        assert result.entity_ids() == (preset.id,)
