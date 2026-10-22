"""``update_ops (field)``: editing one field row, with a role's permission entry as the
representative.

The permission updater declares no guard, so target-4 runs on a test-only action carrying
the keypair updater. No field spec declares two guards, so target-5 is not applicable.
"""

from __future__ import annotations

import contextlib
import uuid
from dataclasses import dataclass
from typing import Any, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.keypair import KeyPairFieldType, KeyPairID
from ai.backend.common.data.entity.permission import PermissionFieldType, PermissionID
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission, RoleSource
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.field.ops import UpdateFieldOpsAction
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.user import KeyPairForbidden
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.keypair.updaters import KeypairUpdater
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.updaters import RolePermissionUpdater
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
from ai.backend.manager.services.permission_contoller.actions.lookup_permission_owner import (
    LookupBulkRolePermissionOwnerAction,
    LookupRolePermissionOwnerAction,
)
from ai.backend.manager.services.permission_contoller.actions.update_permission import (
    UpdatePermissionAction,
)
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupBulkKeypairOwnerAction,
    LookupKeypairOwnerAction,
)
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    FIELD_WRITE_NEEDS_OWNER_READ,
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

_OWNER_LOOKUP = LookupRolePermissionOwnerAction.action_name()
_OPERATION = UpdatePermissionAction.action_name()


@dataclass(frozen=True)
class _DeactivateKeypairAction(UpdateFieldOpsAction[KeyPairID, UserID, KeyPairRow, KeyPairData]):
    """Test-only: the field update shape carrying the guarded keypair updater."""

    keypair_id: KeyPairID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "test_deactivate_keypair"

    @override
    def to_owner_lookup_action(self) -> LookupKeypairOwnerAction:
        return LookupKeypairOwnerAction(keypair_id=self.keypair_id)

    @override
    def to_updater(self) -> KeypairUpdater:
        return KeypairUpdater(keypair_id=self.keypair_id, is_active=OptionalState.update(False))


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


async def _seed_permission(
    db: ExtendedAsyncSAEngine, role_id: RoleID, permission: Permission
) -> PermissionID:
    async with db.begin_session() as sess:
        row = PermissionRow(role_id=role_id, entity_type=DomainEntityType(), permission=permission)
        sess.add(row)
        await sess.flush()
        permission_id = row.id
        await sess.commit()
    return permission_id


async def _seed_default_keypair(db: ExtendedAsyncSAEngine, actors: Actors) -> KeyPairID:
    """The keypair a fresh user authorizes with."""
    owner_id = UserID(uuid.uuid4())
    keypair_id = KeyPairID(uuid.uuid4())
    suffix = owner_id.hex[:8]
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
        sess.add(
            KeyPairRow(
                id=keypair_id,
                user=owner_id,
                access_key=AccessKey(f"AK{owner_id.hex[:16]}"),
                secret_key=SecretValue("test-secret"),
                is_active=True,
                is_admin=False,
                is_default=True,
                resource_policy=f"keypair-policy-{suffix}",
                rate_limit=1000,
            )
        )
        await sess.commit()
    await provision(db, UserEntityType(), owner_id)
    return keypair_id


@pytest.fixture
async def role(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> RoleID:
    role_id = await _seed_role(ops_db, actors)
    for actor, permission in (
        (Actor.GRANTED, Permission.UPDATE),
        (Actor.READ_ONLY, Permission.READ),
    ):
        await grant(
            ops_db, actors.user_id(actor), RoleEntityType(), role_id, RoleEntityType(), permission
        )
    return role_id


@pytest.fixture
async def entry(ops_db: ExtendedAsyncSAEngine, role: RoleID) -> PermissionID:
    return await _seed_permission(ops_db, role, Permission.READ)


async def _bit(db: ExtendedAsyncSAEngine, permission_id: PermissionID) -> Permission | None:
    async with db.begin_readonly_session() as sess:
        bit: Permission | None = await sess.scalar(
            sa.select(PermissionRow.permission).where(PermissionRow.id == permission_id)
        )
    return bit


def _processor(harness: OpsHarness) -> Any:
    permissions = harness.group(RoleEntityType()).field_group(
        FieldGroupMeta(PermissionFieldType()),
        PermissionData,
        LookupRolePermissionOwnerAction,
        LookupBulkRolePermissionOwnerAction,
    )
    return permissions.update_ops(UpdatePermissionAction)


def _to(
    permission_id: PermissionID, permission: Permission = Permission.UPDATE
) -> UpdatePermissionAction:
    return UpdatePermissionAction(
        permission_id=permission_id,
        updater=RolePermissionUpdater(
            permission_id=permission_id, permission=OptionalState.update(permission)
        ),
    )


def _rows(
    records: list[AuditRecord],
) -> list[tuple[tuple[str | None, str | None], str, OperationStatus]]:
    return [((r.entity_type, r.entity_id), r.operation, r.status) for r in records]


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced", "error"),
        [
            pytest.param(Actor.SUPERADMIN, True, None, id="actor-2"),
            pytest.param(
                Actor.GRANTED, True, None, id="actor-3", marks=FIELD_WRITE_NEEDS_OWNER_READ
            ),
            pytest.param(Actor.READ_ONLY, True, NotEnoughPermission, id="actor-4"),
            pytest.param(Actor.UNGRANTED, True, GenericBadRequest, id="actor-5"),
            pytest.param(Actor.UNGRANTED, False, None, id="actor-7"),
        ],
    )
    async def test_actor(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        entry: PermissionID,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(_to(entry))
            else:
                with pytest.raises(error):
                    await _processor(harness).run(_to(entry))

        assert await _bit(ops_db, entry) == (Permission.READ if error else Permission.UPDATE)

    @ANONYMOUS_NOT_REFUSED
    async def test_a_caller_with_no_user_is_refused(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        entry: PermissionID,
    ) -> None:
        """actor-1."""
        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(_to(entry))

        assert await _bit(ops_db, entry) == Permission.READ
        assert_refused(raised.value)

    @MONITOR_READ_REFUSED
    async def test_a_monitor_passes_the_lookup_and_is_denied_the_write(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        role: RoleID,
        entry: PermissionID,
    ) -> None:
        """actor-6."""
        with actors.acting_as(Actor.MONITOR):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_to(entry))

        assert await _bit(ops_db, entry) == Permission.READ
        assert _rows(await harness.audit(_OWNER_LOOKUP)) == [
            (entity_key(role), ActionOperationType.LOOKUP, OperationStatus.SUCCESS)
        ]
        assert _rows(await harness.audit(_OPERATION)) == [
            (entity_key(role), ActionOperationType.UPDATE, OperationStatus.DENIED)
        ]


class TestTarget:
    @pytest.mark.parametrize(
        ("actor", "error"),
        [
            pytest.param(Actor.GRANTED, GenericBadRequest, id="target-1"),
            pytest.param(Actor.SUPERADMIN, FieldNotFoundError, id="target-2"),
        ],
    )
    async def test_missing(
        self,
        harness: OpsHarness,
        actors: Actors,
        role: RoleID,
        actor: Actor,
        error: type[Exception],
    ) -> None:
        with actors.acting_as(actor):
            with pytest.raises(error):
                await _processor(harness).run(_to(PermissionID(uuid.uuid4())))

    @pytest.mark.parametrize(
        "exists", [pytest.param(False, id="missing"), pytest.param(True, id="denied")]
    )
    async def test_the_refusal_names_neither_the_row_nor_its_owner(
        self,
        harness: OpsHarness,
        actors: Actors,
        role: RoleID,
        entry: PermissionID,
        exists: bool,
    ) -> None:
        """target-3."""
        target = entry if exists else PermissionID(uuid.uuid4())

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(GenericBadRequest) as caught:
                await _processor(harness).run(_to(target))

        assert str(target) not in str(caught.value)
        assert str(role) not in str(caught.value)

    async def test_a_failing_guard_leaves_the_row(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-4: the default keypair is not deactivated."""
        keypair_id = await _seed_default_keypair(ops_db, actors)
        processor = (
            harness.group(UserEntityType())
            .field_group(
                FieldGroupMeta(KeyPairFieldType()),
                KeyPairData,
                LookupKeypairOwnerAction,
                LookupBulkKeypairOwnerAction,
            )
            .update_ops(_DeactivateKeypairAction)
        )

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(KeyPairForbidden):
                await processor.run(_DeactivateKeypairAction(keypair_id=keypair_id))

        async with ops_db.begin_readonly_session() as sess:
            active = await sess.scalar(
                sa.select(KeyPairRow.is_active).where(KeyPairRow.id == keypair_id)
            )
        assert active is True

    async def test_a_value_colliding_with_another_row_leaves_the_row(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        role: RoleID,
        entry: PermissionID,
    ) -> None:
        """target-6: the updater declares no domain error."""
        await _seed_permission(ops_db, role, Permission.UPDATE)

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(UniqueConstraintViolationError):
                await _processor(harness).run(_to(entry, Permission.UPDATE))

        assert await _bit(ops_db, entry) == Permission.READ


class TestRecord:
    @pytest.mark.parametrize(
        "record_reads",
        [
            pytest.param(True, id="record-1", marks=FIELD_WRITE_NEEDS_OWNER_READ),
            pytest.param(False, id="record-1-reads-unrecorded", marks=FIELD_WRITE_NEEDS_OWNER_READ),
        ],
    )
    async def test_success(
        self,
        ops_db: ExtendedAsyncSAEngine,
        actors: Actors,
        role: RoleID,
        entry: PermissionID,
        record_reads: bool,
    ) -> None:
        harness = OpsHarness(ops_db, record_reads=record_reads)

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_to(entry))

        lookup = (entity_key(role), ActionOperationType.LOOKUP, OperationStatus.SUCCESS)
        assert _rows(await harness.audit(_OWNER_LOOKUP)) == ([lookup] if record_reads else [])
        assert _rows(await harness.audit(_OPERATION)) == [
            (entity_key(role), ActionOperationType.UPDATE, OperationStatus.SUCCESS)
        ]

    async def test_a_denied_owner_lookup_leaves_no_operation_row(
        self, silent_reads_harness: OpsHarness, actors: Actors, role: RoleID, entry: PermissionID
    ) -> None:
        """record-2."""
        with actors.acting_as(Actor.UNGRANTED):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_to(entry))

        assert _rows(await silent_reads_harness.audit(_OWNER_LOOKUP)) == [
            (entity_key(role), ActionOperationType.LOOKUP, OperationStatus.DENIED)
        ]
        assert await silent_reads_harness.audit(_OPERATION) == []

    async def test_a_denied_operation_follows_a_passed_lookup(
        self, harness: OpsHarness, actors: Actors, role: RoleID, entry: PermissionID
    ) -> None:
        """record-3."""
        with actors.acting_as(Actor.READ_ONLY):
            with contextlib.suppress(Exception):
                await _processor(harness).run(_to(entry))

        assert _rows(await harness.audit(_OWNER_LOOKUP)) == [
            (entity_key(role), ActionOperationType.LOOKUP, OperationStatus.SUCCESS)
        ]
        assert _rows(await harness.audit(_OPERATION)) == [
            (entity_key(role), ActionOperationType.UPDATE, OperationStatus.DENIED)
        ]

    async def test_a_missing_row_is_a_lookup_error_by_its_key(
        self, harness: OpsHarness, actors: Actors, role: RoleID
    ) -> None:
        """record-4."""
        missing = PermissionID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            with contextlib.suppress(Exception):
                await _processor(harness).run(_to(missing))

        lookups = await harness.audit(_OWNER_LOOKUP)
        assert [(r.entity_id, r.status, r.lookup_key) for r in lookups] == [
            (None, OperationStatus.ERROR, f"id={missing}")
        ]
        assert await harness.audit(_OPERATION) == []

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        entry: PermissionID,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_to(entry))

        assert [r.status for r in await harness.audit(_OWNER_LOOKUP)] == [OperationStatus.ERROR]
        assert await harness.audit(_OPERATION) == []
        assert await _bit(ops_db, entry) == Permission.READ


class TestResult:
    async def test_the_data_is_the_row_after_the_write(
        self, harness: OpsHarness, actors: Actors, role: RoleID, entry: PermissionID
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(_to(entry))

        assert result.data.id == entry
        assert result.data.role_id == role
        assert result.data.permission == Permission.UPDATE
