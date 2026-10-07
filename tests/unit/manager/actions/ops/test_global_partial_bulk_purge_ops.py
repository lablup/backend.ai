"""``global_partial_bulk_purge_ops``: purging named global entities; the role preset represents it.

No wired purger of this shape declares a guard or a conflict check, so target-3 and target-4
run a test-only action over the role and resource slot type purgers.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator, Mapping, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any, Self, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.resource_slot import (
    ResourceSlotTypeEntityType,
    ResourceSlotTypeUUID,
)
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.role_preset import RolePresetEntityType, RolePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission, RoleSource
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeGlobalEntityOpsAction
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource_slot import ResourceSlotTypeInUse
from ai.backend.manager.errors.role_preset import SystemRoleNotEditable
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.rbac_models.role.purgers import RolePurger
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.resource_slot.purgers import ResourceSlotTypePurger
from ai.backend.manager.models.resource_slot.row import (
    AgentResourceRow,
    DeploymentRevisionResourceSlotRow,
    ModelCardResourceRequirementRow,
    PresetResourceSlotRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.specs.purger import GuardedEntityPurger
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.role_preset.actions.bulk_purge import BulkPurgeRolePresetsAction
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    provision,
)

DENIALS_RECORDED_AS_ERROR_ON_A_FAILED_RUN = pytest.mark.xfail(
    strict=True, reason="a run that raises records the ids it denied as ERROR, not DENIED"
)


@pytest.fixture
async def preset_db(ops_db: ExtendedAsyncSAEngine) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(ops_db, [RolePresetRow]):
        yield ops_db


async def _seed_preset(db: ExtendedAsyncSAEngine) -> RolePresetID:
    preset_id = RolePresetID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            RolePresetRow(
                id=preset_id, name=f"preset-{preset_id.hex[:8]}", scope_type=ProjectEntityType()
            )
        )
        await sess.commit()
    scope = global_entity_id(GlobalEntityName.GLOBAL)
    await provision(db, RolePresetEntityType(), preset_id, [(scope.entity_type(), scope)])
    return preset_id


@pytest.fixture
async def presets(preset_db: ExtendedAsyncSAEngine, actors: Actors) -> list[RolePresetID]:
    preset_ids = [await _seed_preset(preset_db) for _ in range(2)]
    scope = global_entity_id(GlobalEntityName.GLOBAL)
    await grant(
        preset_db,
        actors.user_id(Actor.GRANTED),
        scope.entity_type(),
        scope,
        RolePresetEntityType(),
        Permission.HARD_DELETE,
    )
    return preset_ids


async def _grant_on(db: ExtendedAsyncSAEngine, actors: Actors, preset_id: RolePresetID) -> None:
    """HARD_DELETE for the ungranted actor on this one preset, row or no row."""
    await grant(
        db,
        actors.user_id(Actor.UNGRANTED),
        RolePresetEntityType(),
        preset_id,
        RolePresetEntityType(),
        Permission.HARD_DELETE,
    )


async def _remaining(db: ExtendedAsyncSAEngine, preset_ids: list[RolePresetID]) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(RolePresetRow.id).where(RolePresetRow.id.in_(preset_ids))
        )
        return set(rows.all())


def _processor(harness: OpsHarness) -> Any:
    return harness.group(RolePresetEntityType()).global_partial_bulk_purge_ops(
        BulkPurgeRolePresetsAction
    )


def _spy_writes(monkeypatch: pytest.MonkeyPatch) -> list[list[EntityIdentifier]]:
    calls: list[list[EntityIdentifier]] = []
    original = OpsRepository.partial_bulk_purge_entities

    async def spy(self: OpsRepository[Any], purgers: Mapping[EntityIdentifier, Any]) -> Any:
        calls.append(list(purgers))
        return await original(self, purgers)

    monkeypatch.setattr(OpsRepository, "partial_bulk_purge_entities", spy)
    return calls


async def _action_ids(db: ExtendedAsyncSAEngine) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(AuditLogRow.action_id).where(
                AuditLogRow.action_name == BulkPurgeRolePresetsAction.action_name()
            )
        )
        return set(rows.all())


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced"),
        [
            pytest.param(Actor.SUPERADMIN, True, id="actor-1"),
            pytest.param(Actor.GRANTED, True, id="actor-3"),
            pytest.param(Actor.UNGRANTED, False, id="actor-6"),
        ],
    )
    async def test_every_id_is_purged(
        self,
        preset_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        presets: list[RolePresetID],
        actor: Actor,
        enforced: bool,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            result = await _processor(harness).run(BulkPurgeRolePresetsAction(ids=presets))

        assert [item.value.id for item in result.items] == presets
        assert await _remaining(preset_db, presets) == set()

    @pytest.mark.parametrize(
        "actor",
        [pytest.param(Actor.MONITOR, id="actor-2"), pytest.param(Actor.UNGRANTED, id="actor-4")],
    )
    async def test_every_item_is_denied(
        self,
        preset_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        presets: list[RolePresetID],
        monkeypatch: pytest.MonkeyPatch,
        actor: Actor,
    ) -> None:
        writes = _spy_writes(monkeypatch)

        with actors.acting_as(actor):
            result = await _processor(harness).run(BulkPurgeRolePresetsAction(ids=presets))

        assert all(item.is_denied for item in result.items)
        assert all(isinstance(item.error, NotEnoughPermission) for item in result.items)
        assert [entity_id for call in writes for entity_id in call] == []
        assert await _remaining(preset_db, presets) == set(presets)

    @pytest.mark.parametrize(
        "enforced",
        [
            pytest.param(True, id="actor-5", marks=ANONYMOUS_NOT_REFUSED),
            pytest.param(False, id="actor-5-rbac-off", marks=ANONYMOUS_NOT_REFUSED),
        ],
    )
    async def test_a_caller_with_no_user_is_refused_the_run(
        self,
        preset_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        presets: list[RolePresetID],
        monkeypatch: pytest.MonkeyPatch,
        enforced: bool,
    ) -> None:
        harness.enforce(enforced)
        writes = _spy_writes(monkeypatch)

        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(BulkPurgeRolePresetsAction(ids=presets))

        assert writes == []
        assert await _remaining(preset_db, presets) == set(presets)
        assert_refused(raised.value)


class TestTarget:
    async def test_a_missing_id_fails_alone(
        self,
        preset_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        presets: list[RolePresetID],
    ) -> None:
        """target-1."""
        missing = RolePresetID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(
                BulkPurgeRolePresetsAction(ids=[presets[0], missing])
            )

        purged, gone = result.items
        assert purged.value.id == presets[0]
        assert isinstance(gone.error, EntityNotFoundError)
        assert not gone.is_denied
        assert await _remaining(preset_db, presets) == {presets[1]}

    async def test_a_missing_id_is_denied_to_a_user(
        self, harness: OpsHarness, actors: Actors, presets: list[RolePresetID]
    ) -> None:
        """target-2."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                BulkPurgeRolePresetsAction(ids=[RolePresetID(uuid.uuid4())])
            )

        (item,) = result.items
        assert item.is_denied
        assert isinstance(item.error, NotEnoughPermission)


class TestMulti:
    async def test_a_denied_entity_is_left_as_it_was(
        self,
        preset_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        presets: list[RolePresetID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """multi-1."""
        allowed, denied = presets
        await _grant_on(preset_db, actors, allowed)
        writes = _spy_writes(monkeypatch)

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(BulkPurgeRolePresetsAction(ids=presets))

        purged, refused = result.items
        assert purged.value.id == allowed
        assert refused.is_denied
        assert isinstance(refused.error, NotEnoughPermission)
        assert writes == [[allowed]]
        assert await _remaining(preset_db, presets) == {denied}

    async def test_a_repeated_id_is_written_once_and_answered_at_every_place(
        self,
        preset_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        presets: list[RolePresetID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """multi-2."""
        allowed, denied = presets
        await _grant_on(preset_db, actors, allowed)
        writes = _spy_writes(monkeypatch)

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(
                BulkPurgeRolePresetsAction(ids=[allowed, denied, allowed, denied])
            )

        assert result.items[0] == result.items[2]
        assert result.items[1] == result.items[3]
        assert result.items[0].value.id == allowed
        assert result.items[1].is_denied
        assert writes == [[allowed]]

    async def test_no_ids_answer_nothing(
        self, harness: OpsHarness, actors: Actors, presets: list[RolePresetID]
    ) -> None:
        """multi-3."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(BulkPurgeRolePresetsAction(ids=[]))

        assert result.items == []

    async def test_the_answer_keeps_the_order_asked_in(
        self, harness: OpsHarness, actors: Actors, presets: list[RolePresetID]
    ) -> None:
        """multi-4."""
        ids = [presets[1], RolePresetID(uuid.uuid4()), presets[0]]

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(BulkPurgeRolePresetsAction(ids=ids))

        assert [item.entity_id for item in result.items] == ids


class TestRecord:
    @pytest.mark.parametrize(
        ("actor", "exists", "status"),
        [
            pytest.param(Actor.GRANTED, True, OperationStatus.SUCCESS, id="record-1"),
            pytest.param(Actor.UNGRANTED, True, OperationStatus.DENIED, id="record-2"),
            pytest.param(Actor.SUPERADMIN, False, OperationStatus.ERROR, id="record-3"),
        ],
    )
    async def test_one_row_on_the_target(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        presets: list[RolePresetID],
        actor: Actor,
        exists: bool,
        status: OperationStatus,
    ) -> None:
        target = presets[0] if exists else RolePresetID(uuid.uuid4())

        with actors.acting_as(actor):
            await _processor(silent_reads_harness).run(BulkPurgeRolePresetsAction(ids=[target]))

        records = await silent_reads_harness.audit(BulkPurgeRolePresetsAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(target), ActionOperationType.PURGE, status)
        ]

    async def test_each_entity_is_recorded_with_its_own_status_under_one_action(
        self,
        preset_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        presets: list[RolePresetID],
    ) -> None:
        """record-4: the row-less id carries a grant, so it reaches the write and fails there."""
        allowed, denied = presets
        missing = RolePresetID(uuid.uuid4())
        await _grant_on(preset_db, actors, allowed)
        await _grant_on(preset_db, actors, missing)

        with actors.acting_as(Actor.UNGRANTED):
            await _processor(harness).run(
                BulkPurgeRolePresetsAction(ids=[allowed, denied, missing])
            )

        records = await harness.audit(BulkPurgeRolePresetsAction.action_name())
        assert {(r.entity_type, r.entity_id): r.status for r in records} == {
            entity_key(allowed): OperationStatus.SUCCESS,
            entity_key(denied): OperationStatus.DENIED,
            entity_key(missing): OperationStatus.ERROR,
        }
        assert len(records) == 3
        assert len(await _action_ids(preset_db)) == 1

    @DENIALS_RECORDED_AS_ERROR_ON_A_FAILED_RUN
    async def test_a_failed_run_keeps_its_denials(
        self,
        preset_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        presets: list[RolePresetID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""
        allowed, denied = presets
        await _grant_on(preset_db, actors, allowed)

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the write failed")

        monkeypatch.setattr(OpsRepository, "partial_bulk_purge_entities", broken)

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(BulkPurgeRolePresetsAction(ids=presets))

        records = await harness.audit(BulkPurgeRolePresetsAction.action_name())
        assert {(r.entity_type, r.entity_id): r.status for r in records} == {
            entity_key(allowed): OperationStatus.ERROR,
            entity_key(denied): OperationStatus.DENIED,
        }

    @ANONYMOUS_RECORDED_AS_ERROR
    async def test_a_caller_with_no_user_is_denied_on_every_entity(
        self, harness: OpsHarness, actors: Actors, presets: list[RolePresetID]
    ) -> None:
        """record-6."""
        with actors.acting_as(Actor.ANONYMOUS):
            with contextlib.suppress(BackendAIError):
                await _processor(harness).run(BulkPurgeRolePresetsAction(ids=presets))

        records = await harness.audit(BulkPurgeRolePresetsAction.action_name())
        assert sorted(((r.entity_type, r.entity_id), r.status) for r in records) == sorted(
            (entity_key(preset_id), OperationStatus.DENIED) for preset_id in presets
        )

    async def test_no_ids_record_nothing(
        self, harness: OpsHarness, actors: Actors, presets: list[RolePresetID]
    ) -> None:
        """record-7."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(BulkPurgeRolePresetsAction(ids=[]))

        assert await harness.audit(BulkPurgeRolePresetsAction.action_name()) == []

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        preset_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        presets: list[RolePresetID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-8."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(BulkPurgeRolePresetsAction(ids=[presets[0]]))

        records = await harness.audit(BulkPurgeRolePresetsAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _remaining(preset_db, presets) == set(presets)


class TestResult:
    async def test_the_value_is_the_row_before_the_purge(
        self, harness: OpsHarness, actors: Actors, presets: list[RolePresetID]
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(BulkPurgeRolePresetsAction(ids=[presets[0]]))

        (item,) = result.items
        assert item.value.id == presets[0]
        assert item.value.name == f"preset-{presets[0].hex[:8]}"


@dataclass
class _PurgeAction(PartialBulkPurgeGlobalEntityOpsAction[Any, Any]):
    """A test-only action of this shape over whichever real purgers it is handed."""

    purgers: Sequence[GuardedEntityPurger[Any, Any]]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "test_bulk_purge"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [purger.entity_id() for purger in self.purgers]

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, GuardedEntityPurger[Any, Any]]:
        return {purger.entity_id(): purger for purger in self.purgers}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, purgers=[purger for purger in self.purgers if purger.entity_id() in allowed]
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


async def _roles_left(db: ExtendedAsyncSAEngine, role_ids: list[RoleID]) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(sa.select(RoleRow.id).where(RoleRow.id.in_(role_ids)))
        return set(rows.all())


class TestGuard:
    """Rows that need a guard, run on the role purger, which declines a SYSTEM role."""

    async def test_a_guarded_id_fails_alone(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-3."""
        custom = await _seed_role(ops_db, actors, RoleSource.CUSTOM)
        system = await _seed_role(ops_db, actors, RoleSource.SYSTEM)
        processor = harness.group(RoleEntityType()).global_partial_bulk_purge_ops(_PurgeAction)

        with actors.acting_as(Actor.SUPERADMIN):
            result = await processor.run(
                _PurgeAction(purgers=[RolePurger(role_id=custom), RolePurger(role_id=system)])
            )

        purged, refused = result.items
        assert purged.value is not None
        assert purged.value.id == custom
        assert isinstance(refused.error, SystemRoleNotEditable)
        assert not refused.is_denied
        assert await _roles_left(ops_db, [custom, system]) == {system}

    async def test_a_guard_failure_is_recorded_as_an_error(
        self, ops_db: ExtendedAsyncSAEngine, silent_reads_harness: OpsHarness, actors: Actors
    ) -> None:
        """record-3: a guard failure."""
        system = await _seed_role(ops_db, actors, RoleSource.SYSTEM)
        processor = silent_reads_harness.group(RoleEntityType()).global_partial_bulk_purge_ops(
            _PurgeAction
        )

        with actors.acting_as(Actor.SUPERADMIN):
            await processor.run(_PurgeAction(purgers=[RolePurger(role_id=system)]))

        records = await silent_reads_harness.audit(_PurgeAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(system), ActionOperationType.PURGE, OperationStatus.ERROR)
        ]


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


async def _seed_slot_type(db: ExtendedAsyncSAEngine, slot_name: str) -> ResourceSlotTypeUUID:
    async with db.begin_session() as sess:
        slot = ResourceSlotTypeRow(
            slot_name=slot_name, slot_type="count", display_name=slot_name, rank=3
        )
        sess.add(slot)
        await sess.flush()
        slot_type_id = slot.uuid
        await sess.commit()
    return slot_type_id


async def _report_slot(db: ExtendedAsyncSAEngine, slot_name: str) -> None:
    """An agent reporting the slot, which the purger's conflict check refuses."""
    resource_group_id = ResourceGroupID(uuid.uuid4())
    agent_uuid = AgentUUID(uuid.uuid4())
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
                slot_name=slot_name,
                capacity=Decimal(2),
            )
        )
        await sess.commit()


class TestConflict:
    async def test_a_referenced_id_fails_alone(
        self, slot_type_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-4: the resource slot type purger refuses a slot an agent still reports."""
        free = await _seed_slot_type(slot_type_db, "free.device")
        reported = await _seed_slot_type(slot_type_db, "cuda.device")
        await _report_slot(slot_type_db, "cuda.device")
        processor = harness.group(ResourceSlotTypeEntityType()).global_partial_bulk_purge_ops(
            _PurgeAction
        )

        with actors.acting_as(Actor.SUPERADMIN):
            result = await processor.run(
                _PurgeAction(
                    purgers=[
                        ResourceSlotTypePurger(slot_name="free.device", slot_type_id=free),
                        ResourceSlotTypePurger(slot_name="cuda.device", slot_type_id=reported),
                    ]
                )
            )

        purged, refused = result.items
        assert purged.error is None
        assert isinstance(refused.error, ResourceSlotTypeInUse)
        assert not refused.is_denied
        async with slot_type_db.begin_readonly_session() as sess:
            left = await sess.scalars(sa.select(ResourceSlotTypeRow.slot_name))
            assert set(left.all()) == {"cuda.device"}
