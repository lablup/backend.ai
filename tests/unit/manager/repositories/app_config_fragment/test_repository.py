"""Tests for AppConfigFragmentRepository with real database operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigScopeType,
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


async def _seed_definition(database: ExtendedAsyncSAEngine, config_name: str) -> None:
    """Insert the FK parent definition row directly."""
    async with database.begin_session() as db_sess:
        db_sess.add(AppConfigDefinitionRow(config_name=config_name))
        await db_sess.flush()


async def _seed_fragment(
    database: ExtendedAsyncSAEngine,
    *,
    config_name: str,
    scope_type: AppConfigScopeType,
    scope_id: str,
    rank: int,
    config: dict[str, Any] | None = None,
) -> AppConfigFragmentData:
    """Insert a fragment row directly (bypassing the repository under test)."""
    async with database.begin_session() as db_sess:
        row = AppConfigFragmentRow(
            config_name=config_name,
            scope_type=scope_type,
            scope_id=scope_id,
            rank=rank,
            config=config if config is not None else {"k": "v"},
        )
        db_sess.add(row)
        await db_sess.flush()
        return row.to_data()


def _spec(
    config_name: str = "theme",
    scope_type: AppConfigScopeType = AppConfigScopeType.PUBLIC,
    scope_id: str = "public",
    config: dict[str, Any] | None = None,
) -> AppConfigFragmentCreatorSpec:
    return AppConfigFragmentCreatorSpec(
        config_name=config_name,
        scope_type=scope_type,
        scope_id=scope_id,
        config=config if config is not None else {"k": "v"},
    )


def _missing_id() -> AppConfigFragmentID:
    return AppConfigFragmentID(uuid.uuid4())


# --- FK parent definitions (seeded directly) ---


@pytest.fixture
async def registered_theme(database: ExtendedAsyncSAEngine) -> None:
    await _seed_definition(database, "theme")


@pytest.fixture
async def registered_menu(database: ExtendedAsyncSAEngine) -> None:
    await _seed_definition(database, "menu")


# --- Fragment inputs (each seeded directly; rank assigned explicitly) ---


@pytest.fixture
async def theme_public(
    database: ExtendedAsyncSAEngine, registered_theme: None
) -> AppConfigFragmentData:
    return await _seed_fragment(
        database,
        config_name="theme",
        scope_type=AppConfigScopeType.PUBLIC,
        scope_id="public",
        rank=100,
    )


@pytest.fixture
async def theme_domain(
    database: ExtendedAsyncSAEngine, registered_theme: None
) -> AppConfigFragmentData:
    return await _seed_fragment(
        database,
        config_name="theme",
        scope_type=AppConfigScopeType.DOMAIN,
        scope_id=_DOMAIN_ID,
        rank=200,
    )


@pytest.fixture
async def theme_domain_other(
    database: ExtendedAsyncSAEngine, registered_theme: None
) -> AppConfigFragmentData:
    return await _seed_fragment(
        database,
        config_name="theme",
        scope_type=AppConfigScopeType.DOMAIN,
        scope_id="other",
        rank=300,
    )


@pytest.fixture
async def theme_user(
    database: ExtendedAsyncSAEngine, registered_theme: None
) -> AppConfigFragmentData:
    return await _seed_fragment(
        database,
        config_name="theme",
        scope_type=AppConfigScopeType.USER,
        scope_id=_USER_ID,
        rank=400,
    )


@pytest.fixture
async def theme_user_other(
    database: ExtendedAsyncSAEngine, registered_theme: None
) -> AppConfigFragmentData:
    return await _seed_fragment(
        database,
        config_name="theme",
        scope_type=AppConfigScopeType.USER,
        scope_id=_OTHER_USER_ID,
        rank=500,
    )


@pytest.fixture
async def menu_public(
    database: ExtendedAsyncSAEngine, registered_menu: None
) -> AppConfigFragmentData:
    return await _seed_fragment(
        database,
        config_name="menu",
        scope_type=AppConfigScopeType.PUBLIC,
        scope_id="public",
        rank=100,
    )


class TestCreateAndGet:
    async def test_create_then_get_by_id(
        self, repository: AppConfigFragmentRepository, registered_theme: None
    ) -> None:
        created = await repository.create(_spec(config={"theme": "dark"}))
        fetched = await repository.get_by_id(created.id)
        assert fetched.id == created.id
        assert fetched.config_name == "theme"
        assert fetched.scope_type is AppConfigScopeType.PUBLIC
        assert fetched.config == {"theme": "dark"}

    async def test_get_by_id_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(_missing_id())

    async def test_unique_constraint_violation(
        self,
        repository: AppConfigFragmentRepository,
        theme_domain: AppConfigFragmentData,
    ) -> None:
        with pytest.raises(UniqueConstraintViolationError):
            await repository.create(
                _spec(
                    config_name=theme_domain.config_name,
                    scope_type=theme_domain.scope_type,
                    scope_id=theme_domain.scope_id,
                )
            )


class TestRankAssignment:
    async def test_rank_increases_per_config_name(
        self, repository: AppConfigFragmentRepository, registered_theme: None
    ) -> None:
        first = await repository.create(
            _spec(scope_type=AppConfigScopeType.PUBLIC, scope_id="public")
        )
        second = await repository.create(
            _spec(scope_type=AppConfigScopeType.DOMAIN, scope_id=_DOMAIN_ID)
        )
        third = await repository.create(
            _spec(scope_type=AppConfigScopeType.USER, scope_id=_USER_ID)
        )
        assert first.rank < second.rank < third.rank


class TestUpdate:
    async def test_update_replaces_config(
        self,
        repository: AppConfigFragmentRepository,
        theme_domain: AppConfigFragmentData,
    ) -> None:
        updated = await repository.update(
            Updater(
                spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2})),
                pk_value=theme_domain.id,
            )
        )
        assert updated.config == {"b": 2}
        assert (await repository.get_by_id(theme_domain.id)).config == {"b": 2}

    async def test_update_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.update(
                Updater(
                    spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({})),
                    pk_value=_missing_id(),
                )
            )


class TestPurge:
    async def test_purge_removes_row(
        self,
        repository: AppConfigFragmentRepository,
        theme_domain: AppConfigFragmentData,
    ) -> None:
        purged = await repository.purge(
            Purger(row_class=AppConfigFragmentRow, pk_value=theme_domain.id)
        )
        assert purged.id == theme_domain.id
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(theme_domain.id)

    async def test_purge_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.purge(Purger(row_class=AppConfigFragmentRow, pk_value=_missing_id()))


class TestSearch:
    async def test_search_returns_all_and_paginates(
        self,
        repository: AppConfigFragmentRepository,
        theme_public: AppConfigFragmentData,
        theme_domain: AppConfigFragmentData,
        theme_domain_other: AppConfigFragmentData,
        theme_user: AppConfigFragmentData,
        theme_user_other: AppConfigFragmentData,
        menu_public: AppConfigFragmentData,
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(pagination=OffsetPagination(limit=2, offset=0))
        )
        assert result.total_count == 6
        assert len(result.items) == 2
        assert result.has_next_page is True

    async def test_filter_by_scope_type(
        self,
        repository: AppConfigFragmentRepository,
        theme_public: AppConfigFragmentData,
        theme_domain: AppConfigFragmentData,
        theme_domain_other: AppConfigFragmentData,
        theme_user: AppConfigFragmentData,
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[
                    AppConfigFragmentConditions.by_scope_type_equals(AppConfigScopeType.DOMAIN)
                ],
            )
        )
        assert {item.id for item in result.items} == {theme_domain.id, theme_domain_other.id}

    async def test_filter_by_scope_id(
        self,
        repository: AppConfigFragmentRepository,
        theme_user: AppConfigFragmentData,
        theme_user_other: AppConfigFragmentData,
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[AppConfigFragmentConditions.by_scope_id_equals(_USER_ID)],
            )
        )
        assert {item.id for item in result.items} == {theme_user.id}

    async def test_order_by_rank_desc(
        self,
        repository: AppConfigFragmentRepository,
        theme_public: AppConfigFragmentData,
        theme_domain: AppConfigFragmentData,
        theme_domain_other: AppConfigFragmentData,
        theme_user: AppConfigFragmentData,
        theme_user_other: AppConfigFragmentData,
    ) -> None:
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
        assert [item.id for item in result.items] == [
            theme_user_other.id,
            theme_user.id,
            theme_domain_other.id,
            theme_domain.id,
            theme_public.id,
        ]


class TestScopedSearch:
    async def test_scoped_search_returns_only_that_config_name(
        self,
        repository: AppConfigFragmentRepository,
        theme_public: AppConfigFragmentData,
        theme_domain: AppConfigFragmentData,
        theme_user: AppConfigFragmentData,
        menu_public: AppConfigFragmentData,
    ) -> None:
        result = await repository.scoped_search(
            BatchQuerier(pagination=OffsetPagination(limit=10, offset=0)),
            [ConfigNameSearchScope(config_name="theme")],
        )
        assert {item.id for item in result.items} == {
            theme_public.id,
            theme_domain.id,
            theme_user.id,
        }
        assert result.total_count == 3

    async def test_scoped_search_unregistered_config_name_raises(
        self, repository: AppConfigFragmentRepository
    ) -> None:
        with pytest.raises(AppConfigDefinitionNotFound):
            await repository.scoped_search(
                BatchQuerier(pagination=OffsetPagination(limit=10, offset=0)),
                [ConfigNameSearchScope(config_name="unregistered")],
            )
