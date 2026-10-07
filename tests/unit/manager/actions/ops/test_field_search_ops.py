"""``search_ops (field)``: a page of the field rows inside named owners, with the domain
usage buckets of resource groups as the representative."""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator, Callable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType, ResourceGroupID
from ai.backend.common.data.entity.usage_bucket import DomainUsageBucketFieldType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.registry.types import Concern, ConcernMeta, FieldGroupMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
    build_orders,
    build_pagination,
)
from ai.backend.manager.data.resource_group.types import ResourceGroupOpts
from ai.backend.manager.data.resource_usage_history.types import DomainUsageBucketData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import EmptyOperationScopeError
from ai.backend.manager.errors.resource import ResourceGroupNotFound
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_usage_history.row import DomainUsageBucketRow
from ai.backend.manager.models.resource_usage_history.scopes import DomainUsageBucketTarget
from ai.backend.manager.models.resource_usage_history.searchable_fields import (
    DomainUsageBucketSearchableFields,
)
from ai.backend.manager.models.resource_usage_history.searchers import DomainUsageBucketSearcher
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.resource_usage.actions.search_domain_usage_buckets import (
    SearchDomainUsageBucketsAction,
)
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    ANONYMOUS_RUNS_UNENFORCED,
    MONITOR_READ_REFUSED,
    Actor,
    Actors,
    AuditRecord,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    provision,
)

_BACKWARD_PAGE_REVERSED = pytest.mark.xfail(
    strict=True, reason="a backward cursor page comes back in reverse display order"
)

_PAGINATION_SPEC = PaginationSpec(
    forward_order=DomainUsageBucketSearchableFields.own.period_start.order.apply(ascending=False),
    cursor_column=DomainUsageBucketRow.id,
)
_PAGE_SIZE = 2


@dataclass(frozen=True)
class _World:
    """Owners and the rows inside each, the rows of ``granted`` in display order."""

    granted: ResourceGroupID
    other_granted: ResourceGroupID
    ungranted: ResourceGroupID
    outside: ResourceGroupID
    tied: ResourceGroupID
    rows: dict[ResourceGroupID, list[uuid.UUID]]


@pytest.fixture
async def bucket_db(ops_db: ExtendedAsyncSAEngine) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(ops_db, [DomainUsageBucketRow]):
        yield ops_db


async def _seed_resource_group(db: ExtendedAsyncSAEngine, *, in_graph: bool) -> ResourceGroupID:
    resource_group_id = ResourceGroupID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            ResourceGroupRow(
                id=resource_group_id,
                name=f"rg-{resource_group_id.hex[:8]}",
                driver="static",
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(),
            )
        )
        await sess.commit()
    if in_graph:
        await provision(db, ResourceGroupEntityType(), resource_group_id)
    return resource_group_id


async def _seed_buckets(
    db: ExtendedAsyncSAEngine, resource_group_id: ResourceGroupID, starts: Sequence[date]
) -> list[uuid.UUID]:
    """The rows in display order: newest period first, then by id."""
    async with db.begin_session() as sess:
        rows = [
            DomainUsageBucketRow(
                domain_name=f"domain-{index}",
                resource_group=f"rg-{resource_group_id.hex[:8]}",
                resource_group_id=resource_group_id,
                period_start=start,
                period_end=start + timedelta(days=1),
                decay_unit_days=1,
                resource_usage=ResourceSlot(),
                capacity_snapshot=ResourceSlot(),
            )
            for index, start in enumerate(starts)
        ]
        sess.add_all(rows)
        await sess.flush()
        keyed = [(row.period_start, row.id) for row in rows]
        await sess.commit()
    keyed.sort(key=lambda pair: (-pair[0].toordinal(), pair[1]))
    return [row_id for _, row_id in keyed]


@pytest.fixture
async def world(bucket_db: ExtendedAsyncSAEngine, actors: Actors) -> _World:
    """The read-only actor holds READ on another entity type at ``granted`` alone."""
    granted = await _seed_resource_group(bucket_db, in_graph=True)
    other_granted = await _seed_resource_group(bucket_db, in_graph=True)
    ungranted = await _seed_resource_group(bucket_db, in_graph=True)
    outside = await _seed_resource_group(bucket_db, in_graph=False)
    tied = await _seed_resource_group(bucket_db, in_graph=True)
    for actor, resource_group_id, entity_type in (
        (Actor.GRANTED, granted, DomainEntityType()),
        (Actor.GRANTED, other_granted, DomainEntityType()),
        (Actor.GRANTED, tied, DomainEntityType()),
        (Actor.READ_ONLY, granted, ProjectEntityType()),
    ):
        await grant(
            bucket_db,
            actors.user_id(actor),
            ResourceGroupEntityType(),
            resource_group_id,
            entity_type,
            Permission.READ,
        )
    base = date(2026, 1, 1)
    return _World(
        granted=granted,
        other_granted=other_granted,
        ungranted=ungranted,
        outside=outside,
        tied=tied,
        rows={
            granted: await _seed_buckets(
                bucket_db, granted, [base + timedelta(days=day) for day in range(5)]
            ),
            other_granted: await _seed_buckets(bucket_db, other_granted, [base, base]),
            ungranted: await _seed_buckets(bucket_db, ungranted, [base]),
            outside: await _seed_buckets(bucket_db, outside, [base]),
            tied: await _seed_buckets(bucket_db, tied, [base] * 5),
        },
    )


def _processor(harness: OpsHarness) -> Any:
    buckets = harness.registry.concern(ConcernMeta(Concern.RESOURCE_GROUP)).dangling_field_group(
        FieldGroupMeta(DomainUsageBucketFieldType()), DomainUsageBucketData
    )
    return buckets.search_ops(SearchDomainUsageBucketsAction)


def _search(
    owners: Sequence[ResourceGroupID], options: PaginationOptions | None = None
) -> SearchDomainUsageBucketsAction:
    options = options or PaginationOptions(limit=100)
    return SearchDomainUsageBucketsAction(
        targets=[DomainUsageBucketTarget(resource_group_id=owner) for owner in owners],
        searcher=DomainUsageBucketSearcher(
            pagination=build_pagination(options, _PAGINATION_SPEC),
            orders=build_orders(options, _PAGINATION_SPEC, []),
        ),
    )


@dataclass(frozen=True)
class _Page:
    ids: list[uuid.UUID]
    has_previous_page: bool
    has_next_page: bool


async def _walk_forward(harness: OpsHarness, owner: ResourceGroupID) -> list[_Page]:
    pages: list[_Page] = []
    after: str | None = None
    while True:
        result = await _processor(harness).run(
            _search([owner], PaginationOptions(first=_PAGE_SIZE, after=after))
        )
        pages.append(
            _Page(
                [item.id for item in result.items], result.has_previous_page, result.has_next_page
            )
        )
        if not result.has_next_page or len(pages) > 10:
            return pages
        after = encode_cursor(result.items[-1].id)


async def _walk_backward(harness: OpsHarness, owner: ResourceGroupID) -> list[_Page]:
    pages: list[_Page] = []
    before: str | None = None
    while True:
        result = await _processor(harness).run(
            _search([owner], PaginationOptions(last=_PAGE_SIZE, before=before))
        )
        pages.append(
            _Page(
                [item.id for item in result.items], result.has_previous_page, result.has_next_page
            )
        )
        if not result.has_previous_page or len(pages) > 10:
            return pages
        before = encode_cursor(result.items[0].id)


def _record(
    records: list[AuditRecord],
) -> list[tuple[str | None, str | None, OperationStatus, frozenset[tuple[str, str]]]]:
    return [(r.entity_type, r.entity_id, r.status, r.scopes) for r in records]


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced"),
        [
            pytest.param(Actor.SUPERADMIN, True, id="actor-1"),
            pytest.param(Actor.MONITOR, True, id="actor-2", marks=MONITOR_READ_REFUSED),
            pytest.param(Actor.GRANTED, True, id="actor-3"),
            pytest.param(Actor.UNGRANTED, False, id="actor-7"),
        ],
    )
    async def test_the_page_is_read(
        self, harness: OpsHarness, actors: Actors, world: _World, actor: Actor, enforced: bool
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            result = await _processor(harness).run(_search([world.granted]))

        assert [item.id for item in result.items] == world.rows[world.granted]

    @pytest.mark.parametrize(
        ("actor", "enforced", "error"),
        [
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
        ],
    )
    async def test_the_read_is_refused(
        self,
        harness: OpsHarness,
        actors: Actors,
        world: _World,
        repository_calls: Callable[[str], list[Any]],
        actor: Actor,
        enforced: bool,
        error: type[Exception],
    ) -> None:
        harness.enforce(enforced)
        reads = repository_calls("search_in_scopes")

        with actors.acting_as(actor):
            with pytest.raises(error) as raised:
                await _processor(harness).run(_search([world.granted]))

        assert reads == []
        if actor is Actor.ANONYMOUS:
            assert_refused(raised.value)


class TestScope:
    async def test_two_granted_owners_read_their_union_once(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """scope-1: one owner named twice as well."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _search([world.granted, world.other_granted, world.granted])
            )

        ids = [item.id for item in result.items]
        expected = {*world.rows[world.granted], *world.rows[world.other_granted]}
        assert len(ids) == len(set(ids))
        assert set(ids) == expected
        assert result.total_count == len(expected)

    @pytest.mark.parametrize(
        "second",
        [pytest.param("ungranted", id="scope-2"), pytest.param("missing", id="scope-3")],
    )
    async def test_an_owner_the_caller_cannot_read_refuses_the_whole_read(
        self, harness: OpsHarness, actors: Actors, world: _World, second: str
    ) -> None:
        owner = world.ungranted if second == "ungranted" else ResourceGroupID(uuid.uuid4())

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_search([world.granted, owner]))

    async def test_a_missing_owner_is_not_found_for_a_superadmin(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """scope-4."""
        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(ResourceGroupNotFound):
                await _processor(harness).run(_search([ResourceGroupID(uuid.uuid4())]))

    async def test_an_owner_outside_the_graph_is_read_by_a_superadmin_alone(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """scope-5."""
        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(_search([world.outside]))
        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_search([world.outside]))

        assert [item.id for item in result.items] == world.rows[world.outside]

    @pytest.mark.parametrize("actor", [Actor.SUPERADMIN, Actor.GRANTED])
    async def test_no_owner_named_is_refused(
        self, harness: OpsHarness, actors: Actors, world: _World, actor: Actor
    ) -> None:
        """scope-6."""
        with actors.acting_as(actor):
            with pytest.raises(EmptyOperationScopeError):
                await _processor(harness).run(_search([]))


class TestPage:
    async def test_the_first_forward_page(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """page-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _search([world.granted], PaginationOptions(first=_PAGE_SIZE))
            )

        assert [item.id for item in result.items] == world.rows[world.granted][:_PAGE_SIZE]
        assert (result.has_previous_page, result.has_next_page) == (False, True)

    async def test_forward_pages_read_every_row_once_in_order(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """page-2."""
        with actors.acting_as(Actor.GRANTED):
            pages = await _walk_forward(harness, world.granted)

        assert [row_id for page in pages for row_id in page.ids] == world.rows[world.granted]
        assert [page.has_previous_page for page in pages] == [False] + [True] * (len(pages) - 1)
        assert [page.has_next_page for page in pages] == [True] * (len(pages) - 1) + [False]

    @_BACKWARD_PAGE_REVERSED
    async def test_the_first_backward_page(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """page-3."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _search([world.granted], PaginationOptions(last=_PAGE_SIZE))
            )

        assert [item.id for item in result.items] == world.rows[world.granted][-_PAGE_SIZE:]
        assert (result.has_previous_page, result.has_next_page) == (True, False)

    @_BACKWARD_PAGE_REVERSED
    async def test_backward_pages_read_every_row_once(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """page-4."""
        with actors.acting_as(Actor.GRANTED):
            pages = await _walk_backward(harness, world.granted)

        assert [row_id for page in reversed(pages) for row_id in page.ids] == world.rows[
            world.granted
        ]
        assert [page.has_next_page for page in pages] == [False] + [True] * (len(pages) - 1)
        assert [page.has_previous_page for page in pages] == [True] * (len(pages) - 1) + [False]

    @pytest.mark.parametrize(
        "forward",
        [
            pytest.param(True, id="page-5-forward"),
            pytest.param(False, id="page-5-backward", marks=_BACKWARD_PAGE_REVERSED),
        ],
    )
    async def test_tied_order_values_neither_overlap_nor_skip(
        self, harness: OpsHarness, actors: Actors, world: _World, forward: bool
    ) -> None:
        with actors.acting_as(Actor.GRANTED):
            if forward:
                pages = await _walk_forward(harness, world.tied)
            else:
                pages = await _walk_backward(harness, world.tied)

        seen = [row_id for page in pages for row_id in page.ids]
        assert sorted(seen) == sorted(world.rows[world.tied])

    async def test_offset_pages_read_every_row_once(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """page-6."""
        rows = world.rows[world.granted]
        seen: list[uuid.UUID] = []
        with actors.acting_as(Actor.GRANTED):
            for offset in range(0, len(rows), _PAGE_SIZE):
                result = await _processor(harness).run(
                    _search([world.granted], PaginationOptions(limit=_PAGE_SIZE, offset=offset))
                )
                seen.extend(item.id for item in result.items)
                assert result.has_previous_page == (offset > 0)
                assert result.has_next_page == (offset + _PAGE_SIZE < len(rows))

        assert seen == rows

    async def test_an_offset_past_the_end_is_empty(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """page-7."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _search([world.granted], PaginationOptions(limit=_PAGE_SIZE, offset=100))
            )

        assert result.items == []
        assert result.total_count == len(world.rows[world.granted])

    @pytest.mark.parametrize(
        "options",
        [
            pytest.param(PaginationOptions(limit=1), id="small-limit"),
            pytest.param(PaginationOptions(first=1), id="first"),
            pytest.param(PaginationOptions(last=1), id="last"),
        ],
    )
    async def test_the_total_is_every_matching_row(
        self, harness: OpsHarness, actors: Actors, world: _World, options: PaginationOptions
    ) -> None:
        """page-8."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_search([world.granted], options))
            after = await _processor(harness).run(
                _search(
                    [world.granted],
                    PaginationOptions(first=1, after=encode_cursor(result.items[0].id)),
                )
            )

        assert result.total_count == len(world.rows[world.granted])
        assert after.total_count == len(world.rows[world.granted])


class TestRecord:
    @pytest.mark.parametrize(
        "record_reads",
        [pytest.param(True, id="record-1"), pytest.param(False, id="record-1-reads-unrecorded")],
    )
    async def test_success(
        self, bucket_db: ExtendedAsyncSAEngine, actors: Actors, world: _World, record_reads: bool
    ) -> None:
        harness = OpsHarness(bucket_db, record_reads=record_reads)

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_search([world.granted]))

        records = await harness.audit(SearchDomainUsageBucketsAction.action_name())
        expected = [
            (
                str(DomainEntityType()),
                None,
                OperationStatus.SUCCESS,
                frozenset({entity_key(world.granted)}),
            )
        ]
        assert _record(records) == (expected if record_reads else [])
        assert all(r.operation == ActionOperationType.SEARCH for r in records)

    @pytest.mark.parametrize(
        ("actor", "exists", "status"),
        [
            pytest.param(Actor.UNGRANTED, True, OperationStatus.DENIED, id="record-2"),
            pytest.param(Actor.SUPERADMIN, False, OperationStatus.ERROR, id="record-3"),
            pytest.param(
                Actor.ANONYMOUS,
                True,
                OperationStatus.DENIED,
                id="record-4",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_a_failure_is_one_row_tied_to_the_owner(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        world: _World,
        actor: Actor,
        exists: bool,
        status: OperationStatus,
    ) -> None:
        owner = world.granted if exists else ResourceGroupID(uuid.uuid4())

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_search([owner]))

        records = await silent_reads_harness.audit(SearchDomainUsageBucketsAction.action_name())
        assert _record(records) == [
            (str(DomainEntityType()), None, status, frozenset({entity_key(owner)}))
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        harness: OpsHarness,
        actors: Actors,
        world: _World,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "checked_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_search([world.granted]))

        records = await harness.audit(SearchDomainUsageBucketsAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]


class TestResult:
    async def test_the_page_names_no_entity(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _search([world.granted], PaginationOptions(first=_PAGE_SIZE))
            )

        assert all(isinstance(item, DomainUsageBucketData) for item in result.items)
        assert all(item.resource_group_id == world.granted for item in result.items)
        assert (result.total_count, result.has_next_page, result.has_previous_page) == (
            len(world.rows[world.granted]),
            True,
            False,
        )
        assert result.entity_ids() == ()
