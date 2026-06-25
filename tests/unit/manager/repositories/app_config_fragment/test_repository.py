"""Tests for AppConfigFragmentRepository with real database operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
)
from ai.backend.manager.errors.app_config import (
    AppConfigDefinitionNotFound,
    AppConfigFragmentNotFound,
)
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.orders import AppConfigFragmentOrders
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.types import ConfigNameSearchScope
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination, Purger, Updater
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables

_DOMAIN_ID = str(uuid.uuid4())
_USER_ID = str(uuid.uuid4())
_OTHER_USER_ID = str(uuid.uuid4())


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    # FK order: app_config_definitions (parent) before app_config_fragments (child).
    async with with_tables(database_connection, [AppConfigDefinitionRow, AppConfigFragmentRow]):
        yield database_connection


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> AppConfigFragmentRepository:
    return AppConfigFragmentRepository(DBOpsProvider(database))


@pytest.fixture
async def theme_registered(database: ExtendedAsyncSAEngine) -> None:
    """Situation: ``theme`` is registered (FK parent) but no fragments exist yet."""
    async with database.begin_session() as db_sess:
        db_sess.add(AppConfigDefinitionRow(config_name="theme"))
        await db_sess.flush()


@pytest.fixture
async def domain_scoped_fragment(database: ExtendedAsyncSAEngine) -> AppConfigFragmentData:
    """Situation: a single pre-existing ``theme``/domain fragment."""
    async with database.begin_session() as db_sess:
        db_sess.add(AppConfigDefinitionRow(config_name="theme"))
        await db_sess.flush()
        row = AppConfigFragmentRow(
            config_name="theme",
            scope_type=AppConfigScopeType.DOMAIN,
            scope_id=_DOMAIN_ID,
            rank=100,
            config={"k": "v"},
        )
        db_sess.add(row)
        await db_sess.flush()
        return row.to_data()


@pytest.fixture
async def fragments_across_scopes(database: ExtendedAsyncSAEngine) -> list[AppConfigFragmentData]:
    """Situation: fragments across every scope_type, two domains, two users, two config_names.

    Returned in creation order so search filters and rank ordering can derive their
    expectations from it.
    """
    async with database.begin_session() as db_sess:
        db_sess.add_all([
            AppConfigDefinitionRow(config_name="theme"),
            AppConfigDefinitionRow(config_name="menu"),
        ])
        await db_sess.flush()
        rows = [
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="public",
                rank=100,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_ID,
                rank=200,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id="other",
                rank=300,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_ID,
                rank=400,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_OTHER_USER_ID,
                rank=500,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="menu",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="public",
                rank=100,
                config={"k": "v"},
            ),
        ]
        db_sess.add_all(rows)
        await db_sess.flush()
        return [row.to_data() for row in rows]


class TestCreateAndGet:
    async def test_create_then_get_by_id(
        self, repository: AppConfigFragmentRepository, theme_registered: None
    ) -> None:
        created = await repository.create(
            AppConfigFragmentCreatorSpec(
                config_name="theme",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="public",
                config={"theme": "dark"},
            )
        )
        fetched = await repository.get_by_id(created.id)
        assert fetched.id == created.id
        assert fetched.config_name == "theme"
        assert fetched.scope_type is AppConfigScopeType.PUBLIC
        assert fetched.config == {"theme": "dark"}

    async def test_get_by_id_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(AppConfigFragmentID(uuid.uuid4()))

    async def test_unique_constraint_violation(
        self,
        repository: AppConfigFragmentRepository,
        domain_scoped_fragment: AppConfigFragmentData,
    ) -> None:
        with pytest.raises(UniqueConstraintViolationError):
            await repository.create(
                AppConfigFragmentCreatorSpec(
                    config_name=domain_scoped_fragment.config_name,
                    scope_type=domain_scoped_fragment.scope_type,
                    scope_id=domain_scoped_fragment.scope_id,
                    config={"k": "v"},
                )
            )


class TestRankAssignment:
    async def test_rank_increases_per_config_name(
        self, repository: AppConfigFragmentRepository, theme_registered: None
    ) -> None:
        first = await repository.create(
            AppConfigFragmentCreatorSpec(
                config_name="theme",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="public",
                config={"k": "v"},
            )
        )
        second = await repository.create(
            AppConfigFragmentCreatorSpec(
                config_name="theme",
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_ID,
                config={"k": "v"},
            )
        )
        third = await repository.create(
            AppConfigFragmentCreatorSpec(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_ID,
                config={"k": "v"},
            )
        )
        assert first.rank < second.rank < third.rank


class TestUpdate:
    async def test_update_replaces_config(
        self,
        repository: AppConfigFragmentRepository,
        domain_scoped_fragment: AppConfigFragmentData,
    ) -> None:
        updated = await repository.update(
            Updater(
                spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2})),
                pk_value=domain_scoped_fragment.id,
            )
        )
        assert updated.config == {"b": 2}
        assert (await repository.get_by_id(domain_scoped_fragment.id)).config == {"b": 2}

    async def test_update_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.update(
                Updater(
                    spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({})),
                    pk_value=AppConfigFragmentID(uuid.uuid4()),
                )
            )


class TestPurge:
    async def test_purge_removes_row(
        self,
        repository: AppConfigFragmentRepository,
        domain_scoped_fragment: AppConfigFragmentData,
    ) -> None:
        purged = await repository.purge(
            Purger(row_class=AppConfigFragmentRow, pk_value=domain_scoped_fragment.id)
        )
        assert purged.id == domain_scoped_fragment.id
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(domain_scoped_fragment.id)

    async def test_purge_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.purge(
                Purger(row_class=AppConfigFragmentRow, pk_value=AppConfigFragmentID(uuid.uuid4()))
            )


class TestSearch:
    async def test_search_returns_all_and_paginates(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(pagination=OffsetPagination(limit=2, offset=0))
        )
        assert result.total_count == len(fragments_across_scopes)
        assert len(result.items) == 2
        assert result.has_next_page is True

    async def test_filter_by_scope_type(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[
                    AppConfigFragmentConditions.by_scope_type_equals(AppConfigScopeType.DOMAIN)
                ],
            )
        )
        expected = {
            f.id for f in fragments_across_scopes if f.scope_type is AppConfigScopeType.DOMAIN
        }
        assert {item.id for item in result.items} == expected

    async def test_filter_by_scope_id(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[AppConfigFragmentConditions.by_scope_id_equals(_USER_ID)],
            )
        )
        expected = {f.id for f in fragments_across_scopes if f.scope_id == _USER_ID}
        assert {item.id for item in result.items} == expected

    async def test_order_by_rank_desc(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        # Rank is monotonic per config_name, so scope to one config_name for a total order.
        theme_fragments = [f for f in fragments_across_scopes if f.config_name == "theme"]
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[
                    AppConfigFragmentConditions.by_config_name_equals(
                        StringMatchSpec("theme", case_insensitive=False, negated=False)
                    )
                ],
                orders=[AppConfigFragmentOrders.rank(ascending=False)],
            )
        )
        expected = [f.id for f in sorted(theme_fragments, key=lambda f: f.rank, reverse=True)]
        assert [item.id for item in result.items] == expected


class TestScopedSearch:
    async def test_scoped_search_returns_only_that_config_name(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.scoped_search(
            BatchQuerier(pagination=OffsetPagination(limit=10, offset=0)),
            [ConfigNameSearchScope(config_name="theme")],
        )
        expected = {f.id for f in fragments_across_scopes if f.config_name == "theme"}
        assert {item.id for item in result.items} == expected
        assert result.total_count == len(expected)

    async def test_scoped_search_unregistered_config_name_raises(
        self, repository: AppConfigFragmentRepository
    ) -> None:
        with pytest.raises(AppConfigDefinitionNotFound):
            await repository.scoped_search(
                BatchQuerier(pagination=OffsetPagination(limit=10, offset=0)),
                [ConfigNameSearchScope(config_name="unregistered")],
            )
