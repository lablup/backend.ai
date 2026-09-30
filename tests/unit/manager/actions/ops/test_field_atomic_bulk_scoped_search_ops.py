"""``atomic_bulk_scoped_search_ops``: a page of the permission rows the named roles hold."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.permission import PermissionFieldType, PermissionID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
    build_orders,
    build_pagination,
)
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.errors.permission import NotEnoughPermission, RoleNotFound
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.searchable_fields import (
    PermissionSearchableFields,
)
from ai.backend.manager.models.rbac_models.permission.searchers import RolePermissionSearcher
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.permission_contoller.actions.lookup_permission_owner import (
    LookupBulkRolePermissionOwnerAction,
    LookupRolePermissionOwnerAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_role_permissions import (
    SearchRolePermissionsAction,
)
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    MONITOR_READ_REFUSED,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    provision,
)

EMPTY_OWNERS_REFUSED = pytest.mark.xfail(
    strict=True, reason="the scoped read refuses an empty scope list (EmptyOperationScopeError)"
)
BACKWARD_PAGE_REVERSED = pytest.mark.xfail(
    strict=True, reason="a backward cursor page comes back in reverse display order"
)

PAGE_SIZE = 3
_ENTITY_TYPES: tuple[EntityType, ...] = (
    DomainEntityType(),
    ProjectEntityType(),
    UserEntityType(),
    RoleEntityType(),
)
_BITS: tuple[Permission, ...] = (Permission.READ, Permission.UPDATE)


@dataclass(frozen=True)
class _Roles:
    """Two roles the granted actor may read, one it may not, and one with tied rows."""

    first: RoleID
    second: RoleID
    hidden: RoleID
    tied: RoleID


async def _seed_role(
    db: ExtendedAsyncSAEngine, actors: Actors, rows: int, *, tied: bool = False
) -> RoleID:
    """A role in the actors' domain holding ``rows`` permission rows."""
    role_id = RoleID(uuid.uuid4())
    base = datetime(2026, 1, 1, tzinfo=UTC)
    pairs = [(entity_type, bit) for entity_type in _ENTITY_TYPES for bit in _BITS][:rows]
    async with db.begin_session() as sess:
        sess.add(
            RoleRow(
                id=role_id,
                name=f"target-{role_id.hex[:8]}",
                status=RoleStatus.ACTIVE,
                scope_type=DomainEntityType(),
                scope_id=actors.domain_id,
            )
        )
        await sess.flush()
        sess.add_all([
            PermissionRow(
                role_id=role_id,
                entity_type=entity_type,
                permission=bit,
                created_at=base if tied else base + timedelta(minutes=index),
            )
            for index, (entity_type, bit) in enumerate(pairs)
        ])
        await sess.commit()
    await provision(db, RoleEntityType(), role_id, [(DomainEntityType(), actors.domain_id)])
    return role_id


async def _grant_read(db: ExtendedAsyncSAEngine, actors: Actors, role_id: RoleID) -> None:
    await grant(
        db,
        actors.user_id(Actor.GRANTED),
        RoleEntityType(),
        role_id,
        RoleEntityType(),
        Permission.READ,
    )


@pytest.fixture
async def roles(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> _Roles:
    seeded = _Roles(
        first=await _seed_role(ops_db, actors, 7),
        second=await _seed_role(ops_db, actors, 2),
        hidden=await _seed_role(ops_db, actors, 2),
        tied=await _seed_role(ops_db, actors, 5, tied=True),
    )
    for role_id in (seeded.first, seeded.second, seeded.tied):
        await _grant_read(ops_db, actors, role_id)
    return seeded


def _processor(harness: OpsHarness) -> Any:
    permissions = harness.group(RoleEntityType()).field_group(
        FieldGroupMeta(PermissionFieldType()),
        PermissionData,
        LookupRolePermissionOwnerAction,
        LookupBulkRolePermissionOwnerAction,
    )
    return permissions.atomic_bulk_scoped_search_ops(SearchRolePermissionsAction)


def _spec() -> PaginationSpec:
    """The spec the role permission search of the RBAC adapter pages with."""
    return PaginationSpec(
        forward_order=PermissionSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=PermissionRow.id,
    )


def _searcher(options: PaginationOptions) -> RolePermissionSearcher:
    return RolePermissionSearcher(
        pagination=build_pagination(options, _spec()),
        orders=build_orders(options, _spec(), []),
    )


def _all(role_ids: Sequence[RoleID]) -> SearchRolePermissionsAction:
    return SearchRolePermissionsAction(
        role_ids=list(role_ids), searcher=RolePermissionSearcher(pagination=NoPagination())
    )


def _display_key(item: PermissionData) -> tuple[float, uuid.UUID]:
    return (-item.created_at.timestamp(), item.id)


async def _display_order(harness: OpsHarness, role_id: RoleID) -> list[PermissionID]:
    result = await _processor(harness).run(_all([role_id]))
    return [item.id for item in sorted(result.items, key=_display_key)]


async def _page(harness: OpsHarness, role_id: RoleID, options: PaginationOptions) -> Any:
    return await _processor(harness).run(
        SearchRolePermissionsAction(role_ids=[role_id], searcher=_searcher(options))
    )


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced", "error"),
        [
            pytest.param(Actor.SUPERADMIN, True, None, id="actor-1"),
            pytest.param(Actor.MONITOR, True, None, id="actor-2", marks=MONITOR_READ_REFUSED),
            pytest.param(Actor.GRANTED, True, None, id="actor-3"),
            pytest.param(Actor.UNGRANTED, True, NotEnoughPermission, id="actor-4"),
            pytest.param(
                Actor.ANONYMOUS, True, BackendAIError, id="actor-5", marks=ANONYMOUS_NOT_REFUSED
            ),
            pytest.param(
                Actor.ANONYMOUS,
                False,
                BackendAIError,
                id="actor-5-rbac-off",
                marks=ANONYMOUS_NOT_REFUSED,
            ),
            pytest.param(Actor.UNGRANTED, False, None, id="actor-6"),
        ],
    )
    async def test_actor(
        self,
        harness: OpsHarness,
        actors: Actors,
        roles: _Roles,
        repository_calls: Callable[[str], list[Any]],
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)
        action = _all([roles.first, roles.second])
        reads = repository_calls("search_in_scopes")

        with actors.acting_as(actor):
            if error is None:
                result = await _processor(harness).run(action)
                assert {item.role_id for item in result.items} == {roles.first, roles.second}
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(action)
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)
                assert reads == []


class TestMulti:
    async def test_one_unreadable_owner_refuses_all(
        self,
        harness: OpsHarness,
        actors: Actors,
        roles: _Roles,
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """multi-1."""
        reads = repository_calls("search_in_scopes")

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_all([roles.first, roles.hidden]))

        assert reads == []

    async def test_two_owners_give_the_union_once(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """multi-2."""
        with actors.acting_as(Actor.GRANTED):
            first = await _processor(harness).run(_all([roles.first]))
            second = await _processor(harness).run(_all([roles.second]))
            both = await _processor(harness).run(_all([roles.first, roles.second]))

        ids = [item.id for item in both.items]
        assert len(ids) == len(set(ids))
        assert set(ids) == {item.id for item in (*first.items, *second.items)}
        assert both.total_count == len(ids)

    async def test_an_owner_named_twice_reads_as_once(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """multi-3."""
        with actors.acting_as(Actor.GRANTED):
            once = await _processor(harness).run(_all([roles.first]))
            twice = await _processor(harness).run(_all([roles.first, roles.first]))

        assert [item.id for item in twice.items] == [item.id for item in once.items]
        assert twice.total_count == once.total_count

    @EMPTY_OWNERS_REFUSED
    async def test_no_owner_is_an_empty_page(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """multi-4."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_all([]))

        assert result.items == []
        assert result.total_count == 0


class TestTarget:
    @pytest.mark.parametrize(
        ("actor", "error", "runs"),
        [
            pytest.param(Actor.SUPERADMIN, RoleNotFound, True, id="target-1"),
            pytest.param(Actor.GRANTED, NotEnoughPermission, False, id="target-2"),
        ],
    )
    async def test_missing(
        self,
        harness: OpsHarness,
        actors: Actors,
        roles: _Roles,
        repository_calls: Callable[[str], list[Any]],
        actor: Actor,
        error: type[Exception],
        runs: bool,
    ) -> None:
        missing = RoleID(uuid.uuid4())
        reads = repository_calls("search_in_scopes")

        with actors.acting_as(actor):
            with pytest.raises(error):
                await _processor(harness).run(_all([missing]))

        assert len(reads) == (1 if runs else 0)


class TestPage:
    async def test_first_forward_page(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """page-1."""
        with actors.acting_as(Actor.GRANTED):
            expected = await _display_order(harness, roles.first)
            page = await _page(harness, roles.first, PaginationOptions(first=PAGE_SIZE))

        assert [item.id for item in page.items] == expected[:PAGE_SIZE]
        assert page.has_previous_page is False
        assert page.has_next_page is True

    async def test_forward_to_the_end(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """page-2."""
        seen: list[PermissionID] = []
        flags: list[tuple[bool, bool]] = []
        with actors.acting_as(Actor.GRANTED):
            expected = await _display_order(harness, roles.first)
            after: str | None = None
            while True:
                page = await _page(
                    harness, roles.first, PaginationOptions(first=PAGE_SIZE, after=after)
                )
                seen.extend(item.id for item in page.items)
                flags.append((page.has_previous_page, page.has_next_page))
                if not page.has_next_page:
                    break
                after = encode_cursor(page.items[-1].id)

        assert seen == expected
        assert [previous for previous, _ in flags] == [False] + [True] * (len(flags) - 1)
        assert [following for _, following in flags] == [True] * (len(flags) - 1) + [False]

    async def test_first_backward_page_flags(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """page-3, the rows and flags; their order is the next test."""
        with actors.acting_as(Actor.GRANTED):
            expected = await _display_order(harness, roles.first)
            page = await _page(harness, roles.first, PaginationOptions(last=PAGE_SIZE))

        assert {item.id for item in page.items} == set(expected[-PAGE_SIZE:])
        assert page.has_next_page is False
        assert page.has_previous_page is True

    @BACKWARD_PAGE_REVERSED
    async def test_first_backward_page_order(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """page-3."""
        with actors.acting_as(Actor.GRANTED):
            expected = await _display_order(harness, roles.first)
            page = await _page(harness, roles.first, PaginationOptions(last=PAGE_SIZE))

        assert [item.id for item in page.items] == expected[-PAGE_SIZE:]

    async def test_backward_to_the_start_flags(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """page-4, each row once and the flags, with the cursor on the page's display-first row."""
        seen: list[PermissionID] = []
        flags: list[tuple[bool, bool]] = []
        with actors.acting_as(Actor.GRANTED):
            expected = await _display_order(harness, roles.first)
            before: str | None = None
            while True:
                page = await _page(
                    harness, roles.first, PaginationOptions(last=PAGE_SIZE, before=before)
                )
                seen.extend(item.id for item in page.items)
                flags.append((page.has_previous_page, page.has_next_page))
                if not page.has_previous_page:
                    break
                before = encode_cursor(min(page.items, key=_display_key).id)

        assert sorted(seen) == sorted(expected)
        assert len(seen) == len(expected)
        assert [following for _, following in flags] == [False] + [True] * (len(flags) - 1)
        assert [previous for previous, _ in flags] == [True] * (len(flags) - 1) + [False]

    @BACKWARD_PAGE_REVERSED
    async def test_backward_to_the_start_order(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """page-4."""
        pages: list[list[PermissionID]] = []
        with actors.acting_as(Actor.GRANTED):
            expected = await _display_order(harness, roles.first)
            before: str | None = None
            while True:
                page = await _page(
                    harness, roles.first, PaginationOptions(last=PAGE_SIZE, before=before)
                )
                pages.append([item.id for item in page.items])
                if not page.has_previous_page:
                    break
                before = encode_cursor(page.items[0].id)

        assert [row for page_ids in reversed(pages) for row in page_ids] == expected

    @pytest.mark.parametrize("forward", [True, False], ids=["forward", "backward"])
    async def test_tied_sort_values(
        self, harness: OpsHarness, actors: Actors, roles: _Roles, forward: bool
    ) -> None:
        """page-5."""
        seen: list[PermissionID] = []
        with actors.acting_as(Actor.GRANTED):
            expected = await _display_order(harness, roles.tied)
            cursor: str | None = None
            while True:
                options = (
                    PaginationOptions(first=2, after=cursor)
                    if forward
                    else PaginationOptions(last=2, before=cursor)
                )
                page = await _page(harness, roles.tied, options)
                seen.extend(item.id for item in page.items)
                more = page.has_next_page if forward else page.has_previous_page
                if not more:
                    break
                edge = (max if forward else min)(page.items, key=_display_key)
                cursor = encode_cursor(edge.id)

        assert len(seen) == len(expected)
        assert set(seen) == set(expected)

    async def test_offset_to_the_end(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """page-6."""
        seen: list[PermissionID] = []
        with actors.acting_as(Actor.GRANTED):
            expected = await _display_order(harness, roles.first)
            for offset in range(0, len(expected), PAGE_SIZE):
                page = await _page(
                    harness, roles.first, PaginationOptions(limit=PAGE_SIZE, offset=offset)
                )
                seen.extend(item.id for item in page.items)
                assert page.has_previous_page is (offset > 0)
                assert page.has_next_page is (offset + PAGE_SIZE < len(expected))

        assert seen == expected

    async def test_offset_past_the_end(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """page-7."""
        with actors.acting_as(Actor.GRANTED):
            expected = await _display_order(harness, roles.first)
            page = await _page(harness, roles.first, PaginationOptions(limit=PAGE_SIZE, offset=100))

        assert page.items == []
        assert page.total_count == len(expected)

    async def test_total_count_ignores_the_page(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """page-8."""
        with actors.acting_as(Actor.GRANTED):
            expected = await _display_order(harness, roles.first)
            small = await _page(harness, roles.first, PaginationOptions(limit=1))
            cursor = await _page(
                harness,
                roles.first,
                PaginationOptions(first=2, after=encode_cursor(expected[0])),
            )
            backward = await _page(
                harness,
                roles.first,
                PaginationOptions(last=2, before=encode_cursor(expected[-1])),
            )

        assert [small.total_count, cursor.total_count, backward.total_count] == [len(expected)] * 3


class TestRecord:
    @pytest.mark.parametrize(
        ("actor", "owners", "status", "error"),
        [
            pytest.param(
                Actor.GRANTED, ("first", "second"), OperationStatus.SUCCESS, None, id="record-1"
            ),
            pytest.param(
                Actor.GRANTED,
                ("first", "hidden"),
                OperationStatus.DENIED,
                NotEnoughPermission,
                id="record-2",
            ),
            pytest.param(
                Actor.SUPERADMIN,
                ("first", "missing"),
                OperationStatus.ERROR,
                RoleNotFound,
                id="record-3",
            ),
            pytest.param(
                Actor.ANONYMOUS,
                ("first", "second"),
                OperationStatus.DENIED,
                BackendAIError,
                id="record-4",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_one_row_per_owner(
        self,
        harness: OpsHarness,
        actors: Actors,
        roles: _Roles,
        actor: Actor,
        owners: tuple[str, ...],
        status: OperationStatus,
        error: type[Exception] | None,
    ) -> None:
        missing = RoleID(uuid.uuid4())
        role_ids = [missing if name == "missing" else getattr(roles, name) for name in owners]

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(_all(role_ids))
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_all(role_ids))
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        records = await harness.audit(SearchRolePermissionsAction.action_name())
        assert sorted(((r.entity_type, r.entity_id), r.operation, r.status) for r in records) == (
            sorted(
                (entity_key(role_id), ActionOperationType.SEARCH, status) for role_id in role_ids
            )
        )

    async def test_a_read_is_not_recorded_unless_opted_in(
        self, silent_reads_harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """record-1, with the read left out of the policy."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(_all([roles.first, roles.second]))

        assert await silent_reads_harness.audit(SearchRolePermissionsAction.action_name()) == []

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        harness: OpsHarness,
        actors: Actors,
        roles: _Roles,
        monkeypatch: pytest.MonkeyPatch,
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)
        reads = repository_calls("search_in_scopes")

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_all([roles.first]))

        assert reads == []

        records = await harness.audit(SearchRolePermissionsAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]


class TestResult:
    async def test_the_page_carries_rows_count_and_flags(
        self, harness: OpsHarness, actors: Actors, roles: _Roles
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            page = await _page(harness, roles.first, PaginationOptions(first=PAGE_SIZE))

        assert len(page.items) == PAGE_SIZE
        assert all(isinstance(item, PermissionData) for item in page.items)
        assert all(item.role_id == roles.first for item in page.items)
        assert page.total_count == 7
        assert page.has_next_page is True
        assert page.has_previous_page is False
