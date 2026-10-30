"""``create_ops (field)``: adding one field row under its owner, with a role's permission
entry as the representative."""

from __future__ import annotations

import contextlib
import uuid
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.permission import PermissionFieldType
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.permission.types import Permission, RoleSource
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.errors.base.not_found import NotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission, PermissionAlreadyGranted
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.permission_contoller.actions.add_role_permission import (
    AddRolePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.lookup_permission_owner import (
    LookupBulkRolePermissionOwnerAction,
    LookupRolePermissionOwnerAction,
)
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    ANONYMOUS_RUNS_UNENFORCED,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    provision,
)

_MISSING_OWNER_IS_A_FK_VIOLATION = pytest.mark.xfail(
    strict=True,
    reason="a field create under a missing owner raises ForeignKeyViolationError, not a not-found",
)


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


async def _entries(db: ExtendedAsyncSAEngine, role_id: RoleID) -> list[Permission]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(PermissionRow.permission).where(PermissionRow.role_id == role_id)
        )
        return list(rows.all())


def _processor(harness: OpsHarness) -> Any:
    permissions = harness.group(RoleEntityType()).field_group(
        FieldGroupMeta(PermissionFieldType()),
        PermissionData,
        LookupRolePermissionOwnerAction,
        LookupBulkRolePermissionOwnerAction,
    )
    return permissions.create_ops(AddRolePermissionAction)


def _add(role_id: RoleID) -> AddRolePermissionAction:
    return AddRolePermissionAction(
        role_id=role_id,
        creator=RolePermissionCreator(entity_type=DomainEntityType(), permission=Permission.READ),
    )


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced", "error"),
        [
            pytest.param(Actor.SUPERADMIN, True, None, id="actor-1"),
            pytest.param(Actor.MONITOR, True, NotEnoughPermission, id="actor-2"),
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
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        role: RoleID,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(_add(role))
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_add(role))
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert await _entries(ops_db, role) == ([] if error else [Permission.READ])


class TestTarget:
    async def test_the_row_is_made_under_its_owner(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, role: RoleID
    ) -> None:
        """target-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_add(role))

        async with ops_db.begin_readonly_session() as sess:
            owner = await sess.scalar(
                sa.select(PermissionRow.role_id).where(PermissionRow.id == result.data.id)
            )
        assert owner == role

    async def test_a_duplicate_raises_the_declared_error_and_leaves_nothing(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, role: RoleID
    ) -> None:
        """target-2."""
        with actors.acting_as(Actor.SUPERADMIN):
            await _processor(harness).run(_add(role))
            with pytest.raises(PermissionAlreadyGranted):
                await _processor(harness).run(_add(role))

        assert await _entries(ops_db, role) == [Permission.READ]

    @_MISSING_OWNER_IS_A_FK_VIOLATION
    async def test_a_missing_owner_is_not_found_for_a_superadmin(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-3."""
        missing = RoleID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(NotFoundError):
                await _processor(harness).run(_add(missing))

        assert await _entries(ops_db, missing) == []

    async def test_a_missing_owner_is_a_denial_for_a_user(
        self, harness: OpsHarness, actors: Actors, role: RoleID
    ) -> None:
        """target-4."""
        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_add(RoleID(uuid.uuid4())))


class TestRecord:
    @pytest.mark.parametrize(
        ("actor", "exists", "status"),
        [
            pytest.param(Actor.GRANTED, True, OperationStatus.SUCCESS, id="record-1"),
            pytest.param(Actor.UNGRANTED, True, OperationStatus.DENIED, id="record-2"),
            pytest.param(
                Actor.ANONYMOUS,
                True,
                OperationStatus.DENIED,
                id="record-4",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_one_row_on_the_owner(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        role: RoleID,
        actor: Actor,
        exists: bool,
        status: OperationStatus,
    ) -> None:
        """A write is recorded whatever the read policy says."""
        owner = role if exists else RoleID(uuid.uuid4())

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_add(owner))

        records = await silent_reads_harness.audit(AddRolePermissionAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(owner), ActionOperationType.UPDATE, status)
        ]

    @_MISSING_OWNER_IS_A_FK_VIOLATION
    async def test_a_missing_owner_is_an_error_on_the_owner(
        self, silent_reads_harness: OpsHarness, actors: Actors, role: RoleID
    ) -> None:
        """record-3: the row carries the not-found error's message."""
        missing = RoleID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(NotFoundError) as raised:
                await _processor(silent_reads_harness).run(_add(missing))

        records = await silent_reads_harness.audit(AddRolePermissionAction.action_name())
        assert [((r.entity_type, r.entity_id), r.status, r.description) for r in records] == [
            (entity_key(missing), OperationStatus.ERROR, str(raised.value))
        ]

    async def test_a_duplicate_is_an_error_on_the_owner(
        self, silent_reads_harness: OpsHarness, actors: Actors, role: RoleID
    ) -> None:
        """record-3: the row carries the declared error's message."""
        with actors.acting_as(Actor.SUPERADMIN):
            await _processor(silent_reads_harness).run(_add(role))
            with pytest.raises(PermissionAlreadyGranted) as raised:
                await _processor(silent_reads_harness).run(_add(role))

        records = await silent_reads_harness.audit(AddRolePermissionAction.action_name())
        assert [
            ((r.entity_type, r.entity_id), r.status, r.description)
            for r in records
            if r.status is not OperationStatus.SUCCESS
        ] == [(entity_key(role), OperationStatus.ERROR, str(raised.value))]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        role: RoleID,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_add(role))

        records = await harness.audit(AddRolePermissionAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _entries(ops_db, role) == []


class TestResult:
    async def test_the_data_is_the_row_made(
        self, harness: OpsHarness, actors: Actors, role: RoleID
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_add(role))

        assert result.data.role_id == role
        assert result.data.entity_type == DomainEntityType()
        assert result.data.permission == Permission.READ
