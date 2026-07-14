"""Tests for AppConfigFragmentRepository with real database operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

import pytest
import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.permission.types import EntityType, ScopeType
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
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.purgers import (
    AppConfigFragmentPurgerSpec,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigScopeArguments,
    DomainAppConfigFragmentSearchScope,
    UserAppConfigFragmentSearchScope,
)
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkCreator,
    OffsetPagination,
    Purger,
    Updater,
)
from ai.backend.manager.repositories.ops.rbac.provider import RBACOpsProvider
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
    async with with_tables(
        database_connection,
        [
            AppConfigDefinitionRow,
            AppConfigAllowListRow,
            AppConfigFragmentRow,
            AssociationScopesEntitiesRow,
            RoleRow,
            PermissionRow,
        ],
    ):
        yield database_connection


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> AppConfigFragmentRepository:
    return AppConfigFragmentRepository(RBACOpsProvider(database))


def _allow_list_row(config_name: str, scope_type: AppConfigScopeType) -> AppConfigAllowListRow:
    return AppConfigAllowListRow(
        config_name=config_name,
        scope_type=scope_type,
        rank=scope_type.default_rank(),
    )


@pytest.fixture
async def theme_registered(database: ExtendedAsyncSAEngine) -> None:
    """Situation: ``theme`` is registered and allow-listed at every scope; no fragments yet."""
    async with database.begin_session() as db_sess:
        db_sess.add(AppConfigDefinitionRow(config_name="theme"))
        await db_sess.flush()
        db_sess.add_all([
            _allow_list_row("theme", AppConfigScopeType.PUBLIC),
            _allow_list_row("theme", AppConfigScopeType.DOMAIN),
            _allow_list_row("theme", AppConfigScopeType.USER),
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
        db_sess.add(_allow_list_row("theme", AppConfigScopeType.DOMAIN))
        await db_sess.flush()
        row = AppConfigFragmentRow(
            config_name="theme",
            scope_type=AppConfigScopeType.DOMAIN,
            scope_id=_DOMAIN_ID,
            config={"k": "v"},
        )
        db_sess.add(row)
        await db_sess.flush()
        return row.to_data()


@pytest.fixture
async def fragments_across_scopes(database: ExtendedAsyncSAEngine) -> list[AppConfigFragmentData]:
    """Situation: fragments across every scope_type, two domains, two users, two config_names.

    Returned in creation order so search filters can derive their expectations from it.
    """
    async with database.begin_session() as db_sess:
        db_sess.add_all([
            AppConfigDefinitionRow(config_name="theme"),
            AppConfigDefinitionRow(config_name="menu"),
        ])
        await db_sess.flush()
        db_sess.add_all([
            _allow_list_row("theme", AppConfigScopeType.PUBLIC),
            _allow_list_row("theme", AppConfigScopeType.DOMAIN),
            _allow_list_row("theme", AppConfigScopeType.USER),
            _allow_list_row("menu", AppConfigScopeType.PUBLIC),
        ])
        await db_sess.flush()
        rows = [
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="public",
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_ID,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id="other",
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_ID,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_OTHER_USER_ID,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="menu",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="public",
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
                )
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
                )
            )


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
        )
        assert updated.config == {"b": 2}
        assert (await repository.get_by_id(domain_scoped_fragment.id)).config == {"b": 2}

    async def test_update_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        missing_id = AppConfigFragmentID(uuid.uuid4())
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.update(
                Updater(
                    spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({})),
                    pk_value=missing_id,
                ),
            )


class TestPurge:
    async def test_purge_removes_row(
        self,
        repository: AppConfigFragmentRepository,
        domain_scoped_fragment: AppConfigFragmentData,
    ) -> None:
        purged = await repository.purge(
            AppConfigFragmentPurgerSpec(fragment_id=domain_scoped_fragment.id),
        )
        assert purged.id == domain_scoped_fragment.id
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(domain_scoped_fragment.id)

    async def test_purge_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        missing_id = AppConfigFragmentID(uuid.uuid4())
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.purge(
                AppConfigFragmentPurgerSpec(fragment_id=missing_id),
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
            _allow_list_row("theme", AppConfigScopeType.DOMAIN),
            _allow_list_row("theme", AppConfigScopeType.USER),
        ])
        await db_sess.flush()
        rows = [
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_ID,
                config={"a": 1},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_ID,
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
            BulkCreator(
                specs=[
                    AppConfigFragmentCreatorSpec(
                        config_name="theme",
                        scope_type=AppConfigScopeType.PUBLIC,
                        scope_id="public",
                        config={"a": 1},
                    ),
                    AppConfigFragmentCreatorSpec(
                        config_name="theme",
                        scope_type=AppConfigScopeType.DOMAIN,
                        scope_id=_DOMAIN_ID,
                        config={"b": 2},
                    ),
                ]
            )
        )
        assert len(result.succeeded) == 2
        assert result.failed == []
        for fragment in result.succeeded:
            assert (await repository.get_by_id(fragment.id)).id == fragment.id

    async def test_partial_when_one_not_allow_listed(
        self, repository: AppConfigFragmentRepository, menu_defined: None
    ) -> None:
        result = await repository.bulk_create(
            BulkCreator(
                specs=[
                    AppConfigFragmentCreatorSpec(
                        config_name="theme",  # allow-listed
                        scope_type=AppConfigScopeType.DOMAIN,
                        scope_id=_DOMAIN_ID,
                        config={"a": 1},
                    ),
                    AppConfigFragmentCreatorSpec(
                        config_name="menu",  # defined but NOT allow-listed -> FK rejects the insert
                        scope_type=AppConfigScopeType.PUBLIC,
                        scope_id="public",
                        config={"b": 2},
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
        result = await repository.bulk_update([
            Updater(
                spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"x": 1})),
                pk_value=two_fragments[0].id,
            ),
            Updater(
                spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"y": 2})),
                pk_value=two_fragments[1].id,
            ),
        ])
        assert [u.config for u in result.succeeded] == [{"x": 1}, {"y": 2}]
        assert result.failed == []
        assert (await repository.get_by_id(two_fragments[0].id)).config == {"x": 1}

    async def test_partial_when_one_missing(
        self,
        repository: AppConfigFragmentRepository,
        two_fragments: list[AppConfigFragmentData],
    ) -> None:
        missing_id = AppConfigFragmentID(uuid.uuid4())
        result = await repository.bulk_update([
            Updater(
                spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"x": 1})),
                pk_value=two_fragments[0].id,
            ),
            Updater(
                spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update({"z": 9})),
                pk_value=missing_id,  # missing -> reported
            ),
        ])
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
        result = await repository.bulk_purge([
            Purger(row_class=AppConfigFragmentRow, pk_value=fragment.id)
            for fragment in two_fragments
        ])
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
        missing_id = AppConfigFragmentID(uuid.uuid4())
        result = await repository.bulk_purge([
            Purger(row_class=AppConfigFragmentRow, pk_value=two_fragments[0].id),
            Purger(row_class=AppConfigFragmentRow, pk_value=missing_id),  # missing -> reported
        ])
        # partial: the existing fragment is purged; the missing one (index 1) is reported
        assert [p.id for p in result.succeeded] == [two_fragments[0].id]
        assert [f.index for f in result.failed] == [1]
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(two_fragments[0].id)


class TestVisibilityConditions:
    async def test_public_visibility_selects_only_public(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[AppConfigFragmentConditions.by_public_visibility()],
            )
        )
        # Visibility is scope-only (name-independent): every public fragment, any name.
        expected = {
            f.id for f in fragments_across_scopes if f.scope_type is AppConfigScopeType.PUBLIC
        }
        assert {item.id for item in result.items} == expected

    async def test_domain_visibility_selects_only_that_domain(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[AppConfigFragmentConditions.by_domain_visibility(_DOMAIN_ID)],
            )
        )
        expected = {
            f.id
            for f in fragments_across_scopes
            if f.scope_type is AppConfigScopeType.DOMAIN and f.scope_id == _DOMAIN_ID
        }
        assert {item.id for item in result.items} == expected

    async def test_user_visibility_selects_only_that_user(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[AppConfigFragmentConditions.by_user_visibility(_USER_ID)],
            )
        )
        expected = {
            f.id
            for f in fragments_across_scopes
            if f.scope_type is AppConfigScopeType.USER and f.scope_id == _USER_ID
        }
        assert {item.id for item in result.items} == expected


class TestApplicableFragments:
    async def test_one_query_returns_public_domain_user_rank_ordered(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        applicable = await repository.list_visible_fragments_bulk(
            ["theme"],
            AppConfigScopeArguments(domain_id=DomainID(_DOMAIN_UUID), user_id=UserID(_USER_UUID)),
        )
        # public + the caller's domain + the caller's own user fragment, ordered by the
        # allow-list entries' ranks (scope-type defaults: public < domain < user).
        expected = [
            f
            for f in fragments_across_scopes
            if f.config_name == "theme"
            and (
                f.scope_type is AppConfigScopeType.PUBLIC
                or (f.scope_type is AppConfigScopeType.DOMAIN and f.scope_id == _DOMAIN_ID)
                or (f.scope_type is AppConfigScopeType.USER and f.scope_id == _USER_ID)
            )
        ]
        assert [f.id for f in applicable] == [f.id for f in expected]
        assert [f.scope_type for f in applicable] == [
            AppConfigScopeType.PUBLIC,
            AppConfigScopeType.DOMAIN,
            AppConfigScopeType.USER,
        ]

    async def test_unknown_config_name_returns_empty(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        applicable = await repository.list_visible_fragments_bulk(
            ["unregistered"],
            AppConfigScopeArguments(domain_id=DomainID(_DOMAIN_UUID), user_id=UserID(_USER_UUID)),
        )
        assert applicable == []

    async def test_bulk_returns_visible_fragments_for_all_names_ordered(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        applicable = await repository.list_visible_fragments_bulk(
            ["theme", "menu"],
            AppConfigScopeArguments(domain_id=DomainID(_DOMAIN_UUID), user_id=UserID(_USER_UUID)),
        )
        # public + the caller's domain + the caller's own user fragment, for both names.
        expected = {
            f.id
            for f in fragments_across_scopes
            if f.config_name in ("theme", "menu")
            and (
                f.scope_type is AppConfigScopeType.PUBLIC
                or (f.scope_type is AppConfigScopeType.DOMAIN and f.scope_id == _DOMAIN_ID)
                or (f.scope_type is AppConfigScopeType.USER and f.scope_id == _USER_ID)
            )
        }
        assert {f.id for f in applicable} == expected
        # Rank-ordered globally, so each config_name's subset stays rank-ordered
        # (public < domain < user) for the caller to group by name and deep-merge in order.
        for name in ("theme", "menu"):
            ranks = [f.scope_type.default_rank() for f in applicable if f.config_name == name]
            assert ranks == sorted(ranks)

    async def test_bulk_empty_names_returns_empty(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        applicable = await repository.list_visible_fragments_bulk(
            [],
            AppConfigScopeArguments(domain_id=DomainID(_DOMAIN_UUID), user_id=UserID(_USER_UUID)),
        )
        assert applicable == []


@dataclass(frozen=True)
class _ScopeBinding:
    """One RBAC scope a fragment is bound to (a row of ``association_scopes_entities``)."""

    scope_type: ScopeType
    scope_id: str


@dataclass(frozen=True)
class _FragmentScopeCase:
    """A fragment scope to write at, with the bindings a create at that scope must produce.

    ``expected_bindings`` is empty for ``public``: it is GLOBAL-scoped and has no RBAC scope
    element to bind to.
    """

    scope_type: AppConfigScopeType
    scope_id: str
    expected_bindings: list[_ScopeBinding] = field(default_factory=list)


class TestRBACScopeAssociation:
    """Create binds a ``user`` / ``domain`` fragment to its RBAC scope so the RBAC validator can
    resolve ownership on a later update/purge; ``public`` (GLOBAL, no RBAC scope) gets none."""

    @staticmethod
    async def _scope_bindings(
        database: ExtendedAsyncSAEngine, entity_id: str
    ) -> list[_ScopeBinding]:
        """The RBAC scopes the fragment is currently bound to."""
        async with database.begin_readonly_session() as db_sess:
            rows = await db_sess.scalars(
                sa.select(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.entity_type == EntityType.APP_CONFIG_FRAGMENT,
                    AssociationScopesEntitiesRow.entity_id == entity_id,
                )
            )
            return [_ScopeBinding(scope_type=row.scope_type, scope_id=row.scope_id) for row in rows]

    @pytest.mark.parametrize(
        "case",
        [
            _FragmentScopeCase(
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_ID,
                expected_bindings=[_ScopeBinding(scope_type=ScopeType.USER, scope_id=_USER_ID)],
            ),
            _FragmentScopeCase(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_ID,
                expected_bindings=[_ScopeBinding(scope_type=ScopeType.DOMAIN, scope_id=_DOMAIN_ID)],
            ),
            _FragmentScopeCase(scope_type=AppConfigScopeType.PUBLIC, scope_id="public"),
        ],
        ids=lambda case: case.scope_type.value,
    )
    async def test_create_binds_to_its_rbac_scope(
        self,
        repository: AppConfigFragmentRepository,
        database: ExtendedAsyncSAEngine,
        theme_registered: None,
        case: _FragmentScopeCase,
    ) -> None:
        created = await repository.create(
            AppConfigFragmentCreatorSpec(
                config_name="theme",
                scope_type=case.scope_type,
                scope_id=case.scope_id,
                config={"k": "v"},
            )
        )
        assert await self._scope_bindings(database, str(created.id)) == case.expected_bindings

    @pytest.mark.parametrize(
        "case",
        [
            _FragmentScopeCase(
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_ID,
                expected_bindings=[_ScopeBinding(scope_type=ScopeType.USER, scope_id=_USER_ID)],
            ),
            _FragmentScopeCase(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_ID,
                expected_bindings=[_ScopeBinding(scope_type=ScopeType.DOMAIN, scope_id=_DOMAIN_ID)],
            ),
            _FragmentScopeCase(scope_type=AppConfigScopeType.PUBLIC, scope_id="public"),
        ],
        ids=lambda case: case.scope_type.value,
    )
    async def test_purge_removes_the_row_and_its_scope_binding(
        self,
        repository: AppConfigFragmentRepository,
        database: ExtendedAsyncSAEngine,
        theme_registered: None,
        case: _FragmentScopeCase,
    ) -> None:
        created = await repository.create(
            AppConfigFragmentCreatorSpec(
                config_name="theme",
                scope_type=case.scope_type,
                scope_id=case.scope_id,
                config={"k": "v"},
            )
        )
        assert await self._scope_bindings(database, str(created.id)) == case.expected_bindings
        purged = await repository.purge(AppConfigFragmentPurgerSpec(fragment_id=created.id))
        assert purged.id == created.id
        assert await self._scope_bindings(database, str(created.id)) == []
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(created.id)
