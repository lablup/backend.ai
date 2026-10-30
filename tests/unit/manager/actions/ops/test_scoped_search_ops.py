"""``scoped_search_ops``: a page read within named scopes, with the project as the representative.

Projects declare no use to narrow by, so the used-by rows run on the model card, whose
searcher narrows by the vfolder a card is built on.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from aiohttp import web

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.model_card import ModelCardEntityType, ModelCardID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    ResourceSlot,
    VFolderHostPermissionMap,
    VFolderMountPolicy,
    VFolderUsageMode,
)
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.ops.result import ScopedBatchOpsResult
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
    build_orders,
    build_pagination,
)
from ai.backend.manager.data.project.types import ProjectData, ProjectStatus, ProjectType
from ai.backend.manager.data.vfolder.types import (
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import EmptyOperationScopeError
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.model_card.scopes import DomainModelCardTarget
from ai.backend.manager.models.model_card.searchable_fields import ModelCardSearchableFields
from ai.backend.manager.models.model_card.searchers import ModelCardSearcher
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.scopes import DomainProjectTarget, ProjectTarget
from ai.backend.manager.models.project.searchable_fields import ProjectSearchableFields
from ai.backend.manager.models.project.searchers import ProjectSearcher
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.specs.searcher import ScopedSearcher
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.model_card.actions.scoped_search import (
    ScopedSearchModelCardsAction,
)
from ai.backend.manager.services.project.actions.scoped_search import ScopedSearchProjectsAction
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
    seed_project,
)
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

_SCOPE_WITHOUT_NODE_READS_NOTHING = pytest.mark.xfail(
    strict=True, reason="scope conditions walk the graph, so a scope with no node reaches no row"
)
_BACKWARD_PAGE_IN_REVERSE = pytest.mark.xfail(
    strict=True, reason="a backward cursor page comes back in reverse display order"
)

_PAGINATION_SPEC = PaginationSpec(
    forward_order=ProjectSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=ProjectRow.id,
)
_PAGE_SIZE = 2
_ROW_COUNT = 5


def _searcher(options: PaginationOptions | None = None) -> ProjectSearcher:
    options = options or PaginationOptions(limit=100)
    return ProjectSearcher(
        pagination=build_pagination(options, _PAGINATION_SPEC),
        orders=build_orders(options, _PAGINATION_SPEC, []),
    )


def _action(
    scopes: Sequence[ProjectTarget], options: PaginationOptions | None = None
) -> ScopedSearchProjectsAction:
    return ScopedSearchProjectsAction(
        searcher=ScopedSearcher(scopes=list(scopes), used_by=(), searcher=_searcher(options))
    )


def _in(*domains: DomainID) -> list[ProjectTarget]:
    return [DomainProjectTarget(domain_id=domain) for domain in domains]


def _processor(harness: OpsHarness) -> Any:
    return harness.group(ProjectEntityType()).scoped_search_ops(ScopedSearchProjectsAction)


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


async def _seed_project(
    db: ExtendedAsyncSAEngine,
    domain_id: DomainID,
    created_in: Sequence[DomainID],
    created_at: datetime | None = None,
) -> ProjectID:
    """A project whose row names ``domain_id`` and whose node is created in ``created_in``."""
    project_id = ProjectID(uuid.uuid4())
    policy = f"project-policy-{project_id.hex[:8]}"
    async with db.begin_session() as sess:
        sess.add(
            ProjectResourcePolicyRow(
                name=policy, max_vfolder_count=0, max_quota_scope_size=-1, max_network_count=0
            )
        )
        await sess.flush()
        row = ProjectRow(
            id=project_id,
            name=f"project-{project_id.hex[:8]}",
            description=None,
            is_active=True,
            status=ProjectStatus.ACTIVE,
            domain_name=DomainName(f"domain-{domain_id.hex[:8]}"),
            total_resource_slots=ResourceSlot(),
            allowed_vfolder_hosts=VFolderHostPermissionMap(),
            integration_id=None,
            resource_policy=policy,
            type=ProjectType.GENERAL,
        )
        if created_at is not None:
            row.created_at = created_at
        sess.add(row)
        await sess.flush()
        seeder = VirtualEntitySeeder()
        if created_in:
            await seeder.create_in(
                sess,
                ProjectEntityType(),
                project_id,
                [(DomainEntityType(), domain) for domain in created_in],
            )
        else:
            await seeder.provision(sess, ProjectEntityType(), project_id)
        await sess.commit()
    return project_id


@dataclass(frozen=True)
class _World:
    """Three domains in the graph; the granted user reads projects in the first two.

    ``shared`` is created in both ``a`` and ``b``.
    """

    a: DomainID
    b: DomainID
    c: DomainID
    in_a: tuple[ProjectID, ...]
    in_b: tuple[ProjectID, ...]
    shared: ProjectID


@pytest.fixture
async def world(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> _World:
    a = actors.domain_id
    b = await _seed_domain(ops_db)
    c = await _seed_domain(ops_db)
    in_a = (await _seed_project(ops_db, b, [a]), await _seed_project(ops_db, b, [a]))
    in_b = (await _seed_project(ops_db, b, [b]),)
    shared = await _seed_project(ops_db, b, [a, b])
    await _seed_project(ops_db, c, [c])
    for domain in (a, b):
        await grant(
            ops_db,
            actors.user_id(Actor.GRANTED),
            DomainEntityType(),
            domain,
            ProjectEntityType(),
            Permission.READ,
        )
    await grant(
        ops_db,
        actors.user_id(Actor.READ_ONLY),
        DomainEntityType(),
        a,
        UserEntityType(),
        Permission.READ,
    )
    return _World(a=a, b=b, c=c, in_a=in_a, in_b=in_b, shared=shared)


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
        searches = repository_calls("scoped_search")
        action = _action(_in(world.a))

        with actors.acting_as(actor):
            if error is None:
                result = await _processor(harness).run(action)
                assert {item.id for item in result.items} == {*world.in_a, world.shared}
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(action)
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)
                assert searches == []


class TestScope:
    async def test_two_granted_scopes_read_their_union_once(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """scope-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_action(_in(world.a, world.b)))

        ids = [item.id for item in result.items]
        assert len(ids) == len(set(ids))
        assert set(ids) == {*world.in_a, *world.in_b, world.shared}
        assert result.total_count == len(ids)

    async def test_one_ungranted_scope_refuses_the_whole_read(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """scope-2."""
        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_action(_in(world.a, world.c)))

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
                await _processor(harness).run(_action(_in(DomainID(uuid.uuid4()))))

    @_SCOPE_WITHOUT_NODE_READS_NOTHING
    async def test_a_superadmin_reads_a_scope_outside_the_graph(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """scope-5: the projects whose row names the domain."""
        outside = await _seed_domain(ops_db, in_graph=False)
        inside = {await _seed_project(ops_db, outside, []) for _ in range(2)}

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(_action(_in(outside)))

        assert {item.id for item in result.items} == inside

    async def test_a_user_is_refused_a_scope_outside_the_graph(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """scope-5."""
        outside = await _seed_domain(ops_db, in_graph=False)
        await _seed_project(ops_db, outside, [])

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_action(_in(outside)))

    @pytest.mark.parametrize("actor", [Actor.SUPERADMIN, Actor.GRANTED])
    async def test_no_scope_is_refused_rather_than_widened(
        self, harness: OpsHarness, actors: Actors, world: _World, actor: Actor
    ) -> None:
        """scope-6."""
        with actors.acting_as(actor):
            with pytest.raises(EmptyOperationScopeError):
                await _processor(harness).run(_action([]))


@dataclass(frozen=True)
class _Cards:
    """Cards in the actors' domain; ``readable`` is the vfolder the granted user reads."""

    readable: VFolderUUID
    unreadable: VFolderUUID
    on_readable: frozenset[ModelCardID]
    on_unreadable: frozenset[ModelCardID]


async def _seed_vfolder(
    db: ExtendedAsyncSAEngine, actors: Actors, project_id: ProjectID
) -> VFolderUUID:
    vfolder_id = VFolderUUID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            VFolderRow(
                id=vfolder_id,
                name=f"vfolder-{vfolder_id.hex[:8]}",
                host="local:volume1",
                domain_name=actors.domain_name,
                quota_scope_id=QuotaScopeID(QuotaScopeType.PROJECT, project_id),
                usage_mode=VFolderUsageMode.MODEL,
                default_mount_permission=VFolderMountPolicy.READ_WRITE,
                max_files=0,
                max_size=None,
                num_files=0,
                cur_size=0,
                creator="creator@test.com",
                unmanaged_path=None,
                ownership_type=VFolderOwnershipType.GROUP,
                user=None,
                group=project_id,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )
        )
        await sess.commit()
    return vfolder_id


async def _seed_card(
    db: ExtendedAsyncSAEngine, actors: Actors, project_id: ProjectID, vfolder_id: VFolderUUID
) -> ModelCardID:
    card_id = ModelCardID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            ModelCardRow(
                id=card_id,
                name=f"card-{card_id.hex[:8]}",
                vfolder=vfolder_id,
                domain=actors.domain_name,
                project=project_id,
                creator=actors.user_id(Actor.SUPERADMIN),
            )
        )
        await sess.commit()
    await provision(db, ModelCardEntityType(), card_id, [(ProjectEntityType(), project_id)])
    return card_id


@pytest.fixture
async def cards(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> _Cards:
    project_id = await seed_project(ops_db, actors, project_type=ProjectType.MODEL_STORE)
    readable = await _seed_vfolder(ops_db, actors, project_id)
    unreadable = await _seed_vfolder(ops_db, actors, project_id)
    on_readable = frozenset([
        await _seed_card(ops_db, actors, project_id, readable),
        await _seed_card(ops_db, actors, project_id, readable),
    ])
    on_unreadable = frozenset([await _seed_card(ops_db, actors, project_id, unreadable)])
    granted = actors.user_id(Actor.GRANTED)
    await grant(
        ops_db,
        granted,
        DomainEntityType(),
        actors.domain_id,
        ModelCardEntityType(),
        Permission.READ,
    )
    await grant(
        ops_db, granted, VFolderEntityType(), readable, VFolderEntityType(), Permission.READ
    )
    return _Cards(
        readable=readable,
        unreadable=unreadable,
        on_readable=on_readable,
        on_unreadable=on_unreadable,
    )


def _cards_used_by(actors: Actors, vfolder_id: VFolderUUID) -> ScopedSearchModelCardsAction:
    return ScopedSearchModelCardsAction(
        searcher=ScopedSearcher(
            scopes=[DomainModelCardTarget(domain_id=actors.domain_id)],
            used_by=[ModelCardSearchableFields.linked.usage.vfolders.uses(vfolder_id)],
            searcher=ModelCardSearcher(pagination=OffsetPagination(limit=100)),
        )
    )


def _card_processor(harness: OpsHarness) -> Any:
    return harness.group(ModelCardEntityType()).scoped_search_ops(ScopedSearchModelCardsAction)


class TestUsedBy:
    @pytest.mark.parametrize(
        "actor",
        [
            pytest.param(Actor.GRANTED, id="scope-7"),
            pytest.param(Actor.SUPERADMIN, id="scope-9"),
        ],
    )
    async def test_only_the_rows_the_use_reaches(
        self, harness: OpsHarness, actors: Actors, cards: _Cards, actor: Actor
    ) -> None:
        with actors.acting_as(actor):
            result = await _card_processor(harness).run(_cards_used_by(actors, cards.readable))

        assert {item.id for item in result.items} == cards.on_readable
        assert result.total_count == len(cards.on_readable)

    async def test_an_unreadable_use_refuses_the_whole_read(
        self, harness: OpsHarness, actors: Actors, cards: _Cards
    ) -> None:
        """scope-8."""
        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _card_processor(harness).run(_cards_used_by(actors, cards.unreadable))


@dataclass(frozen=True)
class _Rows:
    domain_id: DomainID
    display_order: tuple[ProjectID, ...]


async def _seed_rows(db: ExtendedAsyncSAEngine, *, tied: bool) -> _Rows:
    """Projects in a fresh domain; ``tied`` gives them all one ``created_at``."""
    domain_id = await _seed_domain(db)
    base = datetime(2026, 1, 1, tzinfo=UTC)
    created: list[tuple[datetime, ProjectID]] = []
    for index in range(_ROW_COUNT):
        created_at = base if tied else base + timedelta(minutes=index)
        created.append((created_at, await _seed_project(db, domain_id, [domain_id], created_at)))
    # Forward order: created_at DESC, then id ASC.
    ordered = sorted(created, key=lambda pair: (-pair[0].timestamp(), pair[1]))
    return _Rows(domain_id=domain_id, display_order=tuple(pid for _, pid in ordered))


@pytest.fixture
async def rows(ops_db: ExtendedAsyncSAEngine) -> _Rows:
    return await _seed_rows(ops_db, tied=False)


async def _page(
    harness: OpsHarness, rows: _Rows, options: PaginationOptions
) -> ScopedBatchOpsResult[ProjectData]:
    result: ScopedBatchOpsResult[ProjectData] = await _processor(harness).run(
        _action(_in(rows.domain_id), options)
    )
    return result


async def _walk_forward(
    harness: OpsHarness, rows: _Rows
) -> list[ScopedBatchOpsResult[ProjectData]]:
    pages = [await _page(harness, rows, PaginationOptions(first=_PAGE_SIZE))]
    while pages[-1].has_next_page and len(pages) <= _ROW_COUNT:
        after = encode_cursor(pages[-1].items[-1].id)
        pages.append(await _page(harness, rows, PaginationOptions(first=_PAGE_SIZE, after=after)))
    return pages


async def _walk_backward(
    harness: OpsHarness, rows: _Rows
) -> list[ScopedBatchOpsResult[ProjectData]]:
    pages = [await _page(harness, rows, PaginationOptions(last=_PAGE_SIZE))]
    while pages[-1].has_previous_page and len(pages) <= _ROW_COUNT:
        # The display-order front of the page, whatever order the page came in.
        front = min(pages[-1].items, key=lambda item: rows.display_order.index(item.id))
        before = encode_cursor(front.id)
        pages.append(await _page(harness, rows, PaginationOptions(last=_PAGE_SIZE, before=before)))
    return pages


def _ids(pages: Sequence[ScopedBatchOpsResult[ProjectData]]) -> list[uuid.UUID]:
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
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """page-5, forward."""
        tied = await _seed_rows(ops_db, tied=True)

        with actors.acting_as(Actor.SUPERADMIN):
            ids = _ids(await _walk_forward(harness, tied))

        assert sorted(ids) == sorted(tied.display_order)

    async def test_tied_rows_backward(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """page-5, backward."""
        tied = await _seed_rows(ops_db, tied=True)

        with actors.acting_as(Actor.SUPERADMIN):
            ids = _ids(await _walk_backward(harness, tied))

        assert sorted(ids) == sorted(tied.display_order)

    async def test_offset_pages_run_to_the_end(
        self, harness: OpsHarness, actors: Actors, rows: _Rows
    ) -> None:
        """page-6."""
        pages: list[tuple[int, ScopedBatchOpsResult[ProjectData]]] = []
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


def _empty_row(domains: Sequence[DomainID], status: OperationStatus) -> tuple[Any, ...]:
    return (
        str(ProjectEntityType()),
        None,
        ActionOperationType.SEARCH,
        status,
        frozenset(entity_key(domain) for domain in domains),
    )


class TestRecord:
    async def test_one_row_per_entity_read(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """record-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_action(_in(world.a, world.b)))

        records = await harness.audit(ScopedSearchProjectsAction.action_name())
        scopes = frozenset([entity_key(world.a), entity_key(world.b)])
        assert sorted(
            ((r.entity_type, r.entity_id), r.operation, r.status, r.scopes) for r in records
        ) == sorted(
            (
                entity_key(ProjectID(item.id)),
                ActionOperationType.SEARCH,
                OperationStatus.SUCCESS,
                scopes,
            )
            for item in result.items
        )

    async def test_a_read_is_not_recorded_unless_opted_in(
        self, silent_reads_harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """record-1, with the read left out of the policy."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(_action(_in(world.a)))

        assert await silent_reads_harness.audit(ScopedSearchProjectsAction.action_name()) == []

    async def test_an_empty_read_leaves_one_row(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """record-2."""
        empty = await _seed_domain(ops_db)

        with actors.acting_as(Actor.SUPERADMIN):
            await _processor(harness).run(_action(_in(empty)))

        records = await harness.audit(ScopedSearchProjectsAction.action_name())
        assert [(r.entity_type, r.entity_id, r.operation, r.status, r.scopes) for r in records] == [
            _empty_row([empty], OperationStatus.SUCCESS)
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
        scope = DomainID(uuid.uuid4()) if missing else world.a

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(harness).run(_action(_in(scope)))

        records = await harness.audit(ScopedSearchProjectsAction.action_name())
        assert [(r.entity_type, r.entity_id, r.operation, r.status, r.scopes) for r in records] == [
            _empty_row([scope], status)
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
                await _processor(harness).run(_action(_in(world.a)))

        records = await harness.audit(ScopedSearchProjectsAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]


class TestResult:
    async def test_the_page_and_its_bounds(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _action(_in(world.a), PaginationOptions(limit=_PAGE_SIZE))
            )

        assert len(result.items) == _PAGE_SIZE
        assert {item.id for item in result.items} <= {*world.in_a, world.shared}
        assert result.total_count == len(world.in_a) + 1
        assert result.has_next_page
        assert not result.has_previous_page
