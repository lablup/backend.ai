"""Tests for AppConfigFragmentRepository with real database operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
)
from ai.backend.manager.errors.app_config import (
    AppConfigFragmentNotFound,
    AppConfigFragmentWriteNotAllowed,
)
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.app_config_allow_list.conditions import AppConfigAllowListConditions
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
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
from ai.backend.manager.repositories.app_config_fragment.types import (
    DomainAppConfigFragmentSearchScope,
    UserAppConfigFragmentSearchScope,
)
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkConditionalCreator,
    BulkConditionalPurger,
    BulkConditionalUpdater,
    ConditionalCreator,
    ConditionalPurger,
    ConditionalUpdater,
    ExistsQuerier,
    OffsetPagination,
    Purger,
    Updater,
)
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables

_DOMAIN_UUID = uuid.uuid4()
_USER_UUID = uuid.uuid4()
_DOMAIN_ID = str(_DOMAIN_UUID)
_USER_ID = str(_USER_UUID)
_OTHER_USER_ID = str(uuid.uuid4())


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    # FK order: app_config_definitions (parent) before the allow-list and fragments (children).
    async with with_tables(
        database_connection,
        [AppConfigDefinitionRow, AppConfigAllowListRow, AppConfigFragmentRow],
    ):
        yield database_connection


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> AppConfigFragmentRepository:
    return AppConfigFragmentRepository(DBOpsProvider(database))


@pytest.fixture
async def theme_registered(database: ExtendedAsyncSAEngine) -> None:
    """Situation: ``theme`` is registered and allow-listed at every scope; no fragments yet."""
    async with database.begin_session() as db_sess:
        db_sess.add(AppConfigDefinitionRow(config_name="theme"))
        await db_sess.flush()
        db_sess.add_all([
            AppConfigAllowListRow(config_name="theme", scope_type=AppConfigScopeType.PUBLIC),
            AppConfigAllowListRow(config_name="theme", scope_type=AppConfigScopeType.DOMAIN),
            AppConfigAllowListRow(config_name="theme", scope_type=AppConfigScopeType.USER),
        ])
        await db_sess.flush()


@pytest.fixture
async def theme_defined_not_allow_listed(database: ExtendedAsyncSAEngine) -> None:
    """Situation: ``theme`` is registered but has no allow-list row (writes are gated)."""
    async with database.begin_session() as db_sess:
        db_sess.add(AppConfigDefinitionRow(config_name="theme"))
        await db_sess.flush()


@pytest.fixture
async def domain_scoped_fragment(database: ExtendedAsyncSAEngine) -> AppConfigFragmentData:
    """Situation: a pre-existing ``theme``/domain fragment, allow-listed at the domain scope."""
    async with database.begin_session() as db_sess:
        db_sess.add(AppConfigDefinitionRow(config_name="theme"))
        await db_sess.flush()
        db_sess.add(
            AppConfigAllowListRow(config_name="theme", scope_type=AppConfigScopeType.DOMAIN)
        )
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
async def fragment_not_allow_listed(database: ExtendedAsyncSAEngine) -> AppConfigFragmentData:
    """Situation: a ``theme``/domain fragment whose ``(config_name, scope)`` is NOT allow-listed.

    Models a row that survives after its allow-list entry was removed — writes must be gated.
    """
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
            ),
            ExistsQuerier(row_class=AppConfigAllowListRow),
        )
        fetched = await repository.get_by_id(created.id)
        assert fetched.id == created.id
        assert fetched.config_name == "theme"
        assert fetched.scope_type is AppConfigScopeType.PUBLIC
        assert fetched.config == {"theme": "dark"}

    async def test_get_by_id_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(AppConfigFragmentID(uuid.uuid4()))

    async def test_create_rejected_when_not_allow_listed(
        self, repository: AppConfigFragmentRepository, theme_defined_not_allow_listed: None
    ) -> None:
        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await repository.create(
                AppConfigFragmentCreatorSpec(
                    config_name="theme",
                    scope_type=AppConfigScopeType.PUBLIC,
                    scope_id="public",
                    config={"theme": "dark"},
                ),
                ExistsQuerier(row_class=AppConfigAllowListRow),
            )

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
                ),
                ExistsQuerier(row_class=AppConfigAllowListRow),
            )


class TestRankAssignment:
    async def test_rank_follows_scope_precedence(
        self, repository: AppConfigFragmentRepository, theme_registered: None
    ) -> None:
        # rank is derived from scope_type (public < domain < user), independent of
        # creation order, so a more specific scope overrides a broader one when merged.
        first = await repository.create(
            AppConfigFragmentCreatorSpec(
                config_name="theme",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="public",
                config={"k": "v"},
            ),
            ExistsQuerier(row_class=AppConfigAllowListRow),
        )
        second = await repository.create(
            AppConfigFragmentCreatorSpec(
                config_name="theme",
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_ID,
                config={"k": "v"},
            ),
            ExistsQuerier(row_class=AppConfigAllowListRow),
        )
        third = await repository.create(
            AppConfigFragmentCreatorSpec(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_ID,
                config={"k": "v"},
            ),
            ExistsQuerier(row_class=AppConfigAllowListRow),
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
            ),
            ExistsQuerier(row_class=AppConfigAllowListRow),
        )
        assert updated.config == {"b": 2}
        assert (await repository.get_by_id(domain_scoped_fragment.id)).config == {"b": 2}

    async def test_update_missing_raises(
        self, repository: AppConfigFragmentRepository, theme_registered: None
    ) -> None:
        # Writes are allow-listed (gate open), so a missing fragment surfaces as NotFound
        # rather than the write-gate rejection.
        missing_id = AppConfigFragmentID(uuid.uuid4())
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.update(
                Updater(
                    spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({})),
                    pk_value=missing_id,
                ),
                ExistsQuerier(row_class=AppConfigAllowListRow),
            )

    async def test_update_rejected_when_not_allow_listed(
        self,
        repository: AppConfigFragmentRepository,
        fragment_not_allow_listed: AppConfigFragmentData,
    ) -> None:
        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await repository.update(
                Updater(
                    spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"b": 2})),
                    pk_value=fragment_not_allow_listed.id,
                ),
                ExistsQuerier(row_class=AppConfigAllowListRow),
            )


class TestPurge:
    async def test_purge_removes_row(
        self,
        repository: AppConfigFragmentRepository,
        domain_scoped_fragment: AppConfigFragmentData,
    ) -> None:
        purged = await repository.purge(
            Purger(row_class=AppConfigFragmentRow, pk_value=domain_scoped_fragment.id),
            ExistsQuerier(row_class=AppConfigAllowListRow),
        )
        assert purged.id == domain_scoped_fragment.id
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(domain_scoped_fragment.id)

    async def test_purge_missing_raises(
        self, repository: AppConfigFragmentRepository, theme_registered: None
    ) -> None:
        # Writes are allow-listed (gate open), so a missing fragment surfaces as NotFound
        # rather than the write-gate rejection.
        missing_id = AppConfigFragmentID(uuid.uuid4())
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.purge(
                Purger(row_class=AppConfigFragmentRow, pk_value=missing_id),
                ExistsQuerier(row_class=AppConfigAllowListRow),
            )

    async def test_purge_rejected_when_not_allow_listed(
        self,
        repository: AppConfigFragmentRepository,
        fragment_not_allow_listed: AppConfigFragmentData,
    ) -> None:
        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await repository.purge(
                Purger(row_class=AppConfigFragmentRow, pk_value=fragment_not_allow_listed.id),
                ExistsQuerier(row_class=AppConfigAllowListRow),
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
    async def test_domain_scope_returns_only_that_domain(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.scoped_search(
            BatchQuerier(pagination=OffsetPagination(limit=10, offset=0)),
            [DomainAppConfigFragmentSearchScope(domain_id=DomainID(_DOMAIN_UUID))],
        )
        # Only domain-scoped fragments of that domain — not the other domain, public, or users.
        expected = {
            f.id
            for f in fragments_across_scopes
            if f.scope_type is AppConfigScopeType.DOMAIN and f.scope_id == _DOMAIN_ID
        }
        assert {item.id for item in result.items} == expected
        assert result.total_count == len(expected)

    async def test_user_scope_returns_only_that_user(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.scoped_search(
            BatchQuerier(pagination=OffsetPagination(limit=10, offset=0)),
            [UserAppConfigFragmentSearchScope(user_id=UserID(_USER_UUID))],
        )
        expected = {
            f.id
            for f in fragments_across_scopes
            if f.scope_type is AppConfigScopeType.USER and f.scope_id == _USER_ID
        }
        assert {item.id for item in result.items} == expected

    async def test_scopes_or_combined_across_domain_and_user(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.scoped_search(
            BatchQuerier(pagination=OffsetPagination(limit=10, offset=0)),
            [
                DomainAppConfigFragmentSearchScope(domain_id=DomainID(_DOMAIN_UUID)),
                UserAppConfigFragmentSearchScope(user_id=UserID(_USER_UUID)),
            ],
        )
        expected = {
            f.id
            for f in fragments_across_scopes
            if (f.scope_type is AppConfigScopeType.DOMAIN and f.scope_id == _DOMAIN_ID)
            or (f.scope_type is AppConfigScopeType.USER and f.scope_id == _USER_ID)
        }
        assert {item.id for item in result.items} == expected

    async def test_scoped_search_unknown_scope_returns_empty(
        self, repository: AppConfigFragmentRepository
    ) -> None:
        # Unconditional (no existence check): an unknown scope yields no rows, not an error.
        result = await repository.scoped_search(
            BatchQuerier(pagination=OffsetPagination(limit=10, offset=0)),
            [DomainAppConfigFragmentSearchScope(domain_id=DomainID(uuid.uuid4()))],
        )
        assert result.items == []


@pytest.fixture
async def menu_defined(database: ExtendedAsyncSAEngine, theme_registered: None) -> None:
    """``theme`` is allow-listed at every scope (theme_registered); ``menu`` is defined, NOT allow-listed."""
    async with database.begin_session() as db_sess:
        db_sess.add(AppConfigDefinitionRow(config_name="menu"))
        await db_sess.flush()


@pytest.fixture
async def two_fragments(database: ExtendedAsyncSAEngine) -> list[AppConfigFragmentData]:
    """A domain-scoped and a user-scoped ``theme`` fragment, both allow-listed."""
    async with database.begin_session() as db_sess:
        db_sess.add(AppConfigDefinitionRow(config_name="theme"))
        await db_sess.flush()
        db_sess.add_all([
            AppConfigAllowListRow(config_name="theme", scope_type=AppConfigScopeType.DOMAIN),
            AppConfigAllowListRow(config_name="theme", scope_type=AppConfigScopeType.USER),
        ])
        rows = [
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_ID,
                rank=100,
                config={"a": 1},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_ID,
                rank=200,
                config={"b": 2},
            ),
        ]
        db_sess.add_all(rows)
        await db_sess.flush()
        return [row.to_data() for row in rows]


class TestBulkCreate:
    async def test_all_created(
        self, repository: AppConfigFragmentRepository, theme_registered: None
    ) -> None:
        result = await repository.bulk_create(
            BulkConditionalCreator(
                specs=[
                    ConditionalCreator(
                        spec=AppConfigFragmentCreatorSpec(
                            config_name="theme",
                            scope_type=AppConfigScopeType.PUBLIC,
                            scope_id="public",
                            config={"a": 1},
                        ),
                        only_if=ExistsQuerier(row_class=AppConfigAllowListRow),
                    ),
                    ConditionalCreator(
                        spec=AppConfigFragmentCreatorSpec(
                            config_name="theme",
                            scope_type=AppConfigScopeType.DOMAIN,
                            scope_id=_DOMAIN_ID,
                            config={"b": 2},
                        ),
                        only_if=ExistsQuerier(row_class=AppConfigAllowListRow),
                    ),
                ]
            )
        )
        assert len(result.succeeded) == 2
        assert result.failed == []
        # rank follows scope precedence (public < domain), independent of insert order
        assert result.succeeded[0].rank < result.succeeded[1].rank
        for fragment in result.succeeded:
            assert (await repository.get_by_id(fragment.id)).id == fragment.id

    async def test_partial_when_one_not_allow_listed(
        self, repository: AppConfigFragmentRepository, menu_defined: None
    ) -> None:
        result = await repository.bulk_create(
            BulkConditionalCreator(
                specs=[
                    ConditionalCreator(
                        spec=AppConfigFragmentCreatorSpec(
                            config_name="theme",  # allow-listed
                            scope_type=AppConfigScopeType.DOMAIN,
                            scope_id=_DOMAIN_ID,
                            config={"a": 1},
                        ),
                        only_if=ExistsQuerier(
                            row_class=AppConfigAllowListRow,
                            conditions=[
                                AppConfigAllowListConditions.by_config_name_equals(
                                    StringMatchSpec("theme", case_insensitive=False, negated=False)
                                )
                            ],
                        ),
                    ),
                    ConditionalCreator(
                        spec=AppConfigFragmentCreatorSpec(
                            config_name="menu",  # defined but NOT allow-listed -> gate rejects
                            scope_type=AppConfigScopeType.PUBLIC,
                            scope_id="public",
                            config={"b": 2},
                        ),
                        only_if=ExistsQuerier(
                            row_class=AppConfigAllowListRow,
                            conditions=[
                                AppConfigAllowListConditions.by_config_name_equals(
                                    StringMatchSpec("menu", case_insensitive=False, negated=False)
                                )
                            ],
                        ),
                    ),
                ]
            )
        )
        # partial: the allow-listed theme fragment is created; the menu item (index 1) is rejected
        assert [f.config_name for f in result.succeeded] == ["theme"]
        assert [f.index for f in result.failed] == [1]
        # the created theme fragment persists (not rolled back with the rejected one)
        search = await repository.admin_search(
            BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        )
        assert {item.config_name for item in search.items} == {"theme"}


class TestBulkUpdate:
    async def test_all_updated(
        self,
        repository: AppConfigFragmentRepository,
        two_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.bulk_update(
            BulkConditionalUpdater(
                updaters=[
                    ConditionalUpdater(
                        updater=Updater(
                            spec=AppConfigFragmentUpdaterSpec(
                                config=OptionalState.update({"x": 1})
                            ),
                            pk_value=two_fragments[0].id,
                        ),
                        only_if=ExistsQuerier(row_class=AppConfigAllowListRow),
                    ),
                    ConditionalUpdater(
                        updater=Updater(
                            spec=AppConfigFragmentUpdaterSpec(
                                config=OptionalState.update({"y": 2})
                            ),
                            pk_value=two_fragments[1].id,
                        ),
                        only_if=ExistsQuerier(row_class=AppConfigAllowListRow),
                    ),
                ]
            )
        )
        assert [u.config for u in result.succeeded] == [{"x": 1}, {"y": 2}]
        assert result.failed == []
        assert (await repository.get_by_id(two_fragments[0].id)).config == {"x": 1}

    async def test_partial_when_one_missing(
        self,
        repository: AppConfigFragmentRepository,
        two_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.bulk_update(
            BulkConditionalUpdater(
                updaters=[
                    ConditionalUpdater(
                        updater=Updater(
                            spec=AppConfigFragmentUpdaterSpec(
                                config=OptionalState.update({"x": 1})
                            ),
                            pk_value=two_fragments[0].id,
                        ),
                        only_if=ExistsQuerier(row_class=AppConfigAllowListRow),
                    ),
                    ConditionalUpdater(
                        updater=Updater(
                            spec=AppConfigFragmentUpdaterSpec(
                                config=OptionalState.update({"z": 9})
                            ),
                            pk_value=AppConfigFragmentID(uuid.uuid4()),  # missing -> reported
                        ),
                        only_if=ExistsQuerier(row_class=AppConfigAllowListRow),
                    ),
                ]
            )
        )
        # partial: the existing fragment is updated; the missing one (index 1) is reported
        assert [u.config for u in result.succeeded] == [{"x": 1}]
        assert [f.index for f in result.failed] == [1]
        assert (await repository.get_by_id(two_fragments[0].id)).config == {"x": 1}


class TestBulkPurge:
    async def test_all_purged(
        self,
        repository: AppConfigFragmentRepository,
        two_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.bulk_purge(
            BulkConditionalPurger(
                purgers=[
                    ConditionalPurger(
                        purger=Purger(row_class=AppConfigFragmentRow, pk_value=fragment.id),
                        only_if=ExistsQuerier(row_class=AppConfigAllowListRow),
                    )
                    for fragment in two_fragments
                ]
            )
        )
        assert {p.id for p in result.succeeded} == {f.id for f in two_fragments}
        assert result.failed == []
        for fragment in two_fragments:
            with pytest.raises(AppConfigFragmentNotFound):
                await repository.get_by_id(fragment.id)

    async def test_partial_when_one_missing(
        self,
        repository: AppConfigFragmentRepository,
        two_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.bulk_purge(
            BulkConditionalPurger(
                purgers=[
                    ConditionalPurger(
                        purger=Purger(row_class=AppConfigFragmentRow, pk_value=two_fragments[0].id),
                        only_if=ExistsQuerier(row_class=AppConfigAllowListRow),
                    ),
                    ConditionalPurger(
                        purger=Purger(
                            row_class=AppConfigFragmentRow,
                            pk_value=AppConfigFragmentID(uuid.uuid4()),  # missing -> reported
                        ),
                        only_if=ExistsQuerier(row_class=AppConfigAllowListRow),
                    ),
                ]
            )
        )
        # partial: the existing fragment is purged; the missing one (index 1) is reported
        assert [p.id for p in result.succeeded] == [two_fragments[0].id]
        assert [f.index for f in result.failed] == [1]
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(two_fragments[0].id)
