"""``scope_search_ops``: a page read within the named scope, with the app config fragment
as the representative.

The fragment search names one owner, so scope-1 and scope-2 do not apply. An owner of
``None`` names the public scope by design, so scope-6 does not apply either.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from aiohttp import web

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config_fragment import (
    AppConfigFragmentEntityType,
    AppConfigFragmentID,
)
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.ops.result import ScopedBatchOpsResult
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
    build_orders,
    build_pagination,
)
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.orders import AppConfigFragmentOrders
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_fragment.searchers import AppConfigFragmentSearcher
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.app_config.actions.fragment.scoped_search import (
    ScopedSearchAppConfigFragmentAction,
)
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    ANONYMOUS_RUNS_UNENFORCED,
    MONITOR_READ_REFUSED,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    provision,
)

_BACKWARD_PAGE_IN_REVERSE = pytest.mark.xfail(
    strict=True, reason="a backward cursor page comes back in reverse display order"
)

_PAGINATION_SPEC = PaginationSpec(
    forward_order=AppConfigFragmentOrders.created_at(ascending=False),
    cursor_column=AppConfigFragmentRow.id,
)
_PAGE_SIZE = 2
_ROW_COUNT = 5


@pytest.fixture
async def fragment_db(
    ops_db: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        ops_db, [AppConfigDefinitionRow, AppConfigAllowListRow, AppConfigFragmentRow]
    ):
        yield ops_db


def _searcher(options: PaginationOptions | None = None) -> AppConfigFragmentSearcher:
    options = options or PaginationOptions(limit=100)
    return AppConfigFragmentSearcher(
        pagination=build_pagination(options, _PAGINATION_SPEC),
        orders=build_orders(options, _PAGINATION_SPEC, []),
    )


def _action(
    owner: EntityIdentifier | None, options: PaginationOptions | None = None
) -> ScopedSearchAppConfigFragmentAction:
    return ScopedSearchAppConfigFragmentAction(owner=owner, searcher=_searcher(options))


def _processor(harness: OpsHarness) -> Any:
    return harness.group(AppConfigFragmentEntityType()).scope_search_ops(
        ScopedSearchAppConfigFragmentAction
    )


async def _seed_domain(db: ExtendedAsyncSAEngine, *, in_graph: bool = True) -> DomainID:
    domain_id = DomainID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            DomainRow(
                id=domain_id,
                name=DomainName(f"domain-{domain_id.hex[:8]}"),
                total_resource_slots=ResourceSlot(),
            )
        )
        await sess.commit()
    if in_graph:
        await provision(db, DomainEntityType(), domain_id)
    return domain_id


async def _seed_fragment(
    db: ExtendedAsyncSAEngine,
    owner: DomainID | None,
    created_at: datetime | None = None,
    *,
    in_graph: bool = True,
) -> AppConfigFragmentID:
    """A fragment under its own allowed config name, written at ``owner`` or ``public``."""
    config_name = f"config-{uuid.uuid4().hex[:12]}"
    scope_type = AppConfigScopeType.of_owner(owner)
    async with db.begin_session() as sess:
        sess.add(AppConfigDefinitionRow(config_name=config_name))
        await sess.flush()
        sess.add(AppConfigAllowListRow(config_name=config_name, scope_type=scope_type, rank=0))
        await sess.flush()
        row = AppConfigFragmentRow(
            config_name=config_name, scope_type=scope_type, scope_id=owner, config={}
        )
        if created_at is not None:
            row.created_at = created_at
        sess.add(row)
        await sess.flush()
        fragment_id = AppConfigFragmentID(row.id)
        await sess.commit()
    if owner is not None and in_graph:
        await provision(
            db, AppConfigFragmentEntityType(), fragment_id, [(DomainEntityType(), owner)]
        )
    return fragment_id


@dataclass(frozen=True)
class _World:
    """Fragments at the actors' domain, which the granted user reads, and one public."""

    domain_id: DomainID
    fragments: frozenset[AppConfigFragmentID]
    public: AppConfigFragmentID


@pytest.fixture
async def world(fragment_db: ExtendedAsyncSAEngine, actors: Actors) -> _World:
    fragments = frozenset([
        await _seed_fragment(fragment_db, actors.domain_id),
        await _seed_fragment(fragment_db, actors.domain_id),
    ])
    public = await _seed_fragment(fragment_db, None)
    await grant(
        fragment_db,
        actors.user_id(Actor.GRANTED),
        DomainEntityType(),
        actors.domain_id,
        AppConfigFragmentEntityType(),
        Permission.READ,
    )
    await grant(
        fragment_db,
        actors.user_id(Actor.READ_ONLY),
        DomainEntityType(),
        actors.domain_id,
        UserEntityType(),
        Permission.READ,
    )
    return _World(domain_id=actors.domain_id, fragments=fragments, public=public)


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced", "error"),
        [
            pytest.param(Actor.SUPERADMIN, True, None, id="actor-1"),
            pytest.param(Actor.MONITOR, True, None, id="actor-2", marks=MONITOR_READ_REFUSED),
            pytest.param(Actor.GRANTED, True, None, id="actor-3"),
            pytest.param(Actor.UNGRANTED, True, NotEnoughPermission, id="actor-4"),
            pytest.param(Actor.READ_ONLY, True, NotEnoughPermission, id="actor-5"),
            pytest.param(
                Actor.ANONYMOUS, True, BackendAIError, id="actor-6", marks=ANONYMOUS_NOT_REFUSED
            ),
            pytest.param(
                Actor.ANONYMOUS,
                False,
                BackendAIError,
                id="actor-6-rbac-off",
                marks=ANONYMOUS_RUNS_UNENFORCED,
            ),
            pytest.param(Actor.UNGRANTED, False, None, id="actor-7"),
        ],
    )
    async def test_actor(
        self,
        harness: OpsHarness,
        actors: Actors,
        world: _World,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        harness.enforce(enforced)
        searches = repository_calls("search_in_scopes")
        action = _action(world.domain_id)

        with actors.acting_as(actor):
            if error is None:
                result = await _processor(harness).run(action)
                assert {item.id for item in result.items} == world.fragments
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(action)
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)
                assert searches == []


class TestScope:
    @pytest.mark.parametrize(
        ("actor", "error"),
        [
            pytest.param(Actor.GRANTED, NotEnoughPermission, id="scope-3"),
            pytest.param(Actor.SUPERADMIN, web.HTTPNotFound, id="scope-4"),
        ],
    )
    async def test_a_scope_missing_from_the_db(
        self,
        harness: OpsHarness,
        actors: Actors,
        world: _World,
        actor: Actor,
        error: type[Exception],
    ) -> None:
        with actors.acting_as(actor):
            with pytest.raises(error):
                await _processor(harness).run(_action(DomainID(uuid.uuid4())))

    async def test_a_superadmin_reads_a_scope_outside_the_graph(
        self, fragment_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """scope-5."""
        outside = await _seed_domain(fragment_db, in_graph=False)
        inside = {await _seed_fragment(fragment_db, outside, in_graph=False) for _ in range(2)}

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(_action(outside))

        assert {item.id for item in result.items} == inside

    async def test_a_user_is_refused_a_scope_outside_the_graph(
        self, fragment_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """scope-5."""
        outside = await _seed_domain(fragment_db, in_graph=False)
        await _seed_fragment(fragment_db, outside, in_graph=False)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_action(outside))


@dataclass(frozen=True)
class _Rows:
    domain_id: DomainID
    display_order: tuple[AppConfigFragmentID, ...]


async def _seed_rows(db: ExtendedAsyncSAEngine, *, tied: bool) -> _Rows:
    """Fragments at a fresh domain; ``tied`` gives them all one ``created_at``."""
    domain_id = await _seed_domain(db)
    base = datetime(2026, 1, 1, tzinfo=UTC)
    created: list[tuple[datetime, AppConfigFragmentID]] = []
    for index in range(_ROW_COUNT):
        created_at = base if tied else base + timedelta(minutes=index)
        created.append((created_at, await _seed_fragment(db, domain_id, created_at)))
    # Forward order: created_at DESC, then id ASC.
    ordered = sorted(created, key=lambda pair: (-pair[0].timestamp(), pair[1]))
    return _Rows(domain_id=domain_id, display_order=tuple(fid for _, fid in ordered))


@pytest.fixture
async def rows(fragment_db: ExtendedAsyncSAEngine) -> _Rows:
    return await _seed_rows(fragment_db, tied=False)


async def _page(
    harness: OpsHarness, rows: _Rows, options: PaginationOptions
) -> ScopedBatchOpsResult[AppConfigFragmentData]:
    result: ScopedBatchOpsResult[AppConfigFragmentData] = await _processor(harness).run(
        _action(rows.domain_id, options)
    )
    return result


async def _walk_forward(
    harness: OpsHarness, rows: _Rows
) -> list[ScopedBatchOpsResult[AppConfigFragmentData]]:
    pages = [await _page(harness, rows, PaginationOptions(first=_PAGE_SIZE))]
    while pages[-1].has_next_page and len(pages) <= _ROW_COUNT:
        after = encode_cursor(pages[-1].items[-1].id)
        pages.append(await _page(harness, rows, PaginationOptions(first=_PAGE_SIZE, after=after)))
    return pages


async def _walk_backward(
    harness: OpsHarness, rows: _Rows
) -> list[ScopedBatchOpsResult[AppConfigFragmentData]]:
    pages = [await _page(harness, rows, PaginationOptions(last=_PAGE_SIZE))]
    while pages[-1].has_previous_page and len(pages) <= _ROW_COUNT:
        # The display-order front of the page, whatever order the page came in.
        front = min(pages[-1].items, key=lambda item: rows.display_order.index(item.id))
        before = encode_cursor(front.id)
        pages.append(await _page(harness, rows, PaginationOptions(last=_PAGE_SIZE, before=before)))
    return pages


def _ids(pages: Sequence[ScopedBatchOpsResult[AppConfigFragmentData]]) -> list[uuid.UUID]:
    return [item.id for page in pages for item in page.items]


class TestPage:
    async def test_the_first_forward_page(
        self, harness: OpsHarness, actors: Actors, rows: _Rows
    ) -> None:
        """page-1."""
        with actors.acting_as(Actor.SUPERADMIN):
            page = await _page(harness, rows, PaginationOptions(first=_PAGE_SIZE))

        assert [item.id for item in page.items] == list(rows.display_order[:_PAGE_SIZE])
        assert not page.has_previous_page
        assert page.has_next_page

    async def test_forward_pages_run_to_the_end(
        self, harness: OpsHarness, actors: Actors, rows: _Rows
    ) -> None:
        """page-2."""
        with actors.acting_as(Actor.SUPERADMIN):
            pages = await _walk_forward(harness, rows)

        assert _ids(pages) == list(rows.display_order)
        assert [page.has_previous_page for page in pages] == [False] + [True] * (len(pages) - 1)
        assert [page.has_next_page for page in pages] == [True] * (len(pages) - 1) + [False]

    @_BACKWARD_PAGE_IN_REVERSE
    async def test_the_first_backward_page(
        self, harness: OpsHarness, actors: Actors, rows: _Rows
    ) -> None:
        """page-3."""
        with actors.acting_as(Actor.SUPERADMIN):
            page = await _page(harness, rows, PaginationOptions(last=_PAGE_SIZE))

        assert [item.id for item in page.items] == list(rows.display_order[-_PAGE_SIZE:])
        assert not page.has_next_page
        assert page.has_previous_page

    @_BACKWARD_PAGE_IN_REVERSE
    async def test_backward_pages_run_to_the_front(
        self, harness: OpsHarness, actors: Actors, rows: _Rows
    ) -> None:
        """page-4."""
        with actors.acting_as(Actor.SUPERADMIN):
            pages = await _walk_backward(harness, rows)

        assert _ids(list(reversed(pages))) == list(rows.display_order)
        assert [page.has_next_page for page in pages] == [False] + [True] * (len(pages) - 1)
        assert [page.has_previous_page for page in pages] == [True] * (len(pages) - 1) + [False]

    async def test_tied_rows_forward(
        self, fragment_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """page-5, forward."""
        tied = await _seed_rows(fragment_db, tied=True)

        with actors.acting_as(Actor.SUPERADMIN):
            ids = _ids(await _walk_forward(harness, tied))

        assert sorted(ids) == sorted(tied.display_order)

    async def test_tied_rows_backward(
        self, fragment_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """page-5, backward."""
        tied = await _seed_rows(fragment_db, tied=True)

        with actors.acting_as(Actor.SUPERADMIN):
            ids = _ids(await _walk_backward(harness, tied))

        assert sorted(ids) == sorted(tied.display_order)

    async def test_offset_pages_run_to_the_end(
        self, harness: OpsHarness, actors: Actors, rows: _Rows
    ) -> None:
        """page-6."""
        pages: list[tuple[int, ScopedBatchOpsResult[AppConfigFragmentData]]] = []
        with actors.acting_as(Actor.SUPERADMIN):
            for offset in range(0, _ROW_COUNT, _PAGE_SIZE):
                options = PaginationOptions(limit=_PAGE_SIZE, offset=offset)
                pages.append((offset, await _page(harness, rows, options)))

        assert _ids([page for _, page in pages]) == list(rows.display_order)
        for offset, page in pages:
            assert page.has_previous_page == (offset > 0)
            assert page.has_next_page == (offset + len(page.items) < _ROW_COUNT)

    async def test_an_offset_past_the_end(
        self, harness: OpsHarness, actors: Actors, rows: _Rows
    ) -> None:
        """page-7."""
        options = PaginationOptions(limit=_PAGE_SIZE, offset=_ROW_COUNT + 1)
        with actors.acting_as(Actor.SUPERADMIN):
            page = await _page(harness, rows, options)

        assert page.items == []
        assert page.total_count == _ROW_COUNT

    @pytest.mark.parametrize(
        "options",
        [
            PaginationOptions(limit=1),
            PaginationOptions(first=1),
            PaginationOptions(last=1),
        ],
    )
    async def test_total_count_ignores_the_page(
        self, harness: OpsHarness, actors: Actors, rows: _Rows, options: PaginationOptions
    ) -> None:
        """page-8."""
        with actors.acting_as(Actor.SUPERADMIN):
            page = await _page(harness, rows, options)

        assert page.total_count == _ROW_COUNT

    async def test_total_count_ignores_the_cursor(
        self, harness: OpsHarness, actors: Actors, rows: _Rows
    ) -> None:
        """page-8."""
        after = encode_cursor(rows.display_order[0])
        with actors.acting_as(Actor.SUPERADMIN):
            page = await _page(harness, rows, PaginationOptions(first=1, after=after))

        assert page.total_count == _ROW_COUNT


def _empty_row(scope: DomainID, status: OperationStatus) -> tuple[Any, ...]:
    return (
        str(AppConfigFragmentEntityType()),
        None,
        ActionOperationType.SEARCH,
        status,
        frozenset([entity_key(scope)]),
    )


class TestRecord:
    async def test_one_row_per_entity_read(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """record-1."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_action(world.domain_id))

        records = await harness.audit(ScopedSearchAppConfigFragmentAction.action_name())
        scopes = frozenset([entity_key(world.domain_id)])
        assert sorted(
            ((r.entity_type, r.entity_id), r.operation, r.status, r.scopes) for r in records
        ) == sorted(
            (entity_key(fragment), ActionOperationType.SEARCH, OperationStatus.SUCCESS, scopes)
            for fragment in world.fragments
        )

    async def test_a_read_is_not_recorded_unless_opted_in(
        self, silent_reads_harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """record-1, with the read left out of the policy."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(_action(world.domain_id))

        assert (
            await silent_reads_harness.audit(ScopedSearchAppConfigFragmentAction.action_name())
            == []
        )

    async def test_an_empty_read_leaves_one_row(
        self, fragment_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """record-2."""
        empty = await _seed_domain(fragment_db)

        with actors.acting_as(Actor.SUPERADMIN):
            await _processor(harness).run(_action(empty))

        records = await harness.audit(ScopedSearchAppConfigFragmentAction.action_name())
        assert [(r.entity_type, r.entity_id, r.operation, r.status, r.scopes) for r in records] == [
            _empty_row(empty, OperationStatus.SUCCESS)
        ]

    @pytest.mark.parametrize(
        ("actor", "missing", "status"),
        [
            pytest.param(Actor.UNGRANTED, False, OperationStatus.DENIED, id="record-3"),
            pytest.param(Actor.SUPERADMIN, True, OperationStatus.ERROR, id="record-4"),
            pytest.param(
                Actor.ANONYMOUS,
                False,
                OperationStatus.DENIED,
                id="record-5",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_a_failed_run_leaves_one_row(
        self,
        harness: OpsHarness,
        actors: Actors,
        world: _World,
        actor: Actor,
        missing: bool,
        status: OperationStatus,
    ) -> None:
        """record-4 fails in the run: the scope is not in the DB."""
        scope = DomainID(uuid.uuid4()) if missing else world.domain_id

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(harness).run(_action(scope))

        records = await harness.audit(ScopedSearchAppConfigFragmentAction.action_name())
        assert [(r.entity_type, r.entity_id, r.operation, r.status, r.scopes) for r in records] == [
            _empty_row(scope, status)
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        harness: OpsHarness,
        actors: Actors,
        world: _World,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-6."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "checked_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_action(world.domain_id))

        records = await harness.audit(ScopedSearchAppConfigFragmentAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]


class TestResult:
    async def test_the_page_and_its_bounds(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _action(world.domain_id, PaginationOptions(limit=1))
            )

        assert len(result.items) == 1
        assert result.items[0].id in world.fragments
        assert result.total_count == len(world.fragments)
        assert result.has_next_page
        assert not result.has_previous_page
