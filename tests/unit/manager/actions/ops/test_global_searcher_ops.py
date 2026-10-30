"""``global_searcher_ops`` over entities, with the project as the representative.

The project searcher declares no use, so the narrowing row runs on the role preset,
whose searcher is narrowed by the roles instantiated from it.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator, Callable, Sequence
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.role_preset import RolePresetEntityType, RolePresetID
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
    build_orders,
    build_pagination,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.searchable_fields import ProjectSearchableFields
from ai.backend.manager.models.project.searchers import ProjectSearcher
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.role_preset.searchable_fields import (
    RolePresetSearchableFields,
)
from ai.backend.manager.models.rbac_models.role_preset.searchers import RolePresetSearcher
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.specs.search.usage import UsedBy
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.project.actions.search_projects import (
    GlobalSearchProjectsAction,
)
from ai.backend.manager.services.role_preset.actions.search import SearchRolePresetsAction
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    grant,
)

_BACKWARD_PAGE_REVERSED = pytest.mark.xfail(
    strict=True, reason="a backward cursor page comes back in reverse display order"
)

_PAGINATION_SPEC = PaginationSpec(
    forward_order=ProjectSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=ProjectRow.id,
)
_PAGE_SIZE = 2
_PROJECT_COUNT = 5


async def _grant_global(
    db: ExtendedAsyncSAEngine, user_id: UserID, entity_type: EntityType, permission: Permission
) -> None:
    scope = global_entity_id(GlobalEntityName.GLOBAL)
    await grant(db, user_id, scope.entity_type(), scope, entity_type, permission)


async def _seed_projects(
    db: ExtendedAsyncSAEngine, actors: Actors, count: int, *, one_transaction: bool
) -> list[ProjectID]:
    """Projects in the actors' domain; one transaction gives them one ``created_at``."""
    policy = f"project-policy-{uuid.uuid4().hex[:8]}"
    async with db.begin_session() as sess:
        sess.add(
            ProjectResourcePolicyRow(
                name=policy, max_vfolder_count=0, max_quota_scope_size=-1, max_network_count=0
            )
        )
        await sess.commit()
    project_ids = [ProjectID(uuid.uuid4()) for _ in range(count)]
    batches = [project_ids] if one_transaction else [[project_id] for project_id in project_ids]
    for batch in batches:
        async with db.begin_session() as sess:
            sess.add_all([
                ProjectRow(
                    id=project_id,
                    name=f"project-{project_id.hex[:8]}",
                    description=None,
                    is_active=True,
                    domain_name=actors.domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    integration_id=None,
                    resource_policy=policy,
                    type=ProjectType.GENERAL,
                )
                for project_id in batch
            ])
            await sess.commit()
    return project_ids


async def _display_order(db: ExtendedAsyncSAEngine) -> list[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        return list(
            (
                await sess.scalars(
                    sa.select(ProjectRow.id).order_by(
                        ProjectRow.created_at.desc(), ProjectRow.id.asc()
                    )
                )
            ).all()
        )


@pytest.fixture
async def projects(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> list[ProjectID]:
    project_ids = await _seed_projects(ops_db, actors, _PROJECT_COUNT, one_transaction=False)
    await _grant_global(ops_db, actors.user_id(Actor.GRANTED), ProjectEntityType(), Permission.READ)
    return project_ids


def _processor(harness: OpsHarness) -> Any:
    return harness.group(ProjectEntityType()).global_searcher_ops(GlobalSearchProjectsAction)


def _search(
    options: PaginationOptions | None = None,
    conditions: Sequence[QueryCondition] = (),
) -> GlobalSearchProjectsAction:
    options = options or PaginationOptions(limit=100)
    return GlobalSearchProjectsAction(
        searcher=GlobalSearcher(
            used_by=(),
            searcher=ProjectSearcher(
                pagination=build_pagination(options, _PAGINATION_SPEC),
                conditions=list(conditions),
                orders=build_orders(options, _PAGINATION_SPEC, []),
            ),
        )
    )


async def _page(harness: OpsHarness, options: PaginationOptions) -> Any:
    return await _processor(harness).run(_search(options))


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced", "error"),
        [
            pytest.param(Actor.SUPERADMIN, True, None, id="actor-1"),
            pytest.param(Actor.MONITOR, True, None, id="actor-2"),
            pytest.param(Actor.GRANTED, True, None, id="actor-3"),
            pytest.param(Actor.UNGRANTED, True, InsufficientPrivilege, id="actor-6"),
            pytest.param(
                Actor.ANONYMOUS, True, BackendAIError, id="actor-7", marks=ANONYMOUS_NOT_REFUSED
            ),
            pytest.param(
                Actor.ANONYMOUS,
                False,
                BackendAIError,
                id="actor-7-rbac-off",
                marks=ANONYMOUS_NOT_REFUSED,
            ),
            pytest.param(Actor.SUPERADMIN, False, None, id="actor-8"),
            pytest.param(Actor.MONITOR, False, None, id="actor-9"),
            pytest.param(Actor.GRANTED, False, InsufficientPrivilege, id="actor-10"),
        ],
    )
    async def test_actor(
        self,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        repository_calls: Callable[[str], list[Any]],
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)
        reads = repository_calls("global_search")

        with actors.acting_as(actor):
            if error is None:
                result = await _processor(harness).run(_search())
                assert {item.id for item in result.items} == set(projects)
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_search())
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)
        if error is not None:
            assert reads == []

    @pytest.mark.parametrize(
        ("scope_type", "entity_type"),
        [
            pytest.param(DomainEntityType(), ProjectEntityType(), id="actor-4"),
            pytest.param(GlobalEntityType(), UserEntityType(), id="actor-5"),
        ],
    )
    async def test_a_grant_off_the_global_type_is_refused(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        scope_type: EntityType,
        entity_type: EntityType,
    ) -> None:
        """A domain grant on projects, or a global grant on another type, is not enough."""
        user_id = actors.user_id(Actor.UNGRANTED)
        if isinstance(scope_type, GlobalEntityType):
            await _grant_global(ops_db, user_id, entity_type, Permission.full())
        else:
            await grant(
                ops_db, user_id, scope_type, actors.domain_id, entity_type, Permission.full()
            )

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(InsufficientPrivilege):
                await _processor(harness).run(_search())


@pytest.fixture
async def preset_db(ops_db: ExtendedAsyncSAEngine) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(ops_db, [RolePresetRow]):
        yield ops_db


class TestScope:
    async def test_a_use_narrows_to_the_rows_it_uses(
        self, preset_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """scope-1: the caller holds nothing on the role that uses the preset."""
        used, unused = RolePresetID(uuid.uuid4()), RolePresetID(uuid.uuid4())
        role_id = RoleID(uuid.uuid4())
        async with preset_db.begin_session() as sess:
            sess.add_all([
                RolePresetRow(
                    id=preset_id,
                    name=f"preset-{preset_id.hex[:8]}",
                    scope_type=DomainEntityType(),
                )
                for preset_id in (used, unused)
            ])
            await sess.flush()
            sess.add(
                RoleRow(
                    id=role_id,
                    name=f"role-{role_id.hex[:8]}",
                    status=RoleStatus.ACTIVE,
                    scope_type=DomainEntityType(),
                    scope_id=actors.domain_id,
                    role_preset_id=used,
                )
            )
            await sess.commit()
        await _grant_global(
            preset_db, actors.user_id(Actor.GRANTED), RolePresetEntityType(), Permission.READ
        )
        uses: list[UsedBy] = [RolePresetSearchableFields.linked.usage.roles.used_by(role_id)]
        action = SearchRolePresetsAction(
            searcher=GlobalSearcher(
                used_by=uses, searcher=RolePresetSearcher(pagination=OffsetPagination(limit=10))
            )
        )
        processor = harness.group(RolePresetEntityType()).global_searcher_ops(
            SearchRolePresetsAction
        )

        with actors.acting_as(Actor.GRANTED):
            result = await processor.run(action)

        assert [item.id for item in result.items] == [used]

    async def test_no_narrowing_reads_the_whole_table(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """scope-2."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_search())

        assert {item.id for item in result.items} == set(projects)
        assert result.total_count == _PROJECT_COUNT


async def _walk_forward(harness: OpsHarness) -> list[Any]:
    pages = [await _page(harness, PaginationOptions(first=_PAGE_SIZE))]
    while pages[-1].has_next_page and len(pages) <= _PROJECT_COUNT:
        after = encode_cursor(pages[-1].items[-1].id)
        pages.append(await _page(harness, PaginationOptions(first=_PAGE_SIZE, after=after)))
    return pages


async def _walk_backward(harness: OpsHarness) -> list[Any]:
    pages = [await _page(harness, PaginationOptions(last=_PAGE_SIZE))]
    while pages[-1].has_previous_page and len(pages) <= _PROJECT_COUNT:
        before = encode_cursor(pages[-1].items[0].id)
        pages.append(await _page(harness, PaginationOptions(last=_PAGE_SIZE, before=before)))
    return pages


def _ids(pages: Sequence[Any]) -> list[uuid.UUID]:
    return [item.id for page in pages for item in page.items]


class TestPage:
    async def test_the_first_forward_page(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """page-1."""
        with actors.acting_as(Actor.GRANTED):
            page = await _page(harness, PaginationOptions(first=_PAGE_SIZE))

        assert [item.id for item in page.items] == (await _display_order(ops_db))[:_PAGE_SIZE]
        assert (page.has_previous_page, page.has_next_page) == (False, True)

    async def test_forward_pages_run_to_the_end(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """page-2."""
        with actors.acting_as(Actor.GRANTED):
            pages = await _walk_forward(harness)

        assert _ids(pages) == await _display_order(ops_db)
        assert [page.has_previous_page for page in pages[1:]] == [True] * (len(pages) - 1)
        assert [page.has_next_page for page in pages] == [True] * (len(pages) - 1) + [False]

    async def test_the_first_backward_page_flags(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """page-3: the page flags."""
        with actors.acting_as(Actor.GRANTED):
            page = await _page(harness, PaginationOptions(last=_PAGE_SIZE))

        assert (page.has_previous_page, page.has_next_page) == (True, False)

    @_BACKWARD_PAGE_REVERSED
    async def test_the_first_backward_page_is_the_last_rows_in_display_order(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """page-3: the items."""
        with actors.acting_as(Actor.GRANTED):
            page = await _page(harness, PaginationOptions(last=_PAGE_SIZE))

        assert [item.id for item in page.items] == (await _display_order(ops_db))[-_PAGE_SIZE:]

    @_BACKWARD_PAGE_REVERSED
    async def test_backward_pages_run_to_the_start(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """page-4."""
        with actors.acting_as(Actor.GRANTED):
            pages = await _walk_backward(harness)

        assert _ids(list(reversed(pages))) == await _display_order(ops_db)
        assert [page.has_next_page for page in pages[1:]] == [True] * (len(pages) - 1)
        assert [page.has_previous_page for page in pages] == [True] * (len(pages) - 1) + [False]

    async def test_forward_pages_over_tied_rows(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """page-5, forward."""
        tied = await _seed_projects(ops_db, actors, _PROJECT_COUNT, one_transaction=True)

        with actors.acting_as(Actor.SUPERADMIN):
            seen = _ids(await _walk_forward(harness))

        assert sorted(seen) == sorted(tied)

    @_BACKWARD_PAGE_REVERSED
    async def test_backward_pages_over_tied_rows(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """page-5, backward."""
        tied = await _seed_projects(ops_db, actors, _PROJECT_COUNT, one_transaction=True)

        with actors.acting_as(Actor.SUPERADMIN):
            seen = _ids(await _walk_backward(harness))

        assert sorted(seen) == sorted(tied)

    async def test_offset_pages_run_to_the_end(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """page-6."""
        pages = []
        with actors.acting_as(Actor.GRANTED):
            for offset in range(0, _PROJECT_COUNT, _PAGE_SIZE):
                pages.append(
                    await _page(harness, PaginationOptions(limit=_PAGE_SIZE, offset=offset))
                )

        assert _ids(pages) == await _display_order(ops_db)
        assert [page.has_previous_page for page in pages] == [False] + [True] * (len(pages) - 1)
        assert [page.has_next_page for page in pages] == [True] * (len(pages) - 1) + [False]

    async def test_an_offset_past_the_end(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """page-7."""
        with actors.acting_as(Actor.GRANTED):
            page = await _page(harness, PaginationOptions(limit=_PAGE_SIZE, offset=100))

        assert page.items == []
        assert page.total_count == _PROJECT_COUNT

    async def test_the_count_ignores_the_page(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """page-8."""
        with actors.acting_as(Actor.GRANTED):
            first = await _page(harness, PaginationOptions(first=1))
            after = await _page(
                harness, PaginationOptions(first=1, after=encode_cursor(first.items[0].id))
            )
            before = await _page(
                harness, PaginationOptions(last=1, before=encode_cursor(first.items[0].id))
            )
            small = await _page(harness, PaginationOptions(limit=1))

        assert [p.total_count for p in (first, after, before, small)] == [_PROJECT_COUNT] * 4


def _failing() -> sa.sql.expression.ColumnElement[bool]:
    raise RuntimeError("the search failed")


class TestRecord:
    @pytest.mark.parametrize(
        ("record_reads", "expected"),
        [
            pytest.param(True, [OperationStatus.SUCCESS], id="record-1"),
            pytest.param(False, [], id="record-1-unrecorded"),
        ],
    )
    async def test_a_success(
        self,
        ops_db: ExtendedAsyncSAEngine,
        actors: Actors,
        projects: list[ProjectID],
        record_reads: bool,
        expected: list[OperationStatus],
    ) -> None:
        harness = OpsHarness(ops_db, record_reads=record_reads)

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_search())

        records = await harness.audit(GlobalSearchProjectsAction.action_name())
        assert [(r.entity_type, r.entity_id, r.operation, r.status) for r in records] == [
            (str(GlobalEntityType()), None, ActionOperationType.SEARCH, status)
            for status in expected
        ]

    @pytest.mark.parametrize(
        ("actor", "fails", "status"),
        [
            pytest.param(Actor.UNGRANTED, False, OperationStatus.DENIED, id="record-2"),
            pytest.param(Actor.GRANTED, True, OperationStatus.ERROR, id="record-3"),
            pytest.param(
                Actor.ANONYMOUS,
                False,
                OperationStatus.DENIED,
                id="record-4",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_a_failure(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        actor: Actor,
        fails: bool,
        status: OperationStatus,
    ) -> None:
        """A failure is recorded whatever the read policy says."""
        action = _search(conditions=[_failing] if fails else [])

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(action)

        records = await silent_reads_harness.audit(GlobalSearchProjectsAction.action_name())
        assert [(r.entity_type, r.entity_id, r.status) for r in records] == [
            (str(GlobalEntityType()), None, status)
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "governed_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_search())

        records = await harness.audit(GlobalSearchProjectsAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]


class TestResult:
    async def test_the_page_and_its_flags(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _page(harness, PaginationOptions(limit=_PAGE_SIZE, offset=_PAGE_SIZE))

        order = await _display_order(ops_db)
        assert [item.id for item in result.items] == order[_PAGE_SIZE : 2 * _PAGE_SIZE]
        assert result.total_count == _PROJECT_COUNT
        assert (result.has_previous_page, result.has_next_page) == (True, True)
