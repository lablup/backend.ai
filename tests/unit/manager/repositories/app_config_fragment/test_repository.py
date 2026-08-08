"""Tests for AppConfigFragmentRepository with real database operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

import pytest
import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.common.exception import BackendAIError, UserNotFound
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.errors.app_config import (
    AppConfigFragmentNotFound,
    AppConfigFragmentWriteNotAllowed,
)
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.purgers import (
    AppConfigFragmentPurgerSpec,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigFragmentOperationScope,
)
from ai.backend.manager.repositories.app_config_fragment.upserters import (
    AppConfigFragmentUpserterSpec,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
)
from ai.backend.manager.repositories.ops.rbac.provider import RBACOpsProvider
from ai.backend.testutils.db import with_tables

_DOMAIN_ID = DomainID(uuid.uuid4())
_USER_ID = UserID(uuid.uuid4())
_OTHER_DOMAIN_ID = DomainID(uuid.uuid4())
_OTHER_USER_ID = UserID(uuid.uuid4())

# The same owners seen as a fragment's scope_id, which is polymorphic over scope kinds.
_DOMAIN_SCOPE_ID = AppConfigScopeID(_DOMAIN_ID)
_USER_SCOPE_ID = AppConfigScopeID(_USER_ID)
_OTHER_DOMAIN_SCOPE_ID = AppConfigScopeID(_OTHER_DOMAIN_ID)
_OTHER_USER_SCOPE_ID = AppConfigScopeID(_OTHER_USER_ID)


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
            # Owners of the domain / user scopes a scoped search existence-checks.
            DomainRow,
            UserResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRow,
            KeyPairRow,
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
            scope_id=_DOMAIN_SCOPE_ID,
            config={"k": "v"},
        )
        db_sess.add(row)
        await db_sess.flush()
        return row.to_data()


@pytest.fixture
async def fragment_at_every_scope(
    database: ExtendedAsyncSAEngine, theme_registered: None
) -> dict[AppConfigScopeType, AppConfigFragmentData]:
    """Situation: ``theme`` already holds one fragment at each scope, keyed by that scope."""
    owners: dict[AppConfigScopeType, AppConfigScopeID | None] = {
        AppConfigScopeType.PUBLIC: None,
        AppConfigScopeType.DOMAIN: _DOMAIN_SCOPE_ID,
        AppConfigScopeType.USER: _USER_SCOPE_ID,
    }
    async with database.begin_session() as db_sess:
        rows = [
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=scope_type,
                scope_id=scope_id,
                config={"k": "v"},
            )
            for scope_type, scope_id in owners.items()
        ]
        db_sess.add_all(rows)
        await db_sess.flush()
        return {row.scope_type: row.to_data() for row in rows}


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
                scope_id=None,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_SCOPE_ID,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_OTHER_DOMAIN_SCOPE_ID,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_SCOPE_ID,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_OTHER_USER_SCOPE_ID,
                config={"k": "v"},
            ),
            AppConfigFragmentRow(
                config_name="menu",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id=None,
                config={"k": "v"},
            ),
        ]
        db_sess.add_all(rows)
        await db_sess.flush()
        return [row.to_data() for row in rows]


class TestGet:
    async def test_get_by_id_missing_raises(self, repository: AppConfigFragmentRepository) -> None:
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(AppConfigFragmentID(uuid.uuid4()))


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

    @pytest.mark.parametrize("negated", [False, True], ids=["equals", "not-equals"])
    async def test_filter_by_scope_id(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
        negated: bool,
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[
                    AppConfigFragmentConditions.by_scope_id_equals(
                        UUIDEqualMatchSpec(value=_USER_SCOPE_ID, negated=negated)
                    )
                ],
            )
        )
        # Public rows hold NULL, and neither `= x` nor `NOT (= x)` is true of NULL, so they
        # fall out of both directions of the filter.
        expected = {
            f.id
            for f in fragments_across_scopes
            if f.scope_id is not None and (f.scope_id == _USER_SCOPE_ID) is not negated
        }
        assert {item.id for item in result.items} == expected


@dataclass(frozen=True)
class _ScopedSearchCase:
    """One scope a scoped search runs against, and the rows it must return."""

    scope: AppConfigFragmentOperationScope
    expected_scope_type: AppConfigScopeType
    expected_scope_id: AppConfigScopeID | None


@dataclass(frozen=True)
class _MissingOwnerCase:
    """A scope whose owner does not exist, and the error the existence check must raise."""

    scope: AppConfigFragmentOperationScope
    expected_error: type[BackendAIError]


_DOMAIN_NAME = "app-config-fragment-test-domain"
_RESOURCE_POLICY_NAME = "app-config-fragment-test-policy"


@pytest.fixture
async def scope_owners(database: ExtendedAsyncSAEngine) -> None:
    """The domain and user a scoped search names, so its existence checks find them."""
    async with database.begin_session() as db_sess:
        db_sess.add_all([
            DomainRow(id=_DOMAIN_ID, name=_DOMAIN_NAME, total_resource_slots=ResourceSlot()),
            UserResourcePolicyRow(
                name=_RESOURCE_POLICY_NAME,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            ),
        ])
        await db_sess.flush()
        db_sess.add(
            UserRow(
                uuid=_USER_ID,
                email="app-config-fragment@lablup.com",
                username="app-config-fragment",
                password=PasswordInfo(
                    password="test_password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=100_000,
                    salt_size=32,
                ),
                domain_name=_DOMAIN_NAME,
                resource_policy=_RESOURCE_POLICY_NAME,
            )
        )


class TestScopedSearch:
    @pytest.mark.parametrize(
        "case",
        [
            _ScopedSearchCase(
                scope=AppConfigFragmentOperationScope(
                    scope_type=AppConfigScopeType.DOMAIN, scope_id=_DOMAIN_SCOPE_ID
                ),
                expected_scope_type=AppConfigScopeType.DOMAIN,
                expected_scope_id=_DOMAIN_SCOPE_ID,
            ),
            _ScopedSearchCase(
                scope=AppConfigFragmentOperationScope(
                    scope_type=AppConfigScopeType.USER, scope_id=_USER_SCOPE_ID
                ),
                expected_scope_type=AppConfigScopeType.USER,
                expected_scope_id=_USER_SCOPE_ID,
            ),
            _ScopedSearchCase(
                scope=AppConfigFragmentOperationScope(
                    scope_type=AppConfigScopeType.PUBLIC, scope_id=None
                ),
                expected_scope_type=AppConfigScopeType.PUBLIC,
                expected_scope_id=None,
            ),
        ],
        ids=lambda case: case.scope.scope_type.value,
    )
    async def test_scope_returns_only_the_fragments_written_at_it(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
        scope_owners: None,
        case: _ScopedSearchCase,
    ) -> None:
        result = await repository.scoped_search(
            BatchQuerier(pagination=OffsetPagination(limit=10, offset=0)),
            [case.scope],
        )
        expected = {
            f.id
            for f in fragments_across_scopes
            if f.scope_type is case.expected_scope_type and f.scope_id == case.expected_scope_id
        }
        assert {item.id for item in result.items} == expected
        assert result.total_count == len(expected)

    @pytest.mark.parametrize(
        "case",
        [
            _MissingOwnerCase(
                scope=AppConfigFragmentOperationScope(
                    scope_type=AppConfigScopeType.DOMAIN,
                    scope_id=AppConfigScopeID(uuid.uuid4()),
                ),
                expected_error=DomainNotFound,
            ),
            _MissingOwnerCase(
                scope=AppConfigFragmentOperationScope(
                    scope_type=AppConfigScopeType.USER,
                    scope_id=AppConfigScopeID(uuid.uuid4()),
                ),
                expected_error=UserNotFound,
            ),
        ],
        ids=lambda case: case.scope.scope_type.value,
    )
    async def test_missing_scope_owner_is_not_found(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
        case: _MissingOwnerCase,
    ) -> None:
        # A scope that does not exist is a 404, not an empty page — otherwise "no fragments
        # here" and "no such domain" are indistinguishable to the caller.
        with pytest.raises(case.expected_error):
            await repository.scoped_search(
                BatchQuerier(pagination=OffsetPagination(limit=10, offset=0)),
                [case.scope],
            )

    async def test_scopes_are_or_combined(
        self,
        repository: AppConfigFragmentRepository,
        fragments_across_scopes: list[AppConfigFragmentData],
        scope_owners: None,
    ) -> None:
        # The repository takes a sequence because the ops layer ORs the scopes; a single
        # scoped search passes one, but the read path itself is not limited to one.
        result = await repository.scoped_search(
            BatchQuerier(pagination=OffsetPagination(limit=10, offset=0)),
            [
                AppConfigFragmentOperationScope(
                    scope_type=AppConfigScopeType.DOMAIN, scope_id=_DOMAIN_SCOPE_ID
                ),
                AppConfigFragmentOperationScope(
                    scope_type=AppConfigScopeType.USER, scope_id=_USER_SCOPE_ID
                ),
            ],
        )
        expected = {
            f.id
            for f in fragments_across_scopes
            if (f.scope_type is AppConfigScopeType.DOMAIN and f.scope_id == _DOMAIN_SCOPE_ID)
            or (f.scope_type is AppConfigScopeType.USER and f.scope_id == _USER_SCOPE_ID)
        }
        assert {item.id for item in result.items} == expected


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
                scope_id=_DOMAIN_SCOPE_ID,
                config={"a": 1},
            ),
            AppConfigFragmentRow(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_SCOPE_ID,
                config={"b": 2},
            ),
        ]
        db_sess.add_all(rows)
        await db_sess.flush()
        return [row.to_data() for row in rows]


class TestBulkPurge:
    async def test_all_purged(
        self,
        repository: AppConfigFragmentRepository,
        two_fragments: list[AppConfigFragmentData],
    ) -> None:
        result = await repository.bulk_purge([
            AppConfigFragmentPurgerSpec(fragment_id=fragment.id) for fragment in two_fragments
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
            AppConfigFragmentPurgerSpec(fragment_id=two_fragments[0].id),
            AppConfigFragmentPurgerSpec(fragment_id=missing_id),  # missing -> reported
        ])
        # partial: the missing fragment is reported by its id
        assert [p.id for p in result.succeeded] == [two_fragments[0].id]
        assert [f.id for f in result.failed] == [missing_id]
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
            if f.scope_type is AppConfigScopeType.DOMAIN and f.scope_id == _DOMAIN_SCOPE_ID
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
            if f.scope_type is AppConfigScopeType.USER and f.scope_id == _USER_SCOPE_ID
        }
        assert {item.id for item in result.items} == expected


class TestApplicableFragments:
    async def test_naming_no_domain_drops_the_overlay(
        self,
        repository: AppConfigFragmentRepository,
        scope_owners: None,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        # A caller whose session carries no domain gets public and its own, never a
        # domain's — the absent domain narrows the query rather than widening it.
        applicable = await repository.list_visible_fragments_bulk(
            ["theme"],
            UserID(uuid.uuid4()),
            None,
        )
        expected = [
            f
            for f in fragments_across_scopes
            if f.config_name == "theme" and f.scope_type is AppConfigScopeType.PUBLIC
        ]
        assert [f.id for f in applicable] == [f.id for f in expected]

    async def test_one_query_returns_public_domain_user_rank_ordered(
        self,
        repository: AppConfigFragmentRepository,
        scope_owners: None,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        applicable = await repository.list_visible_fragments_bulk(
            ["theme"],
            _USER_ID,
            _DOMAIN_ID,
        )
        # public + the caller's domain + the caller's own user fragment, ordered by the
        # allow-list entries' ranks (scope-type defaults: public < domain < user).
        expected = [
            f
            for f in fragments_across_scopes
            if f.config_name == "theme"
            and (
                f.scope_type is AppConfigScopeType.PUBLIC
                or (f.scope_type is AppConfigScopeType.DOMAIN and f.scope_id == _DOMAIN_SCOPE_ID)
                or (f.scope_type is AppConfigScopeType.USER and f.scope_id == _USER_SCOPE_ID)
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
        scope_owners: None,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        applicable = await repository.list_visible_fragments_bulk(
            ["unregistered"],
            _USER_ID,
            _DOMAIN_ID,
        )
        assert applicable == []

    async def test_bulk_returns_visible_fragments_for_all_names_ordered(
        self,
        repository: AppConfigFragmentRepository,
        scope_owners: None,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        applicable = await repository.list_visible_fragments_bulk(
            ["theme", "menu"],
            _USER_ID,
            _DOMAIN_ID,
        )
        # public + the caller's domain + the caller's own user fragment, for both names.
        expected = {
            f.id
            for f in fragments_across_scopes
            if f.config_name in ("theme", "menu")
            and (
                f.scope_type is AppConfigScopeType.PUBLIC
                or (f.scope_type is AppConfigScopeType.DOMAIN and f.scope_id == _DOMAIN_SCOPE_ID)
                or (f.scope_type is AppConfigScopeType.USER and f.scope_id == _USER_SCOPE_ID)
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
        scope_owners: None,
        fragments_across_scopes: list[AppConfigFragmentData],
    ) -> None:
        applicable = await repository.list_visible_fragments_bulk(
            [],
            _USER_ID,
            _DOMAIN_ID,
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
    scope_id: AppConfigScopeID | None
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
                scope_id=_USER_SCOPE_ID,
                expected_bindings=[
                    _ScopeBinding(scope_type=ScopeType.USER, scope_id=str(_USER_ID))
                ],
            ),
            _FragmentScopeCase(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_SCOPE_ID,
                expected_bindings=[
                    _ScopeBinding(scope_type=ScopeType.DOMAIN, scope_id=str(_DOMAIN_ID))
                ],
            ),
            _FragmentScopeCase(scope_type=AppConfigScopeType.PUBLIC, scope_id=None),
        ],
        ids=lambda case: case.scope_type.value,
    )
    async def test_upsert_binds_the_new_fragment_to_its_rbac_scope(
        self,
        repository: AppConfigFragmentRepository,
        database: ExtendedAsyncSAEngine,
        theme_registered: None,
        case: _FragmentScopeCase,
    ) -> None:
        upserted = await repository.bulk_upsert([
            AppConfigFragmentUpserterSpec(
                config_name="theme",
                scope_type=case.scope_type,
                scope_id=case.scope_id,
                config={"k": "v"},
            )
        ])
        assert (
            await self._scope_bindings(database, str(upserted.items[0].id))
            == case.expected_bindings
        )

    @pytest.mark.parametrize(
        "case",
        [
            _FragmentScopeCase(
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_SCOPE_ID,
                expected_bindings=[
                    _ScopeBinding(scope_type=ScopeType.USER, scope_id=str(_USER_ID))
                ],
            ),
            _FragmentScopeCase(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_SCOPE_ID,
                expected_bindings=[
                    _ScopeBinding(scope_type=ScopeType.DOMAIN, scope_id=str(_DOMAIN_ID))
                ],
            ),
            _FragmentScopeCase(scope_type=AppConfigScopeType.PUBLIC, scope_id=None),
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
        upserted = await repository.bulk_upsert([
            AppConfigFragmentUpserterSpec(
                config_name="theme",
                scope_type=case.scope_type,
                scope_id=case.scope_id,
                config={"k": "v"},
            )
        ])
        created = upserted.items[0]
        assert await self._scope_bindings(database, str(created.id)) == case.expected_bindings
        purged = await repository.purge(AppConfigFragmentPurgerSpec(fragment_id=created.id))
        assert purged.id == created.id
        assert await self._scope_bindings(database, str(created.id)) == []

    async def test_bulk_purge_removes_the_scope_binding(
        self,
        repository: AppConfigFragmentRepository,
        database: ExtendedAsyncSAEngine,
        theme_registered: None,
    ) -> None:
        """A bulk purge unbinds each fragment, like the single purge.

        Deleting the rows alone would leave their scope associations behind, pointing at
        fragments that no longer exist.
        """
        upserted = await repository.bulk_upsert([
            AppConfigFragmentUpserterSpec(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_SCOPE_ID,
                config={"k": "v"},
            )
        ])
        created = upserted.items[0]
        assert await self._scope_bindings(database, str(created.id)) == [
            _ScopeBinding(scope_type=ScopeType.USER, scope_id=str(_USER_ID))
        ]
        result = await repository.bulk_purge([AppConfigFragmentPurgerSpec(fragment_id=created.id)])
        assert [p.id for p in result.succeeded] == [created.id]
        assert await self._scope_bindings(database, str(created.id)) == []
        with pytest.raises(AppConfigFragmentNotFound):
            await repository.get_by_id(created.id)


class TestUpsert:
    """A fragment is addressed by ``(config_name, scope_type, scope_id)``, so an upsert inserts
    it when absent and replaces its ``config`` when present, in one all-or-nothing transaction.
    """

    @pytest.mark.parametrize(
        "case",
        [
            _FragmentScopeCase(
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_SCOPE_ID,
                expected_bindings=[
                    _ScopeBinding(scope_type=ScopeType.USER, scope_id=str(_USER_ID))
                ],
            ),
            _FragmentScopeCase(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_SCOPE_ID,
                expected_bindings=[
                    _ScopeBinding(scope_type=ScopeType.DOMAIN, scope_id=str(_DOMAIN_ID))
                ],
            ),
            _FragmentScopeCase(scope_type=AppConfigScopeType.PUBLIC, scope_id=None),
        ],
        ids=lambda case: case.scope_type.value,
    )
    async def test_upsert_inserts_the_fragment_and_binds_it_to_its_scope(
        self,
        repository: AppConfigFragmentRepository,
        database: ExtendedAsyncSAEngine,
        theme_registered: None,
        case: _FragmentScopeCase,
    ) -> None:
        """An insert binds the new row to its RBAC scope, exactly as a create does."""
        result = await repository.bulk_upsert([
            AppConfigFragmentUpserterSpec(
                config_name="theme",
                scope_type=case.scope_type,
                scope_id=case.scope_id,
                config={"theme": "dark"},
            )
        ])

        assert result.failed == []
        upserted = result.items
        assert [(f.config_name, f.scope_type, f.scope_id) for f in upserted] == [
            ("theme", case.scope_type, case.scope_id)
        ]
        assert (await repository.get_by_id(upserted[0].id)).config == {"theme": "dark"}
        async with database.begin_readonly_session() as db_sess:
            rows = await db_sess.scalars(
                sa.select(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.entity_type == EntityType.APP_CONFIG_FRAGMENT,
                    AssociationScopesEntitiesRow.entity_id == str(upserted[0].id),
                )
            )
            bindings = [
                _ScopeBinding(scope_type=row.scope_type, scope_id=row.scope_id) for row in rows
            ]
        assert bindings == case.expected_bindings

    @pytest.mark.parametrize(
        "case",
        [
            _FragmentScopeCase(
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_SCOPE_ID,
                expected_bindings=[
                    _ScopeBinding(scope_type=ScopeType.USER, scope_id=str(_USER_ID))
                ],
            ),
            _FragmentScopeCase(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=_DOMAIN_SCOPE_ID,
                expected_bindings=[
                    _ScopeBinding(scope_type=ScopeType.DOMAIN, scope_id=str(_DOMAIN_ID))
                ],
            ),
            _FragmentScopeCase(scope_type=AppConfigScopeType.PUBLIC, scope_id=None),
        ],
        ids=lambda case: case.scope_type.value,
    )
    async def test_upsert_replaces_the_config_of_the_existing_fragment(
        self,
        repository: AppConfigFragmentRepository,
        database: ExtendedAsyncSAEngine,
        fragment_at_every_scope: dict[AppConfigScopeType, AppConfigFragmentData],
        case: _FragmentScopeCase,
    ) -> None:
        """The conflict updates the row in place — the same id, and its binding is not doubled.

        ``public`` conflicts on the partial unique index (``scope_id IS NULL``), the other
        scopes on the plain unique constraint.
        """
        existing = fragment_at_every_scope[case.scope_type]

        result = await repository.bulk_upsert([
            AppConfigFragmentUpserterSpec(
                config_name="theme",
                scope_type=case.scope_type,
                scope_id=case.scope_id,
                config={"theme": "light"},
            )
        ])

        assert result.failed == []
        upserted = result.items
        assert [f.id for f in upserted] == [existing.id]
        assert upserted[0].config == {"theme": "light"}
        async with database.begin_readonly_session() as db_sess:
            stored = (
                await db_sess.scalars(
                    sa.select(AppConfigFragmentRow).where(
                        AppConfigFragmentRow.config_name == "theme"
                    )
                )
            ).all()
        assert len(stored) == len(fragment_at_every_scope)
        async with database.begin_readonly_session() as db_sess:
            rows = await db_sess.scalars(
                sa.select(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.entity_type == EntityType.APP_CONFIG_FRAGMENT,
                    AssociationScopesEntitiesRow.entity_id == str(existing.id),
                )
            )
            bindings = [
                _ScopeBinding(scope_type=row.scope_type, scope_id=row.scope_id) for row in rows
            ]
        assert bindings == case.expected_bindings

    async def test_upsert_writes_every_item_of_the_batch(
        self,
        repository: AppConfigFragmentRepository,
        theme_registered: None,
    ) -> None:
        """One call mixing an insert and an update settles both."""
        await repository.bulk_upsert([
            AppConfigFragmentUpserterSpec(
                config_name="theme",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id=None,
                config={"theme": "dark"},
            )
        ])

        result = await repository.bulk_upsert([
            AppConfigFragmentUpserterSpec(
                config_name="theme",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id=None,
                config={"theme": "light"},
            ),
            AppConfigFragmentUpserterSpec(
                config_name="theme",
                scope_type=AppConfigScopeType.USER,
                scope_id=_USER_SCOPE_ID,
                config={"theme": "solarized"},
            ),
        ])

        assert result.failed == []
        assert [(f.scope_type, f.config) for f in result.items] == [
            (AppConfigScopeType.PUBLIC, {"theme": "light"}),
            (AppConfigScopeType.USER, {"theme": "solarized"}),
        ]

    async def test_upsert_rejected_when_not_allow_listed(
        self,
        repository: AppConfigFragmentRepository,
        theme_defined_not_allow_listed: None,
    ) -> None:
        """The FK to the allow list gates an upsert as it gates a create."""
        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await repository.bulk_upsert([
                AppConfigFragmentUpserterSpec(
                    config_name="theme",
                    scope_type=AppConfigScopeType.PUBLIC,
                    scope_id=None,
                    config={"theme": "dark"},
                )
            ])

    async def test_upsert_persists_nothing_when_one_item_is_rejected(
        self,
        repository: AppConfigFragmentRepository,
        database: ExtendedAsyncSAEngine,
        theme_registered: None,
    ) -> None:
        """The batch shares one transaction, so a rejected item rolls the whole call back."""
        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await repository.bulk_upsert([
                AppConfigFragmentUpserterSpec(
                    config_name="theme",
                    scope_type=AppConfigScopeType.PUBLIC,
                    scope_id=None,
                    config={"theme": "dark"},
                ),
                AppConfigFragmentUpserterSpec(
                    config_name="menu",  # registered nowhere, so its FK gate rejects it
                    scope_type=AppConfigScopeType.PUBLIC,
                    scope_id=None,
                    config={"menu": "compact"},
                ),
            ])

        async with database.begin_readonly_session() as db_sess:
            stored = (
                await db_sess.scalars(
                    sa.select(AppConfigFragmentRow).where(
                        AppConfigFragmentRow.config_name == "theme"
                    )
                )
            ).all()
        assert stored == []

    async def test_upsert_of_no_items_writes_nothing(
        self, repository: AppConfigFragmentRepository, theme_registered: None
    ) -> None:
        result = await repository.bulk_upsert([])
        assert result.items == []
        assert result.failed == []
