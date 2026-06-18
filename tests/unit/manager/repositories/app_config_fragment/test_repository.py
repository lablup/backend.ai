"""Tests for AppConfigFragmentRepository with real database operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.app_config_fragment.types import (
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
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables

_DOMAIN_ID = "default"
_USER_ID = str(uuid.uuid4())
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
    config: dict | None = None,
) -> AppConfigFragmentCreatorSpec:
    return AppConfigFragmentCreatorSpec(
        config_name=config_name,
        scope_type=scope_type,
        scope_id=scope_id,
        config=config if config is not None else {"k": "v"},
    )


def _missing_id() -> AppConfigFragmentID:
    return AppConfigFragmentID(uuid.uuid4())


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
        self, repository: AppConfigFragmentRepository
    ) -> None:
        await repository.create(_spec(scope_type=AppConfigScopeType.DOMAIN, scope_id=_DOMAIN_ID))
        with pytest.raises(UniqueConstraintViolationError):
            await repository.create(
                _spec(scope_type=AppConfigScopeType.DOMAIN, scope_id=_DOMAIN_ID)
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
    async def test_update_replaces_config(self, repository: AppConfigFragmentRepository) -> None:
        created = await repository.create(_spec(config={"a": 1}))
        updated = await repository.update(
            created.id,
            AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2})),
        )
        assert updated.config == {"b": 2}
        assert (await repository.get_by_id(created.id)).config == {"b": 2}

    async def test_update_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.update(
                _missing_id(),
                AppConfigFragmentUpdaterSpec(config=OptionalState.update({})),
            )


class TestPurge:
    async def test_purge_removes_row(self, repository: AppConfigFragmentRepository) -> None:
        created = await repository.create(_spec())
        purged = await repository.purge(created.id)
        assert purged.id == created.id
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(created.id)

    async def test_purge_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.purge(_missing_id())


class TestSearch:
    async def test_search_returns_all_and_paginates(
        self, repository: AppConfigFragmentRepository
    ) -> None:
        await repository.create(_spec(scope_type=AppConfigScopeType.PUBLIC, scope_id="public"))
        await repository.create(_spec(scope_type=AppConfigScopeType.DOMAIN, scope_id=_DOMAIN_ID))
        await repository.create(_spec(scope_type=AppConfigScopeType.USER, scope_id=_USER_ID))
        result = await repository.search(
            BatchQuerier(pagination=OffsetPagination(limit=2, offset=0))
        )
        assert result.total_count == 3
        assert len(result.items) == 2
        assert result.has_next_page is True

    async def test_filter_by_scope_type(self, repository: AppConfigFragmentRepository) -> None:
        await repository.create(_spec(scope_type=AppConfigScopeType.PUBLIC, scope_id="public"))
        await repository.create(_spec(scope_type=AppConfigScopeType.DOMAIN, scope_id=_DOMAIN_ID))
        result = await repository.search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[
                    AppConfigFragmentConditions.by_scope_type_equals(AppConfigScopeType.DOMAIN)
                ],
            )
        )
        assert [item.scope_type for item in result.items] == [AppConfigScopeType.DOMAIN]

    async def test_filter_by_scope_id(self, repository: AppConfigFragmentRepository) -> None:
        await repository.create(_spec(scope_type=AppConfigScopeType.USER, scope_id=_USER_ID))
        await repository.create(_spec(scope_type=AppConfigScopeType.USER, scope_id=_OTHER_USER_ID))
        result = await repository.search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[AppConfigFragmentConditions.by_scope_id_equals(_USER_ID)],
            )
        )
        assert [item.scope_id for item in result.items] == [_USER_ID]

    async def test_order_by_rank_desc(self, repository: AppConfigFragmentRepository) -> None:
        created = [
            await repository.create(_spec(scope_type=AppConfigScopeType.PUBLIC, scope_id="public")),
            await repository.create(
                _spec(scope_type=AppConfigScopeType.DOMAIN, scope_id=_DOMAIN_ID)
            ),
            await repository.create(_spec(scope_type=AppConfigScopeType.USER, scope_id=_USER_ID)),
        ]
        result = await repository.search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                orders=[AppConfigFragmentOrders.rank(ascending=False)],
            )
        )
        expected = [f.id for f in sorted(created, key=lambda f: f.rank, reverse=True)]
        assert [item.id for item in result.items] == expected


class TestApplicableFragments:
    async def test_returns_only_applicable_in_rank_order(
        self, repository: AppConfigFragmentRepository
    ) -> None:
        public = await repository.create(
            _spec(config_name="theme", scope_type=AppConfigScopeType.PUBLIC, scope_id="public")
        )
        domain = await repository.create(
            _spec(config_name="theme", scope_type=AppConfigScopeType.DOMAIN, scope_id=_DOMAIN_ID)
        )
        user = await repository.create(
            _spec(config_name="theme", scope_type=AppConfigScopeType.USER, scope_id=_USER_ID)
        )
        # Non-applicable: another domain, another user, and a different config_name.
        await repository.create(
            _spec(config_name="theme", scope_type=AppConfigScopeType.DOMAIN, scope_id="other")
        )
        await repository.create(
            _spec(config_name="theme", scope_type=AppConfigScopeType.USER, scope_id=_OTHER_USER_ID)
        )
        await repository.create(
            _spec(config_name="menu", scope_type=AppConfigScopeType.PUBLIC, scope_id="public")
        )

        applicable = await repository.applicable_fragments(
            config_name="theme", domain_id=_DOMAIN_ID, user_id=_USER_ID
        )
        assert [f.id for f in applicable] == [public.id, domain.id, user.id]
