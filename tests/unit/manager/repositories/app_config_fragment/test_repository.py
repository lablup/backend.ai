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
from ai.backend.manager.errors.app_config import AppConfigFragmentNotFound
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
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination, Purger, Updater
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables

_DOMAIN_UUID = uuid.uuid4()
_DOMAIN_ID = str(_DOMAIN_UUID)
_USER_UUID = uuid.uuid4()
_USER_ID = str(_USER_UUID)
_OTHER_USER_ID = str(uuid.uuid4())


@pytest.fixture
async def repository(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[AppConfigFragmentRepository, None]:
    async with with_tables(database_connection, [AppConfigDefinitionRow, AppConfigFragmentRow]):
        # Seed the FK parent definitions referenced by the fragments under test.
        async with database_connection.begin_session() as db_sess:
            db_sess.add_all([
                AppConfigDefinitionRow(config_name=name) for name in ("theme", "menu")
            ])
        yield AppConfigFragmentRepository(DBOpsProvider(database_connection))


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


@pytest.fixture
async def existing_fragment(
    repository: AppConfigFragmentRepository,
) -> AppConfigFragmentData:
    """A single pre-created fragment for tests that need an existing row as precondition."""
    return await repository.create(
        _spec(scope_type=AppConfigScopeType.DOMAIN, scope_id=_DOMAIN_ID, config={"k": "v"})
    )


@pytest.fixture
async def seeded_fragments(
    repository: AppConfigFragmentRepository,
) -> list[AppConfigFragmentData]:
    """A fixed set of fragments (returned in creation order) for search/applicable tests.

    Covers every scope_type, two domains, two users, and two config_names so that search
    filters, rank ordering, and applicability can all derive their expectations from it.
    """
    specs = [
        _spec(config_name="theme", scope_type=AppConfigScopeType.PUBLIC, scope_id="public"),
        _spec(config_name="theme", scope_type=AppConfigScopeType.DOMAIN, scope_id=_DOMAIN_ID),
        _spec(config_name="theme", scope_type=AppConfigScopeType.DOMAIN, scope_id="other"),
        _spec(config_name="theme", scope_type=AppConfigScopeType.USER, scope_id=_USER_ID),
        _spec(config_name="theme", scope_type=AppConfigScopeType.USER, scope_id=_OTHER_USER_ID),
        _spec(config_name="menu", scope_type=AppConfigScopeType.PUBLIC, scope_id="public"),
    ]
    fragments: list[AppConfigFragmentData] = []
    for spec in specs:
        fragments.append(await repository.create(spec))
    return fragments


class TestCreateAndGet:
    async def test_create_then_get_by_id(self, repository: AppConfigFragmentRepository) -> None:
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
        existing_fragment: AppConfigFragmentData,
    ) -> None:
        with pytest.raises(UniqueConstraintViolationError):
            await repository.create(
                _spec(
                    config_name=existing_fragment.config_name,
                    scope_type=existing_fragment.scope_type,
                    scope_id=existing_fragment.scope_id,
                )
            )


class TestRankAssignment:
    async def test_rank_increases_per_config_name(
        self, repository: AppConfigFragmentRepository
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
        existing_fragment: AppConfigFragmentData,
    ) -> None:
        updated = await repository.update(
            Updater(
                spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2})),
                pk_value=existing_fragment.id,
            )
        )
        assert updated.config == {"b": 2}
        assert (await repository.get_by_id(existing_fragment.id)).config == {"b": 2}

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
        existing_fragment: AppConfigFragmentData,
    ) -> None:
        purged = await repository.purge(
            Purger(row_class=AppConfigFragmentRow, pk_value=existing_fragment.id)
        )
        assert purged.id == existing_fragment.id
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(existing_fragment.id)

    async def test_purge_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.purge(Purger(row_class=AppConfigFragmentRow, pk_value=_missing_id()))


class TestSearch:
    async def test_search_returns_all_and_paginates(
        self,
        repository: AppConfigFragmentRepository,
        seeded_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.search(
            BatchQuerier(pagination=OffsetPagination(limit=2, offset=0))
        )
        assert result.total_count == len(seeded_fragments)
        assert len(result.items) == 2
        assert result.has_next_page is True

    async def test_filter_by_scope_type(
        self,
        repository: AppConfigFragmentRepository,
        seeded_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[
                    AppConfigFragmentConditions.by_scope_type_equals(AppConfigScopeType.DOMAIN)
                ],
            )
        )
        expected = {f.id for f in seeded_fragments if f.scope_type is AppConfigScopeType.DOMAIN}
        assert {item.id for item in result.items} == expected

    async def test_filter_by_scope_id(
        self,
        repository: AppConfigFragmentRepository,
        seeded_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[AppConfigFragmentConditions.by_scope_id_equals(_USER_ID)],
            )
        )
        expected = {f.id for f in seeded_fragments if f.scope_id == _USER_ID}
        assert {item.id for item in result.items} == expected

    async def test_order_by_rank_desc(
        self,
        repository: AppConfigFragmentRepository,
        seeded_fragments: list[AppConfigFragmentData],
    ) -> None:
        # Rank is monotonic per config_name, so scope to one config_name for a total order.
        theme_fragments = [f for f in seeded_fragments if f.config_name == "theme"]
        result = await repository.search(
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
