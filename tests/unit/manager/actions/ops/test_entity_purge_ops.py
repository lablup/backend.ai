"""``entity_purge_ops``: purging one entity, with the role as the representative.

The role purger declares no conflict check, so that row runs on the resource slot type,
whose purger declares one per table naming the slot. Not applicable: target-4, as no
purger of this shape declares two guards.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeEntityType
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.permission.types import Permission, RoleSource
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource_slot import ResourceSlotTypeInUse
from ai.backend.manager.errors.role_preset import SystemRoleNotEditable
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.resource_group.row import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_slot.purgers import ResourceSlotTypePurger
from ai.backend.manager.models.resource_slot.row import (
    AgentResourceRow,
    DeploymentRevisionResourceSlotRow,
    ModelCardResourceRequirementRow,
    PresetResourceSlotRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import PurgeRoleAction
from ai.backend.manager.services.resource_slot.actions.purge import PurgeResourceSlotTypeAction
from ai.backend.testutils.db import with_tables
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


async def _seed_role(db: ExtendedAsyncSAEngine, actors: Actors, source: RoleSource) -> RoleID:
    role_id = RoleID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            RoleRow(
                id=role_id,
                name=f"target-{role_id.hex[:8]}",
                source=source,
                status=RoleStatus.ACTIVE,
                scope_type=DomainEntityType(),
                scope_id=actors.domain_id,
            )
        )
        await sess.commit()
    await provision(db, RoleEntityType(), role_id, [(DomainEntityType(), actors.domain_id)])
    return role_id


@pytest.fixture
async def role(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> RoleID:
    role_id = await _seed_role(ops_db, actors, RoleSource.CUSTOM)
    for actor, permission in (
        (Actor.GRANTED, Permission.HARD_DELETE),
        (Actor.READ_ONLY, Permission.READ),
    ):
        await grant(
            ops_db,
            actors.user_id(actor),
            DomainEntityType(),
            actors.domain_id,
            RoleEntityType(),
            permission,
        )
    return role_id


async def _role_exists(db: ExtendedAsyncSAEngine, role_id: RoleID) -> bool:
    async with db.begin_readonly_session() as sess:
        return await sess.scalar(sa.select(RoleRow.id).where(RoleRow.id == role_id)) is not None


async def _node_exists(db: ExtendedAsyncSAEngine, role_id: RoleID) -> bool:
    async with db.begin_readonly_session() as sess:
        found = await sess.scalar(
            sa.select(VirtualEntityRow.id).where(VirtualEntityRow.entity_id == role_id)
        )
    return found is not None


def _processor(harness: OpsHarness) -> Any:
    return harness.group(RoleEntityType()).entity_purge_ops(PurgeRoleAction)


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
                await _processor(harness).run(PurgeRoleAction(role_id=role))
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(PurgeRoleAction(role_id=role))
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert await _role_exists(ops_db, role) == (error is not None)


class TestTarget:
    @pytest.mark.parametrize(
        ("actor", "error"),
        [
            pytest.param(Actor.SUPERADMIN, EntityNotFoundError, id="target-1"),
            pytest.param(Actor.GRANTED, NotEnoughPermission, id="target-2"),
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
                await _processor(harness).run(PurgeRoleAction(role_id=RoleID(uuid.uuid4())))

    async def test_a_failing_guard_leaves_the_row(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-3: a system role is not purged."""
        system = await _seed_role(ops_db, actors, RoleSource.SYSTEM)

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(SystemRoleNotEditable):
                await _processor(harness).run(PurgeRoleAction(role_id=system))

        assert await _role_exists(ops_db, system)

    async def test_the_row_and_its_node_are_gone(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, role: RoleID
    ) -> None:
        """target-6."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(PurgeRoleAction(role_id=role))

        assert not await _role_exists(ops_db, role)
        assert not await _node_exists(ops_db, role)


@pytest.fixture
async def slot_type_db(
    ops_db: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Every table the slot type purger's conflict checks read."""
    async with with_tables(
        ops_db,
        [
            ResourceSlotTypeRow,
            AgentResourceRow,
            ResourceAllocationRow,
            ModelCardResourceRequirementRow,
            PresetResourceSlotRow,
            DeploymentRevisionResourceSlotRow,
        ],
    ):
        yield ops_db


class TestConflict:
    async def test_a_referenced_row_is_refused(
        self, slot_type_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-5: an agent still reports the slot."""
        resource_group_id = ResourceGroupID(uuid.uuid4())
        agent_uuid = AgentUUID(uuid.uuid4())
        async with slot_type_db.begin_session() as sess:
            slot = ResourceSlotTypeRow(
                slot_name="cuda.device", slot_type="unique", display_name="GPU", rank=3
            )
            sess.add(slot)
            sess.add(
                ResourceGroupRow(
                    id=resource_group_id,
                    name=f"rg-{resource_group_id.hex[:8]}",
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
            await sess.flush()
            sess.add(
                AgentRow(
                    uuid=agent_uuid,
                    id="i-conflict",
                    status=AgentStatus.ALIVE,
                    region="local",
                    version="26.9.0",
                    scaling_group=f"rg-{resource_group_id.hex[:8]}",
                    resource_group_id=resource_group_id,
                    addr="tcp://127.0.0.1:6011",
                    architecture="x86_64",
                )
            )
            await sess.flush()
            sess.add(
                AgentResourceRow(
                    agent_id="i-conflict",
                    agent_uuid=agent_uuid,
                    slot_name="cuda.device",
                    capacity=Decimal(2),
                )
            )
            await sess.flush()
            slot_type_id = slot.uuid
            await sess.commit()
        action = PurgeResourceSlotTypeAction(
            purger=ResourceSlotTypePurger(slot_name="cuda.device", slot_type_id=slot_type_id)
        )
        processor = harness.group(ResourceSlotTypeEntityType()).entity_purge_ops(
            PurgeResourceSlotTypeAction
        )

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(ResourceSlotTypeInUse):
                await processor.run(action)

        async with slot_type_db.begin_readonly_session() as sess:
            left = await sess.scalar(
                sa.select(ResourceSlotTypeRow.uuid).where(ResourceSlotTypeRow.uuid == slot_type_id)
            )
        assert left == slot_type_id


class TestRecord:
    @pytest.mark.parametrize(
        ("actor", "exists", "status"),
        [
            pytest.param(Actor.GRANTED, True, OperationStatus.SUCCESS, id="record-1"),
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
    async def test_one_row_on_the_target(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        role: RoleID,
        actor: Actor,
        exists: bool,
        status: OperationStatus,
    ) -> None:
        target = role if exists else RoleID(uuid.uuid4())

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(PurgeRoleAction(role_id=target))

        records = await silent_reads_harness.audit(PurgeRoleAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(target), ActionOperationType.PURGE, status)
        ]

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
                await _processor(harness).run(PurgeRoleAction(role_id=role))

        records = await harness.audit(PurgeRoleAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _role_exists(ops_db, role)


class TestResult:
    async def test_the_data_is_the_row_before_the_purge(
        self, harness: OpsHarness, actors: Actors, role: RoleID
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(PurgeRoleAction(role_id=role))

        assert result.data.id == role
        assert result.data.name == f"target-{role.hex[:8]}"
