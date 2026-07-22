"""Tests for AppConfigAllowListRepository with real database operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID
from ai.backend.manager.data.app_config_allow_list.types import (
    AppConfigAllowListData,
)
from ai.backend.manager.errors.app_config import AppConfigAllowListNotFound
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.models.app_config_allow_list.conditions import (
    AppConfigAllowListConditions,
)
from ai.backend.manager.models.app_config_allow_list.orders import AppConfigAllowListOrders
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_allow_list.creators import (
    AppConfigAllowListCreatorSpec,
)
from ai.backend.manager.repositories.app_config_allow_list.repository import (
    AppConfigAllowListRepository,
)
from ai.backend.manager.repositories.app_config_allow_list.updaters import (
    AppConfigAllowListUpdaterSpec,
)
from ai.backend.manager.repositories.app_config_definition.creators import (
    AppConfigDefinitionCreatorSpec,
)
from ai.backend.manager.repositories.app_config_definition.repository import (
    AppConfigDefinitionRepository,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
    Purger,
    Updater,
)
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    # FK order: app_config_definitions (parent), then the allow-list, then the
    # fragments hanging off the allow-list (cascade tests need them).
    async with with_tables(
        database_connection,
        [AppConfigDefinitionRow, AppConfigAllowListRow, AppConfigFragmentRow],
    ):
        yield database_connection


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> AppConfigAllowListRepository:
    return AppConfigAllowListRepository(DBOpsProvider(database))


@pytest.fixture
def definition_repository(database: ExtendedAsyncSAEngine) -> AppConfigDefinitionRepository:
    return AppConfigDefinitionRepository(DBOpsProvider(database))


async def _register(definition_repository: AppConfigDefinitionRepository, config_name: str) -> None:
    """Seed the FK parent: register a config_name in app_config_definitions."""
    await definition_repository.create(
        Creator(spec=AppConfigDefinitionCreatorSpec(config_name=config_name))
    )


async def _create_entry(
    repository: AppConfigAllowListRepository,
    config_name: str,
    scope_type: AppConfigScopeType,
    rank: int | None = None,
) -> AppConfigAllowListData:
    return await repository.create(
        Creator(
            spec=AppConfigAllowListCreatorSpec(
                config_name=config_name, scope_type=scope_type, rank=rank
            )
        )
    )


def _missing_id() -> AppConfigAllowListID:
    return AppConfigAllowListID(uuid.uuid4())


@pytest.fixture
async def existing_entry(
    repository: AppConfigAllowListRepository,
    definition_repository: AppConfigDefinitionRepository,
) -> AppConfigAllowListData:
    await _register(definition_repository, "theme")
    return await _create_entry(repository, "theme", AppConfigScopeType.PUBLIC)


@pytest.fixture
async def seeded_entries(
    repository: AppConfigAllowListRepository,
    definition_repository: AppConfigDefinitionRepository,
) -> list[AppConfigAllowListData]:
    for config_name in ("theme", "menu"):
        await _register(definition_repository, config_name)
    entries: list[AppConfigAllowListData] = []
    for config_name, scope_type in (
        ("theme", AppConfigScopeType.PUBLIC),
        ("theme", AppConfigScopeType.DOMAIN),
        ("menu", AppConfigScopeType.USER),
    ):
        entries.append(await _create_entry(repository, config_name, scope_type))
    return entries


class TestCreateAndGet:
    async def test_create_then_get_by_id(
        self,
        repository: AppConfigAllowListRepository,
        definition_repository: AppConfigDefinitionRepository,
    ) -> None:
        await _register(definition_repository, "theme")
        created = await _create_entry(repository, "theme", AppConfigScopeType.PUBLIC)
        fetched = await repository.get_by_id(created.id)
        assert fetched.id == created.id
        assert fetched.config_name == "theme"
        assert fetched.scope_type is AppConfigScopeType.PUBLIC

    async def test_get_by_id_missing_raises(self, repository: AppConfigAllowListRepository) -> None:
        with pytest.raises(AppConfigAllowListNotFound):
            await repository.get_by_id(_missing_id())

    async def test_create_requires_registered_config_name(
        self, repository: AppConfigAllowListRepository
    ) -> None:
        # No app_config_definitions row for "unregistered" -> FK violation.
        with pytest.raises(ForeignKeyViolationError):
            await _create_entry(repository, "unregistered", AppConfigScopeType.PUBLIC)

    async def test_duplicate_config_name_scope_type_rejected(
        self,
        repository: AppConfigAllowListRepository,
        existing_entry: AppConfigAllowListData,
    ) -> None:
        with pytest.raises(UniqueConstraintViolationError):
            await _create_entry(repository, existing_entry.config_name, existing_entry.scope_type)


class TestRankAssignment:
    @pytest.mark.parametrize(
        ("scope_type", "expected_rank"),
        [
            (AppConfigScopeType.PUBLIC, 100),
            (AppConfigScopeType.DOMAIN, 200),
            (AppConfigScopeType.USER, 300),
        ],
    )
    async def test_rank_defaults_by_scope_type(
        self,
        repository: AppConfigAllowListRepository,
        definition_repository: AppConfigDefinitionRepository,
        scope_type: AppConfigScopeType,
        expected_rank: int,
    ) -> None:
        await _register(definition_repository, "theme")
        created = await _create_entry(repository, "theme", scope_type)
        assert created.rank == expected_rank

    async def test_explicit_rank_overrides_default(
        self,
        repository: AppConfigAllowListRepository,
        definition_repository: AppConfigDefinitionRepository,
    ) -> None:
        await _register(definition_repository, "theme")
        created = await _create_entry(repository, "theme", AppConfigScopeType.DOMAIN, rank=250)
        assert created.rank == 250
        assert (await repository.get_by_id(created.id)).rank == 250


class TestUpdate:
    async def test_update_changes_rank(
        self,
        repository: AppConfigAllowListRepository,
        existing_entry: AppConfigAllowListData,
    ) -> None:
        updated = await repository.update(
            Updater(
                spec=AppConfigAllowListUpdaterSpec(rank=OptionalState.update(250)),
                pk_value=existing_entry.id,
            )
        )
        assert updated.rank == 250
        assert (await repository.get_by_id(existing_entry.id)).rank == 250
        # identity fields are untouched
        assert updated.config_name == existing_entry.config_name
        assert updated.scope_type is existing_entry.scope_type

    async def test_update_missing_raises(self, repository: AppConfigAllowListRepository) -> None:
        with pytest.raises(AppConfigAllowListNotFound):
            await repository.update(
                Updater(
                    spec=AppConfigAllowListUpdaterSpec(rank=OptionalState.update(250)),
                    pk_value=_missing_id(),
                )
            )


class TestPurge:
    async def test_purge_removes_row(
        self,
        repository: AppConfigAllowListRepository,
        existing_entry: AppConfigAllowListData,
    ) -> None:
        purged = await repository.purge(
            Purger(row_class=AppConfigAllowListRow, pk_value=existing_entry.id)
        )
        assert purged.id == existing_entry.id
        with pytest.raises(AppConfigAllowListNotFound):
            await repository.get_by_id(existing_entry.id)

    async def test_purge_missing_raises(self, repository: AppConfigAllowListRepository) -> None:
        with pytest.raises(AppConfigAllowListNotFound):
            await repository.purge(Purger(row_class=AppConfigAllowListRow, pk_value=_missing_id()))

    async def test_purge_cascades_to_fragments(
        self,
        database: ExtendedAsyncSAEngine,
        repository: AppConfigAllowListRepository,
        existing_entry: AppConfigAllowListData,
    ) -> None:
        # existing_entry is ("theme", PUBLIC); a fragment under it must go with it.
        async with database.begin_session() as db_sess:
            db_sess.add(
                AppConfigFragmentRow(
                    config_name=existing_entry.config_name,
                    scope_type=existing_entry.scope_type,
                    scope_id=None,
                    config={"k": "v"},
                )
            )
            await db_sess.flush()

        await repository.purge(Purger(row_class=AppConfigAllowListRow, pk_value=existing_entry.id))

        async with database.begin_readonly_session() as db_sess:
            remaining = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AppConfigFragmentRow)
            )
        assert remaining == 0

    async def test_definition_purge_cascades_to_allow_list_and_fragments(
        self,
        database: ExtendedAsyncSAEngine,
        repository: AppConfigAllowListRepository,
        definition_repository: AppConfigDefinitionRepository,
    ) -> None:
        # Deleting the definition cascades to its allow-list entry and its fragment.
        definition = await definition_repository.create(
            Creator(spec=AppConfigDefinitionCreatorSpec(config_name="theme"))
        )
        entry = await _create_entry(repository, "theme", AppConfigScopeType.PUBLIC)
        async with database.begin_session() as db_sess:
            db_sess.add(
                AppConfigFragmentRow(
                    config_name=entry.config_name,
                    scope_type=entry.scope_type,
                    scope_id=None,
                    config={"k": "v"},
                )
            )
            await db_sess.flush()

        await definition_repository.purge(
            Purger(row_class=AppConfigDefinitionRow, pk_value=definition.id)
        )

        async with database.begin_readonly_session() as db_sess:
            remaining_entries = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AppConfigAllowListRow)
            )
            remaining_fragments = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AppConfigFragmentRow)
            )
        assert remaining_entries == 0
        assert remaining_fragments == 0


class TestAdminSearch:
    async def test_admin_search_returns_all_with_total_count(
        self,
        repository: AppConfigAllowListRepository,
        seeded_entries: list[AppConfigAllowListData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        )
        assert result.total_count == len(seeded_entries)
        assert {item.id for item in result.items} == {entry.id for entry in seeded_entries}

    async def test_admin_search_respects_pagination(
        self,
        repository: AppConfigAllowListRepository,
        seeded_entries: list[AppConfigAllowListData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(pagination=OffsetPagination(limit=2, offset=0))
        )
        assert result.total_count == len(seeded_entries)
        assert len(result.items) == 2
        assert result.has_next_page is True

    async def test_admin_search_filters_by_config_name(
        self,
        repository: AppConfigAllowListRepository,
        seeded_entries: list[AppConfigAllowListData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[
                    AppConfigAllowListConditions.by_config_name_equals(
                        StringMatchSpec("theme", case_insensitive=False, negated=False)
                    )
                ],
            )
        )
        expected = {entry.id for entry in seeded_entries if entry.config_name == "theme"}
        assert {item.id for item in result.items} == expected

    async def test_admin_search_filters_by_scope_type(
        self,
        repository: AppConfigAllowListRepository,
        seeded_entries: list[AppConfigAllowListData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[
                    AppConfigAllowListConditions.by_scope_type_equals(AppConfigScopeType.USER)
                ],
            )
        )
        expected = {
            entry.id for entry in seeded_entries if entry.scope_type is AppConfigScopeType.USER
        }
        assert {item.id for item in result.items} == expected

    async def test_admin_search_filters_by_scope_type_not_equals(
        self,
        repository: AppConfigAllowListRepository,
        seeded_entries: list[AppConfigAllowListData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[
                    AppConfigAllowListConditions.by_scope_type_not_equals(AppConfigScopeType.USER)
                ],
            )
        )
        expected = {
            entry.id for entry in seeded_entries if entry.scope_type is not AppConfigScopeType.USER
        }
        assert {item.id for item in result.items} == expected

    async def test_admin_search_orders_by_config_name_desc(
        self,
        repository: AppConfigAllowListRepository,
        seeded_entries: list[AppConfigAllowListData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                orders=[AppConfigAllowListOrders.config_name(ascending=False)],
            )
        )
        config_names = [item.config_name for item in result.items]
        assert config_names == sorted(config_names, reverse=True)

    async def test_admin_search_filters_by_created_at(
        self,
        repository: AppConfigAllowListRepository,
        seeded_entries: list[AppConfigAllowListData],
    ) -> None:
        target = seeded_entries[1]
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[AppConfigAllowListConditions.by_created_at_equals(target.created_at)],
            )
        )
        assert [item.id for item in result.items] == [target.id]

    async def test_admin_search_filters_by_updated_at(
        self,
        repository: AppConfigAllowListRepository,
        seeded_entries: list[AppConfigAllowListData],
    ) -> None:
        target = seeded_entries[1]
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[AppConfigAllowListConditions.by_updated_at_equals(target.updated_at)],
            )
        )
        assert [item.id for item in result.items] == [target.id]

    async def test_admin_search_orders_by_rank_asc(
        self,
        repository: AppConfigAllowListRepository,
        seeded_entries: list[AppConfigAllowListData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                orders=[AppConfigAllowListOrders.rank(ascending=True)],
            )
        )
        expected = [entry.id for entry in sorted(seeded_entries, key=lambda e: e.rank)]
        assert [item.id for item in result.items] == expected

    async def test_admin_search_orders_by_created_at(
        self,
        repository: AppConfigAllowListRepository,
        seeded_entries: list[AppConfigAllowListData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                orders=[AppConfigAllowListOrders.created_at(ascending=True)],
            )
        )
        expected = [entry.id for entry in sorted(seeded_entries, key=lambda e: e.created_at)]
        assert [item.id for item in result.items] == expected

    async def test_admin_search_cursor_forward(
        self,
        repository: AppConfigAllowListRepository,
        seeded_entries: list[AppConfigAllowListData],
    ) -> None:
        by_created_desc = sorted(seeded_entries, key=lambda e: e.created_at, reverse=True)
        cursor = by_created_desc[0].id
        result = await repository.admin_search(
            BatchQuerier(
                pagination=CursorForwardPagination(
                    first=10,
                    cursor_order=AppConfigAllowListOrders.created_at(ascending=False),
                    cursor_condition=AppConfigAllowListConditions.by_cursor_forward(str(cursor)),
                )
            )
        )
        assert [item.id for item in result.items] == [entry.id for entry in by_created_desc[1:]]

    async def test_admin_search_cursor_backward(
        self,
        repository: AppConfigAllowListRepository,
        seeded_entries: list[AppConfigAllowListData],
    ) -> None:
        by_created_asc = sorted(seeded_entries, key=lambda e: e.created_at)
        cursor = by_created_asc[0].id
        result = await repository.admin_search(
            BatchQuerier(
                pagination=CursorBackwardPagination(
                    last=10,
                    cursor_order=AppConfigAllowListOrders.created_at(ascending=True),
                    cursor_condition=AppConfigAllowListConditions.by_cursor_backward(str(cursor)),
                )
            )
        )
        assert {item.id for item in result.items} == {entry.id for entry in by_created_asc[1:]}
