"""``partial_bulk_get_ops (field)``: reading the named field rows, with roles' permission
entries as the representative.

The permission querier reads every row the owner lookup found, so record-3 drops one row
from the read to make it fail after the lookup.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.permission import PermissionFieldType, PermissionID
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.types import FieldIdentifier
from ai.backend.common.data.permission.types import Permission, RoleSource
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_get_permissions import (
    BulkGetPermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.lookup_permission_owner import (
    LookupBulkRolePermissionOwnerAction,
    LookupRolePermissionOwnerAction,
)
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
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

_NO_ROWS_NAMED_RAISES = pytest.mark.xfail(
    strict=True, reason="a partial field run naming no row raises IndexError"
)
_ALL_ROWS_MISSING_FAILS_THE_RUN = pytest.mark.xfail(
    strict=True, reason="a partial field run whose rows are all missing raises FieldNotFoundError"
)

_OWNER_LOOKUP = LookupBulkRolePermissionOwnerAction.action_name()
_OPERATION = BulkGetPermissionsAction.action_name()


@dataclass(frozen=True)
class _World:
    role_a: RoleID
    role_b: RoleID
    a1: PermissionID
    a2: PermissionID
    b1: PermissionID


async def _seed_role(db: ExtendedAsyncSAEngine, actors: Actors) -> RoleID:
    role_id = RoleID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            RoleRow(
                id=role_id,
                name=f"owner-{role_id.hex[:8]}",
                source=RoleSource.CUSTOM,
                status=RoleStatus.ACTIVE,
                scope_type=DomainEntityType(),
                scope_id=actors.domain_id,
            )
        )
        await sess.commit()
    await provision(db, RoleEntityType(), role_id)
    return role_id


async def _seed_entry(
    db: ExtendedAsyncSAEngine, role_id: RoleID, permission: Permission
) -> PermissionID:
    async with db.begin_session() as sess:
        row = PermissionRow(role_id=role_id, entity_type=DomainEntityType(), permission=permission)
        sess.add(row)
        await sess.flush()
        permission_id = row.id
        await sess.commit()
    return permission_id


@pytest.fixture
async def world(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> _World:
    """Two roles; the read-only actor may read the first alone."""
    role_a = await _seed_role(ops_db, actors)
    role_b = await _seed_role(ops_db, actors)
    for actor, role_id in (
        (Actor.GRANTED, role_a),
        (Actor.GRANTED, role_b),
        (Actor.READ_ONLY, role_a),
    ):
        await grant(
            ops_db,
            actors.user_id(actor),
            RoleEntityType(),
            role_id,
            RoleEntityType(),
            Permission.READ,
        )
    return _World(
        role_a=role_a,
        role_b=role_b,
        a1=await _seed_entry(ops_db, role_a, Permission.READ),
        a2=await _seed_entry(ops_db, role_a, Permission.UPDATE),
        b1=await _seed_entry(ops_db, role_b, Permission.READ),
    )


def _processor(harness: OpsHarness) -> Any:
    permissions = harness.group(RoleEntityType()).field_group(
        FieldGroupMeta(PermissionFieldType()),
        PermissionData,
        LookupRolePermissionOwnerAction,
        LookupBulkRolePermissionOwnerAction,
    )
    return permissions.partial_bulk_get_ops(BulkGetPermissionsAction)


def _get(ids: Sequence[PermissionID]) -> BulkGetPermissionsAction:
    return BulkGetPermissionsAction(permission_ids=list(ids))


def _errors(errors: Mapping[FieldIdentifier, Exception]) -> dict[FieldIdentifier, type[Exception]]:
    return {field_id: type(error) for field_id, error in errors.items()}


def _described(records: list[AuditRecord], field_id: PermissionID) -> list[AuditRecord]:
    return [r for r in records if str(field_id) in r.description]


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced"),
        [
            pytest.param(Actor.SUPERADMIN, True, id="actor-2"),
            pytest.param(Actor.GRANTED, True, id="actor-3"),
            pytest.param(Actor.MONITOR, True, id="actor-5", marks=MONITOR_READ_REFUSED),
            pytest.param(Actor.UNGRANTED, False, id="actor-6"),
        ],
    )
    async def test_every_row_is_read(
        self, harness: OpsHarness, actors: Actors, world: _World, actor: Actor, enforced: bool
    ) -> None:
        harness.enforce(enforced)
        ids = [world.a1, world.a2, world.b1]

        with actors.acting_as(actor):
            result = await _processor(harness).run(_get(ids))

        assert set(result.successes) == set(ids)
        assert result.errors == {}

    @ANONYMOUS_NOT_REFUSED
    async def test_a_caller_with_no_user_is_refused(
        self,
        harness: OpsHarness,
        actors: Actors,
        world: _World,
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """actor-1."""
        reads = repository_calls("bulk_get_fields")

        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(_get([world.a1]))

        assert reads == []
        assert_refused(raised.value)

    async def test_an_ungranted_caller_is_denied_every_row(
        self,
        harness: OpsHarness,
        actors: Actors,
        world: _World,
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """actor-4."""
        ids = [world.a1, world.a2, world.b1]
        reads = repository_calls("bulk_get_fields")

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(_get(ids))

        assert result.successes == {}
        assert _errors(result.errors) == dict.fromkeys(ids, NotEnoughPermission)
        assert [field_id for _, field_ids in reads for field_id in field_ids] == []


class TestMulti:
    async def test_a_denied_owner_takes_its_rows_out_of_the_read(
        self,
        harness: OpsHarness,
        actors: Actors,
        world: _World,
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """multi-1."""
        reads = repository_calls("bulk_get_fields")

        with actors.acting_as(Actor.READ_ONLY):
            result = await _processor(harness).run(_get([world.a1, world.b1]))

        assert set(result.successes) == {world.a1}
        assert _errors(result.errors) == {world.b1: NotEnoughPermission}
        assert [field_id for _, field_ids in reads for field_id in field_ids] == [world.a1]

    async def test_a_repeated_row_is_answered_once(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """multi-2."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_get([world.a1, world.a1]))

        assert list(result.successes) == [world.a1]
        assert result.errors == {}

    @_NO_ROWS_NAMED_RAISES
    async def test_no_rows_named_answers_nothing(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """multi-3."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_get([]))

        assert result.successes == {}
        assert result.errors == {}
        assert await harness.audit(_OWNER_LOOKUP) == []
        assert await harness.audit(_OPERATION) == []


class TestTarget:
    async def test_a_missing_row_fails_alone(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """target-1."""
        missing = PermissionID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(_get([world.a1, missing]))

        assert set(result.successes) == {world.a1}
        assert _errors(result.errors) == {missing: FieldNotFoundError}

    @_ALL_ROWS_MISSING_FAILS_THE_RUN
    async def test_every_row_missing_fails_each_row(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """target-2."""
        missing = [PermissionID(uuid.uuid4()), PermissionID(uuid.uuid4())]

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(_get(missing))

        assert result.successes == {}
        assert _errors(result.errors) == dict.fromkeys(missing, FieldNotFoundError)


class TestRecord:
    @pytest.mark.parametrize(
        "record_reads",
        [pytest.param(True, id="record-1"), pytest.param(False, id="record-1-reads-unrecorded")],
    )
    async def test_a_read_row_is_recorded_on_its_owner_by_policy(
        self, ops_db: ExtendedAsyncSAEngine, actors: Actors, world: _World, record_reads: bool
    ) -> None:
        harness = OpsHarness(ops_db, record_reads=record_reads)

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_get([world.a1, world.b1]))

        records = await harness.audit(_OPERATION)
        if not record_reads:
            assert records == []
            return
        for field_id, owner in ((world.a1, world.role_a), (world.b1, world.role_b)):
            assert [
                ((r.entity_type, r.entity_id), r.status) for r in _described(records, field_id)
            ] == [(entity_key(owner), OperationStatus.SUCCESS)]
        assert len(records) == 2

    async def test_a_denied_row_is_recorded_on_its_owner(
        self, silent_reads_harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """record-2."""
        with actors.acting_as(Actor.READ_ONLY):
            await _processor(silent_reads_harness).run(_get([world.a1, world.b1]))

        records = await silent_reads_harness.audit(_OPERATION)
        assert [
            ((r.entity_type, r.entity_id), r.status) for r in _described(records, world.b1)
        ] == [(entity_key(world.role_b), OperationStatus.DENIED)]
        assert len(records) == 1

    async def test_a_row_failing_after_the_lookup_is_an_error_on_its_owner(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        world: _World,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-3: the read drops one row the lookup found."""
        original = OpsRepository.bulk_get_fields

        async def dropping(
            self: OpsRepository[Any], querier: Any, field_ids: Sequence[FieldIdentifier]
        ) -> Mapping[FieldIdentifier, Any]:
            found = await original(self, querier, field_ids)
            return {field_id: data for field_id, data in found.items() if field_id != world.a1}

        monkeypatch.setattr(OpsRepository, "bulk_get_fields", dropping)

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(silent_reads_harness).run(_get([world.a1, world.b1]))

        assert _errors(result.errors) == {world.a1: FieldNotFoundError}
        records = await silent_reads_harness.audit(_OPERATION)
        assert [((r.entity_type, r.entity_id), r.status) for r in records] == [
            (entity_key(world.role_a), OperationStatus.ERROR)
        ]
        assert str(world.a1) in records[0].description

    async def test_a_missing_row_is_a_lookup_error_alone(
        self, silent_reads_harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """record-4."""
        missing = PermissionID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            await _processor(silent_reads_harness).run(_get([world.a1, missing]))

        lookups = await silent_reads_harness.audit(_OWNER_LOOKUP)
        assert [(r.entity_id, r.status, r.lookup_key) for r in lookups] == [
            (None, OperationStatus.ERROR, f"id={missing}")
        ]
        assert _described(await silent_reads_harness.audit(_OPERATION), missing) == []

    @ANONYMOUS_RECORDED_AS_ERROR
    async def test_a_caller_with_no_user_is_one_denied_lookup(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """record-5."""
        with actors.acting_as(Actor.ANONYMOUS):
            with contextlib.suppress(Exception):
                await _processor(harness).run(_get([world.a1]))

        assert [r.status for r in await harness.audit(_OWNER_LOOKUP)] == [OperationStatus.DENIED]

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

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_get([world.a1]))

        assert [r.status for r in await harness.audit(_OPERATION)] == [OperationStatus.ERROR]


class TestResult:
    async def test_a_read_row_is_its_data(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_get([world.a1]))

        data = result.successes[world.a1]
        assert (data.id, data.role_id, data.permission) == (world.a1, world.role_a, Permission.READ)

    async def test_a_denial_is_told_apart_from_a_miss(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """result-2."""
        missing = PermissionID(uuid.uuid4())

        with actors.acting_as(Actor.READ_ONLY):
            result = await _processor(harness).run(_get([world.a1, world.b1, missing]))

        assert _errors(result.errors) == {
            world.b1: NotEnoughPermission,
            missing: FieldNotFoundError,
        }
