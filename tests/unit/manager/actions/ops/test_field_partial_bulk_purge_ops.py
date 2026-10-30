"""``partial_bulk_purge_ops (field)``: removing the named field rows, with roles'
permission entries as the representative.

The permission purger declares no guard, so target-3 and record-3 run on a test-only
action carrying the keypair purger, which refuses the default key.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Self, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.keypair import KeyPairFieldType, KeyPairID
from ai.backend.common.data.entity.permission import PermissionFieldType, PermissionID
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.types import FieldIdentifier
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission, RoleSource
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.field.ops import PartialBulkPurgeFieldOpsAction
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.user import KeyPairForbidden
from ai.backend.manager.models.keypair.purgers import NonDefaultKeypairPurger
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.services.permission_contoller.actions.bulk_remove_role_permissions import (
    BulkRemoveRolePermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.lookup_permission_owner import (
    LookupBulkRolePermissionOwnerAction,
    LookupRolePermissionOwnerAction,
)
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupBulkKeypairOwnerAction,
    LookupKeypairOwnerAction,
)
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
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
_OPERATION = BulkRemoveRolePermissionsAction.action_name()


@dataclass(frozen=True)
class _PurgeKeypairsAction(
    PartialBulkPurgeFieldOpsAction[KeyPairID, UserID, KeyPairRow, KeyPairData]
):
    """Test-only: the partial field purge shape carrying the guarded keypair purger."""

    keypair_ids: Sequence[KeyPairID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "test_purge_keypairs"

    @override
    def field_ids(self) -> Sequence[KeyPairID]:
        return tuple(self.keypair_ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkKeypairOwnerAction:
        return LookupBulkKeypairOwnerAction(keypair_ids=self.keypair_ids)

    @override
    def to_purgers(self) -> Mapping[KeyPairID, NonDefaultKeypairPurger]:
        return {
            keypair_id: NonDefaultKeypairPurger(keypair_id=keypair_id)
            for keypair_id in self.keypair_ids
        }

    @override
    def narrowed_to(self, field_ids: Sequence[KeyPairID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(
            self,
            keypair_ids=[keypair_id for keypair_id in self.keypair_ids if keypair_id in allowed],
        )


@dataclass(frozen=True)
class _Keypairs:
    owner: UserID
    default: KeyPairID
    other: KeyPairID


async def _seed_keypairs(db: ExtendedAsyncSAEngine, actors: Actors) -> _Keypairs:
    """A user with its default keypair and one more."""
    owner_id = UserID(uuid.uuid4())
    suffix = owner_id.hex[:8]
    keypairs = _Keypairs(
        owner=owner_id, default=KeyPairID(uuid.uuid4()), other=KeyPairID(uuid.uuid4())
    )
    async with db.begin_session() as sess:
        sess.add(
            UserResourcePolicyRow(
                name=f"owner-policy-{suffix}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
        )
        sess.add(
            KeyPairResourcePolicyRow(
                name=f"keypair-policy-{suffix}",
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=1,
                max_concurrent_sftp_sessions=1,
                max_containers_per_session=1,
                idle_timeout=3600,
            )
        )
        await sess.flush()
        sess.add(
            UserRow(
                uuid=owner_id,
                username=f"owner-{suffix}",
                email=f"owner-{suffix}@test.com",
                resource_policy=f"owner-policy-{suffix}",
                status=UserStatus.ACTIVE,
                need_password_change=False,
                sudo_session_enabled=False,
                domain_name=actors.domain_name,
                domain_id=actors.domain_id,
                role=UserRole.USER,
            )
        )
        await sess.flush()
        sess.add_all([
            KeyPairRow(
                id=keypair_id,
                user=owner_id,
                access_key=AccessKey(f"AK{keypair_id.hex[:16]}"),
                secret_key=SecretValue("test-secret"),
                is_active=True,
                is_admin=False,
                is_default=is_default,
                resource_policy=f"keypair-policy-{suffix}",
                rate_limit=1000,
            )
            for keypair_id, is_default in ((keypairs.default, True), (keypairs.other, False))
        ])
        await sess.commit()
    await provision(db, UserEntityType(), owner_id)
    return keypairs


def _keypair_processor(harness: OpsHarness) -> Any:
    keypairs = harness.group(UserEntityType()).field_group(
        FieldGroupMeta(KeyPairFieldType()),
        KeyPairData,
        LookupKeypairOwnerAction,
        LookupBulkKeypairOwnerAction,
    )
    return keypairs.partial_bulk_purge_ops(_PurgeKeypairsAction)


async def _keypairs_left(db: ExtendedAsyncSAEngine, keypairs: _Keypairs) -> set[KeyPairID]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(sa.select(KeyPairRow.id).where(KeyPairRow.user == keypairs.owner))
        return set(rows.all())


@dataclass(frozen=True)
class _World:
    role_a: RoleID
    role_b: RoleID
    a1: PermissionID
    a2: PermissionID
    b1: PermissionID

    def every_entry(self) -> list[PermissionID]:
        return [self.a1, self.a2, self.b1]


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
    role_a = await _seed_role(ops_db, actors)
    role_b = await _seed_role(ops_db, actors)
    for role_id in (role_a, role_b):
        await grant(
            ops_db,
            actors.user_id(Actor.GRANTED),
            RoleEntityType(),
            role_id,
            RoleEntityType(),
            Permission.UPDATE,
        )
    return _World(
        role_a=role_a,
        role_b=role_b,
        a1=await _seed_entry(ops_db, role_a, Permission.READ),
        a2=await _seed_entry(ops_db, role_a, Permission.UPDATE),
        b1=await _seed_entry(ops_db, role_b, Permission.READ),
    )


async def _left(db: ExtendedAsyncSAEngine, ids: Sequence[PermissionID]) -> set[PermissionID]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(sa.select(PermissionRow.id).where(PermissionRow.id.in_(ids)))
        return set(rows.all())


def _processor(harness: OpsHarness) -> Any:
    permissions = harness.group(RoleEntityType()).field_group(
        FieldGroupMeta(PermissionFieldType()),
        PermissionData,
        LookupRolePermissionOwnerAction,
        LookupBulkRolePermissionOwnerAction,
    )
    return permissions.partial_bulk_purge_ops(BulkRemoveRolePermissionsAction)


def _remove(ids: Sequence[PermissionID]) -> BulkRemoveRolePermissionsAction:
    return BulkRemoveRolePermissionsAction(permission_ids=list(ids))


def _errors(errors: Mapping[FieldIdentifier, Exception]) -> dict[FieldIdentifier, type[Exception]]:
    return {field_id: type(error) for field_id, error in errors.items()}


def _described(records: list[AuditRecord], field_id: FieldIdentifier) -> list[AuditRecord]:
    return [r for r in records if str(field_id) in r.description]


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced"),
        [
            pytest.param(Actor.SUPERADMIN, True, id="actor-2"),
            pytest.param(Actor.GRANTED, True, id="actor-3"),
            pytest.param(Actor.UNGRANTED, False, id="actor-6"),
        ],
    )
    async def test_every_row_is_removed(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        world: _World,
        actor: Actor,
        enforced: bool,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            result = await _processor(harness).run(_remove(world.every_entry()))

        assert set(result.successes) == set(world.every_entry())
        assert result.errors == {}
        assert await _left(ops_db, world.every_entry()) == set()

    @pytest.mark.parametrize(
        "actor",
        [pytest.param(Actor.UNGRANTED, id="actor-4"), pytest.param(Actor.MONITOR, id="actor-5")],
    )
    async def test_every_row_is_denied(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        world: _World,
        actor: Actor,
    ) -> None:
        with actors.acting_as(actor):
            result = await _processor(harness).run(_remove(world.every_entry()))

        assert result.successes == {}
        assert _errors(result.errors) == dict.fromkeys(world.every_entry(), NotEnoughPermission)
        assert await _left(ops_db, world.every_entry()) == set(world.every_entry())

    @ANONYMOUS_NOT_REFUSED
    async def test_a_caller_with_no_user_is_refused(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """actor-1."""
        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(_remove([world.a1]))

        assert await _left(ops_db, [world.a1]) == {world.a1}
        assert_refused(raised.value)


class TestMulti:
    async def test_a_denied_owner_keeps_its_rows(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """multi-1: the caller may write the first role alone."""
        await grant(
            ops_db,
            actors.user_id(Actor.UNGRANTED),
            RoleEntityType(),
            world.role_a,
            RoleEntityType(),
            Permission.UPDATE,
        )

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(_remove([world.a1, world.b1]))

        assert set(result.successes) == {world.a1}
        assert _errors(result.errors) == {world.b1: NotEnoughPermission}
        assert await _left(ops_db, [world.a1, world.b1]) == {world.b1}

    async def test_a_repeated_row_is_answered_and_removed_once(
        self,
        ops_db: ExtendedAsyncSAEngine,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        world: _World,
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """multi-2."""
        writes = repository_calls("partial_bulk_purge_field_entities")

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(silent_reads_harness).run(_remove([world.a1, world.a1]))

        assert list(result.successes) == [world.a1]
        assert result.errors == {}
        assert await _left(ops_db, [world.a1]) == set()
        assert [list(purgers) for (purgers,) in writes] == [[world.a1]]
        assert [r.status for r in await silent_reads_harness.audit(_OPERATION)] == [
            OperationStatus.SUCCESS
        ]

    @_NO_ROWS_NAMED_RAISES
    async def test_no_rows_named_answers_nothing(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """multi-3."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_remove([]))

        assert result.successes == {}
        assert result.errors == {}
        assert await harness.audit(_OWNER_LOOKUP) == []
        assert await harness.audit(_OPERATION) == []


class TestTarget:
    async def test_a_missing_row_fails_alone(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """target-1."""
        missing = PermissionID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(_remove([world.a1, missing]))

        assert set(result.successes) == {world.a1}
        assert _errors(result.errors) == {missing: FieldNotFoundError}
        assert await _left(ops_db, [world.a1]) == set()

    @_ALL_ROWS_MISSING_FAILS_THE_RUN
    async def test_every_row_missing_fails_each_row(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """target-2."""
        missing = [PermissionID(uuid.uuid4()), PermissionID(uuid.uuid4())]

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(_remove(missing))

        assert result.successes == {}
        assert _errors(result.errors) == dict.fromkeys(missing, FieldNotFoundError)

    async def test_a_row_failing_its_guard_fails_alone(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-3: the default keypair is kept, the other removed."""
        keypairs = await _seed_keypairs(ops_db, actors)

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _keypair_processor(harness).run(
                _PurgeKeypairsAction(keypair_ids=[keypairs.default, keypairs.other])
            )

        assert set(result.successes) == {keypairs.other}
        assert _errors(result.errors) == {keypairs.default: KeyPairForbidden}
        assert await _keypairs_left(ops_db, keypairs) == {keypairs.default}


class TestRecord:
    async def test_a_removed_row_is_recorded_on_its_owner(
        self, silent_reads_harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """record-1: a write is recorded whatever the read policy says."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(_remove([world.a1, world.b1]))

        records = await silent_reads_harness.audit(_OPERATION)
        for field_id, owner in ((world.a1, world.role_a), (world.b1, world.role_b)):
            assert [
                ((r.entity_type, r.entity_id), r.operation, r.status)
                for r in _described(records, field_id)
            ] == [(entity_key(owner), ActionOperationType.UPDATE, OperationStatus.SUCCESS)]
        assert len(records) == 2

    async def test_a_denied_row_is_recorded_on_its_owner(
        self, silent_reads_harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """record-2."""
        with actors.acting_as(Actor.UNGRANTED):
            await _processor(silent_reads_harness).run(_remove([world.b1]))

        records = await silent_reads_harness.audit(_OPERATION)
        assert [
            ((r.entity_type, r.entity_id), r.status) for r in _described(records, world.b1)
        ] == [(entity_key(world.role_b), OperationStatus.DENIED)]
        assert len(records) == 1

    async def test_a_row_failing_its_guard_is_an_error_on_its_owner(
        self, ops_db: ExtendedAsyncSAEngine, silent_reads_harness: OpsHarness, actors: Actors
    ) -> None:
        """record-3."""
        keypairs = await _seed_keypairs(ops_db, actors)

        with actors.acting_as(Actor.SUPERADMIN):
            await _keypair_processor(silent_reads_harness).run(
                _PurgeKeypairsAction(keypair_ids=[keypairs.default, keypairs.other])
            )

        records = await silent_reads_harness.audit(_PurgeKeypairsAction.action_name())
        owner = entity_key(keypairs.owner)
        assert [
            ((r.entity_type, r.entity_id), r.status) for r in _described(records, keypairs.default)
        ] == [(owner, OperationStatus.ERROR)]
        assert [
            ((r.entity_type, r.entity_id), r.status) for r in _described(records, keypairs.other)
        ] == [(owner, OperationStatus.SUCCESS)]

    async def test_a_missing_row_is_a_lookup_error_alone(
        self, silent_reads_harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """record-4."""
        missing = PermissionID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            await _processor(silent_reads_harness).run(_remove([world.a1, missing]))

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
                await _processor(harness).run(_remove([world.a1]))

        assert [r.status for r in await harness.audit(_OWNER_LOOKUP)] == [OperationStatus.DENIED]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        ops_db: ExtendedAsyncSAEngine,
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
                await _processor(harness).run(_remove([world.a1]))

        assert [r.status for r in await harness.audit(_OPERATION)] == [OperationStatus.ERROR]
        assert await _left(ops_db, [world.a1]) == {world.a1}


class TestResult:
    async def test_a_removed_row_is_its_data_before_the_purge(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_remove([world.a1]))

        data = result.successes[world.a1]
        assert (data.id, data.role_id, data.permission) == (world.a1, world.role_a, Permission.READ)

    async def test_a_denial_is_told_apart_from_a_miss(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """result-2."""
        missing = PermissionID(uuid.uuid4())

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(_remove([world.a1, missing]))

        assert _errors(result.errors) == {
            world.a1: NotEnoughPermission,
            missing: FieldNotFoundError,
        }
