"""``global_update_ops``: editing one global entity by key, with the resource slot type as
the representative."""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_slot import (
    ResourceSlotTypeEntityType,
    ResourceSlotTypeUUID,
)
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.ops.base import UpdateGlobalOpsAction
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.project.types import ProjectData, ProjectStatus, ProjectType
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.resource import ProjectPurgeInProgress
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.updaters import ProjectSoftDeleteUpdater
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.resource_slot.updaters import ResourceSlotTypeUpdater
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.resource_slot.actions.update import UpdateResourceSlotTypeAction
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    grant,
    project_status,
    seed_project,
)


async def _grant_global(
    db: ExtendedAsyncSAEngine, user_id: UserID, entity_type: EntityType, permission: Permission
) -> None:
    scope = global_entity_id(GlobalEntityName.GLOBAL)
    await grant(db, user_id, scope.entity_type(), scope, entity_type, permission)


@pytest.fixture
async def slot_type_db(
    ops_db: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(ops_db, [ResourceSlotTypeRow]):
        yield ops_db


@pytest.fixture
async def slot_type(slot_type_db: ExtendedAsyncSAEngine, actors: Actors) -> ResourceSlotTypeUUID:
    async with slot_type_db.begin_session() as sess:
        row = ResourceSlotTypeRow(
            slot_name="cuda.device", slot_type="count", display_name="GPU", rank=3
        )
        sess.add(row)
        await sess.flush()
        slot_type_id = ResourceSlotTypeUUID(row.uuid)
        await sess.commit()
    for actor, permission in (
        (Actor.GRANTED, Permission.UPDATE),
        (Actor.READ_ONLY, Permission.READ),
    ):
        await _grant_global(
            slot_type_db, actors.user_id(actor), ResourceSlotTypeEntityType(), permission
        )
    return slot_type_id


async def _display_name(
    db: ExtendedAsyncSAEngine, slot_type_id: ResourceSlotTypeUUID
) -> str | None:
    async with db.begin_readonly_session() as sess:
        name: str | None = await sess.scalar(
            sa.select(ResourceSlotTypeRow.display_name).where(
                ResourceSlotTypeRow.uuid == slot_type_id
            )
        )
    return name


def _processor(harness: OpsHarness) -> Any:
    return harness.group(ResourceSlotTypeEntityType()).global_update_ops(
        UpdateResourceSlotTypeAction
    )


def _rename(
    slot_type_id: ResourceSlotTypeUUID, name: str = "edited"
) -> UpdateResourceSlotTypeAction:
    return UpdateResourceSlotTypeAction(
        updater=ResourceSlotTypeUpdater(
            slot_type_id=slot_type_id, display_name=OptionalState.update(name)
        )
    )


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced", "error"),
        [
            pytest.param(Actor.SUPERADMIN, True, None, id="actor-1"),
            pytest.param(Actor.MONITOR, True, InsufficientPrivilege, id="actor-2"),
            pytest.param(Actor.GRANTED, True, None, id="actor-3"),
            pytest.param(Actor.READ_ONLY, True, InsufficientPrivilege, id="actor-4"),
            pytest.param(Actor.UNGRANTED, True, InsufficientPrivilege, id="actor-7"),
            pytest.param(
                Actor.ANONYMOUS, True, BackendAIError, id="actor-8", marks=ANONYMOUS_NOT_REFUSED
            ),
            pytest.param(
                Actor.ANONYMOUS,
                False,
                BackendAIError,
                id="actor-8-rbac-off",
                marks=ANONYMOUS_NOT_REFUSED,
            ),
            pytest.param(Actor.SUPERADMIN, False, None, id="actor-9"),
            pytest.param(Actor.MONITOR, False, InsufficientPrivilege, id="actor-10"),
            pytest.param(Actor.GRANTED, False, InsufficientPrivilege, id="actor-11"),
        ],
    )
    async def test_actor(
        self,
        slot_type_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        slot_type: ResourceSlotTypeUUID,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(_rename(slot_type))
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_rename(slot_type))
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert await _display_name(slot_type_db, slot_type) == ("GPU" if error else "edited")

    @pytest.mark.parametrize(
        ("at_global", "entity_type"),
        [
            pytest.param(False, ResourceSlotTypeEntityType(), id="actor-5"),
            pytest.param(True, ProjectEntityType(), id="actor-6"),
        ],
    )
    async def test_a_grant_off_the_global_type_is_refused(
        self,
        slot_type_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        slot_type: ResourceSlotTypeUUID,
        at_global: bool,
        entity_type: EntityType,
    ) -> None:
        """A domain grant on the type, or a global grant on another type, is not enough."""
        user_id = actors.user_id(Actor.UNGRANTED)
        if at_global:
            await _grant_global(slot_type_db, user_id, entity_type, Permission.full())
        else:
            await grant(
                slot_type_db,
                user_id,
                DomainEntityType(),
                actors.domain_id,
                entity_type,
                Permission.full(),
            )

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(InsufficientPrivilege):
                await _processor(harness).run(_rename(slot_type))

        assert await _display_name(slot_type_db, slot_type) == "GPU"


class TestTarget:
    async def test_an_existing_key_is_updated(
        self,
        slot_type_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        slot_type: ResourceSlotTypeUUID,
    ) -> None:
        """target-1."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_rename(slot_type))

        assert await _display_name(slot_type_db, slot_type) == "edited"

    async def test_a_missing_key_is_not_found(
        self, harness: OpsHarness, actors: Actors, slot_type: ResourceSlotTypeUUID
    ) -> None:
        """target-2."""
        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(EntityNotFoundError):
                await _processor(harness).run(_rename(ResourceSlotTypeUUID(uuid.uuid4())))


@dataclass
class _SoftDeleteProjectGlobally(UpdateGlobalOpsAction[ProjectRow, ProjectData]):
    """Test-only: the wired action's updater declares no guard; the project's declares two."""

    updater: ProjectSoftDeleteUpdater

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ProjectEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "test_global_soft_delete_project"

    @override
    def to_updater(self) -> ProjectSoftDeleteUpdater:
        return self.updater


class TestGuard:
    @pytest.mark.parametrize(
        ("project_type", "error"),
        [
            pytest.param(ProjectType.GENERAL, ProjectPurgeInProgress, id="target-3"),
            pytest.param(ProjectType.PERSONAL, ProjectPurgeInProgress, id="target-4"),
        ],
    )
    async def test_a_failing_guard_leaves_the_row(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        project_type: ProjectType,
        error: type[Exception],
    ) -> None:
        """A purging project fails one guard; a personal one fails both, the first answering."""
        project_id = await seed_project(
            ops_db, actors, project_type=project_type, status=ProjectStatus.PURGING
        )
        processor = harness.group(ProjectEntityType()).global_update_ops(_SoftDeleteProjectGlobally)
        action = _SoftDeleteProjectGlobally(updater=ProjectSoftDeleteUpdater(project_id=project_id))

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(error):
                await processor.run(action)

        assert await project_status(ops_db, project_id) == ProjectStatus.PURGING


class TestRecord:
    @pytest.mark.parametrize(
        ("actor", "exists", "status"),
        [
            pytest.param(Actor.GRANTED, True, OperationStatus.SUCCESS, id="record-1"),
            pytest.param(Actor.UNGRANTED, True, OperationStatus.DENIED, id="record-2"),
            pytest.param(Actor.GRANTED, False, OperationStatus.ERROR, id="record-3"),
            pytest.param(
                Actor.ANONYMOUS,
                True,
                OperationStatus.DENIED,
                id="record-4",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_one_row_with_no_target(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        slot_type: ResourceSlotTypeUUID,
        actor: Actor,
        exists: bool,
        status: OperationStatus,
    ) -> None:
        """A write is recorded whatever the read policy says."""
        target = slot_type if exists else ResourceSlotTypeUUID(uuid.uuid4())

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_rename(target))

        records = await silent_reads_harness.audit(UpdateResourceSlotTypeAction.action_name())
        assert [(r.entity_type, r.entity_id, r.operation, r.status) for r in records] == [
            (str(GlobalEntityType()), None, ActionOperationType.UPDATE, status)
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        slot_type_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        slot_type: ResourceSlotTypeUUID,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "governed_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_rename(slot_type))

        records = await harness.audit(UpdateResourceSlotTypeAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _display_name(slot_type_db, slot_type) == "GPU"


class TestResult:
    async def test_the_data_is_the_row_after_the_write(
        self, harness: OpsHarness, actors: Actors, slot_type: ResourceSlotTypeUUID
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_rename(slot_type, "after"))

        assert result.data.uuid == slot_type
        assert (result.data.slot_name, result.data.display_name) == ("cuda.device", "after")
