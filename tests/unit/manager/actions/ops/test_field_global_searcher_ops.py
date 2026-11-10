"""``global_searcher_ops`` over field rows, with the keypair (owned by a user).

scope-1 is not applicable: only entity searchable fields declare a use, no field row's does.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Callable, Sequence
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.keypair import KeyPairFieldType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import AccessKey, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
    build_orders,
    build_pagination,
)
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.keypair.searchable_fields import KeyPairSearchableFields
from ai.backend.manager.models.keypair.searchers import KeyPairSearcher
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.services.user.actions.keypair_ops import AdminSearchKeypairsAction
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupBulkKeypairOwnerAction,
    LookupKeypairOwnerAction,
)
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
    forward_order=KeyPairSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=KeyPairRow.id,
)
_PAGE_SIZE = 2
_KEYPAIR_COUNT = 5


async def _grant_global(
    db: ExtendedAsyncSAEngine, user_id: UserID, entity_type: EntityType, permission: Permission
) -> None:
    scope = global_entity_id(GlobalEntityName.GLOBAL)
    await grant(db, user_id, scope.entity_type(), scope, entity_type, permission)


async def _seed_keypairs(
    db: ExtendedAsyncSAEngine, owner: UserID, count: int, *, one_transaction: bool
) -> list[AccessKey]:
    """Keypairs of one user; one transaction gives them one ``created_at``."""
    policy = f"keypair-policy-{uuid.uuid4().hex[:8]}"
    async with db.begin_session() as sess:
        sess.add(
            KeyPairResourcePolicyRow(
                name=policy,
                total_resource_slots=ResourceSlot(),
                max_concurrent_sessions=1,
                max_containers_per_session=1,
                idle_timeout=0,
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
            )
        )
        await sess.commit()
    access_keys = [AccessKey(f"AK{uuid.uuid4().hex[:18].upper()}") for _ in range(count)]
    batches = [access_keys] if one_transaction else [[access_key] for access_key in access_keys]
    for batch in batches:
        async with db.begin_session() as sess:
            sess.add_all([
                KeyPairRow(
                    user=owner,
                    access_key=access_key,
                    secret_key=SecretValue("secret"),
                    is_active=True,
                    is_admin=False,
                    resource_policy=policy,
                    rate_limit=1000,
                )
                for access_key in batch
            ])
            await sess.commit()
    return access_keys


async def _display_order(db: ExtendedAsyncSAEngine) -> list[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        return list(
            (
                await sess.scalars(
                    sa.select(KeyPairRow.id).order_by(
                        KeyPairRow.created_at.desc(), KeyPairRow.id.asc()
                    )
                )
            ).all()
        )


@pytest.fixture
async def keypairs(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> list[AccessKey]:
    access_keys = await _seed_keypairs(
        ops_db, actors.user_id(Actor.UNGRANTED), _KEYPAIR_COUNT, one_transaction=False
    )
    await _grant_global(ops_db, actors.user_id(Actor.GRANTED), UserEntityType(), Permission.READ)
    return access_keys


def _processor(harness: OpsHarness) -> Any:
    keypair_group = harness.group(UserEntityType()).field_group(
        FieldGroupMeta(KeyPairFieldType()),
        KeyPairData,
        LookupKeypairOwnerAction,
        LookupBulkKeypairOwnerAction,
    )
    return keypair_group.global_searcher_ops(AdminSearchKeypairsAction)


def _search(
    options: PaginationOptions | None = None,
    conditions: Sequence[QueryCondition] = (),
) -> AdminSearchKeypairsAction:
    options = options or PaginationOptions(limit=100)
    return AdminSearchKeypairsAction(
        searcher=GlobalSearcher(
            used_by=(),
            searcher=KeyPairSearcher(
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
        keypairs: list[AccessKey],
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
                assert {item.access_key for item in result.items} == set(keypairs)
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_search())
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)
        if error is not None:
            assert reads == []

    @pytest.mark.parametrize(
        ("at_global", "entity_type"),
        [
            pytest.param(False, UserEntityType(), id="actor-4"),
            pytest.param(True, ProjectEntityType(), id="actor-5"),
        ],
    )
    async def test_a_grant_off_the_global_owner_type_is_refused(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        keypairs: list[AccessKey],
        at_global: bool,
        entity_type: EntityType,
    ) -> None:
        """A domain grant on users, or a global grant on another type, is not enough."""
        user_id = actors.user_id(Actor.UNGRANTED)
        if at_global:
            await _grant_global(ops_db, user_id, entity_type, Permission.full())
        else:
            await grant(
                ops_db,
                user_id,
                DomainEntityType(),
                actors.domain_id,
                entity_type,
                Permission.full(),
            )

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(InsufficientPrivilege):
                await _processor(harness).run(_search())


async def _walk_forward(harness: OpsHarness) -> list[Any]:
    pages = [await _page(harness, PaginationOptions(first=_PAGE_SIZE))]
    while pages[-1].has_next_page and len(pages) <= _KEYPAIR_COUNT:
        after = encode_cursor(pages[-1].items[-1].id)
        pages.append(await _page(harness, PaginationOptions(first=_PAGE_SIZE, after=after)))
    return pages


async def _walk_backward(harness: OpsHarness) -> list[Any]:
    pages = [await _page(harness, PaginationOptions(last=_PAGE_SIZE))]
    while pages[-1].has_previous_page and len(pages) <= _KEYPAIR_COUNT:
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
        keypairs: list[AccessKey],
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
        keypairs: list[AccessKey],
    ) -> None:
        """page-2."""
        with actors.acting_as(Actor.GRANTED):
            pages = await _walk_forward(harness)

        assert _ids(pages) == await _display_order(ops_db)
        assert [page.has_previous_page for page in pages[1:]] == [True] * (len(pages) - 1)
        assert [page.has_next_page for page in pages] == [True] * (len(pages) - 1) + [False]

    async def test_the_first_backward_page_flags(
        self, harness: OpsHarness, actors: Actors, keypairs: list[AccessKey]
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
        keypairs: list[AccessKey],
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
        keypairs: list[AccessKey],
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
        tied = await _seed_keypairs(
            ops_db, actors.user_id(Actor.UNGRANTED), _KEYPAIR_COUNT, one_transaction=True
        )

        with actors.acting_as(Actor.SUPERADMIN):
            pages = await _walk_forward(harness)

        seen = [item.access_key for page in pages for item in page.items]
        assert sorted(seen) == sorted(tied)

    @_BACKWARD_PAGE_REVERSED
    async def test_backward_pages_over_tied_rows(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """page-5, backward."""
        tied = await _seed_keypairs(
            ops_db, actors.user_id(Actor.UNGRANTED), _KEYPAIR_COUNT, one_transaction=True
        )

        with actors.acting_as(Actor.SUPERADMIN):
            pages = await _walk_backward(harness)

        seen = [item.access_key for page in pages for item in page.items]
        assert sorted(seen) == sorted(tied)

    async def test_offset_pages_run_to_the_end(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        keypairs: list[AccessKey],
    ) -> None:
        """page-6."""
        pages = []
        with actors.acting_as(Actor.GRANTED):
            for offset in range(0, _KEYPAIR_COUNT, _PAGE_SIZE):
                pages.append(
                    await _page(harness, PaginationOptions(limit=_PAGE_SIZE, offset=offset))
                )

        assert _ids(pages) == await _display_order(ops_db)
        assert [page.has_previous_page for page in pages] == [False] + [True] * (len(pages) - 1)
        assert [page.has_next_page for page in pages] == [True] * (len(pages) - 1) + [False]

    async def test_an_offset_past_the_end(
        self, harness: OpsHarness, actors: Actors, keypairs: list[AccessKey]
    ) -> None:
        """page-7."""
        with actors.acting_as(Actor.GRANTED):
            page = await _page(harness, PaginationOptions(limit=_PAGE_SIZE, offset=100))

        assert page.items == []
        assert page.total_count == _KEYPAIR_COUNT

    async def test_the_count_ignores_the_page(
        self, harness: OpsHarness, actors: Actors, keypairs: list[AccessKey]
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

        assert [p.total_count for p in (first, after, before, small)] == [_KEYPAIR_COUNT] * 4


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
        keypairs: list[AccessKey],
        record_reads: bool,
        expected: list[OperationStatus],
    ) -> None:
        harness = OpsHarness(ops_db, record_reads=record_reads)

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_search())

        records = await harness.audit(AdminSearchKeypairsAction.action_name())
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
        keypairs: list[AccessKey],
        actor: Actor,
        fails: bool,
        status: OperationStatus,
    ) -> None:
        """A failure is recorded whatever the read policy says."""
        action = _search(conditions=[_failing] if fails else [])

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(action)

        records = await silent_reads_harness.audit(AdminSearchKeypairsAction.action_name())
        assert [(r.entity_type, r.entity_id, r.status) for r in records] == [
            (str(GlobalEntityType()), None, status)
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        harness: OpsHarness,
        actors: Actors,
        keypairs: list[AccessKey],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "governed_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_search())

        records = await harness.audit(AdminSearchKeypairsAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]


class TestResult:
    async def test_the_page_holds_field_rows_and_its_flags(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        keypairs: list[AccessKey],
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _page(harness, PaginationOptions(limit=_PAGE_SIZE, offset=_PAGE_SIZE))

        order = await _display_order(ops_db)
        assert all(isinstance(item, KeyPairData) for item in result.items)
        assert [item.id for item in result.items] == order[_PAGE_SIZE : 2 * _PAGE_SIZE]
        assert {item.user_id for item in result.items} == {actors.user_id(Actor.UNGRANTED)}
        assert result.total_count == _KEYPAIR_COUNT
        assert (result.has_previous_page, result.has_next_page) == (True, True)
