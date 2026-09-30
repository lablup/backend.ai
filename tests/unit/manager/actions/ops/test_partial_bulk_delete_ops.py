"""``partial_bulk_delete_ops``: soft-deleting named entities; the role preset represents it.

No wired updater of this shape declares a guard, so target-3 runs a test-only action over
the project's guarded updater.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Self, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.role_preset import RolePresetEntityType, RolePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.ops.base import DeletePartialBulkOpsAction
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.project.types import ProjectData, ProjectStatus
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import ProjectPurgeInProgress
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.updaters import ProjectSoftDeleteUpdater
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.role_preset.actions.delete import BulkDeleteRolePresetsAction
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
    project_status,
    provision,
    seed_project,
)

DENIALS_RECORDED_AS_ERROR_ON_A_FAILED_RUN = pytest.mark.xfail(
    strict=True, reason="a run that raises records the ids it denied as ERROR, not DENIED"
)


@pytest.fixture
async def preset_db(ops_db: ExtendedAsyncSAEngine) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(ops_db, [RolePresetRow]):
        yield ops_db


_SEEDED_DELETED = False


async def _seed_preset(db: ExtendedAsyncSAEngine) -> RolePresetID:
    preset_id = RolePresetID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            RolePresetRow(
                id=preset_id,
                name=f"preset-{preset_id.hex[:8]}",
                scope_type=ProjectEntityType(),
                deleted=_SEEDED_DELETED,
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
        Permission.SOFT_DELETE,
    )
    return preset_ids


async def _grant_on(db: ExtendedAsyncSAEngine, actors: Actors, preset_id: RolePresetID) -> None:
    """SOFT_DELETE for the ungranted actor on this one preset, row or no row."""
    await grant(
        db,
        actors.user_id(Actor.UNGRANTED),
        RolePresetEntityType(),
        preset_id,
        RolePresetEntityType(),
        Permission.SOFT_DELETE,
    )


async def _untouched(db: ExtendedAsyncSAEngine, preset_ids: list[RolePresetID]) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(RolePresetRow.id).where(
                RolePresetRow.id.in_(preset_ids), RolePresetRow.deleted == _SEEDED_DELETED
            )
        )
        return set(rows.all())


def _processor(harness: OpsHarness) -> Any:
    return harness.group(RolePresetEntityType()).partial_bulk_delete_ops(
        BulkDeleteRolePresetsAction
    )


def _spy_writes(monkeypatch: pytest.MonkeyPatch) -> list[list[EntityIdentifier]]:
    calls: list[list[EntityIdentifier]] = []
    original = OpsRepository.partial_bulk_update

    async def spy(self: OpsRepository[Any], updaters: Mapping[EntityIdentifier, Any]) -> Any:
        calls.append(list(updaters))
        return await original(self, updaters)

    monkeypatch.setattr(OpsRepository, "partial_bulk_update", spy)
    return calls


async def _action_ids(db: ExtendedAsyncSAEngine) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(AuditLogRow.action_id).where(
                AuditLogRow.action_name == BulkDeleteRolePresetsAction.action_name()
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
    async def test_every_id_is_deleted(
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
            result = await _processor(harness).run(BulkDeleteRolePresetsAction(ids=presets))

        assert [item.value.id for item in result.items] == presets
        assert await _untouched(preset_db, presets) == set()

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
            result = await _processor(harness).run(BulkDeleteRolePresetsAction(ids=presets))

        assert all(item.is_denied for item in result.items)
        assert all(isinstance(item.error, NotEnoughPermission) for item in result.items)
        assert [entity_id for call in writes for entity_id in call] == []
        assert await _untouched(preset_db, presets) == set(presets)

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
                await _processor(harness).run(BulkDeleteRolePresetsAction(ids=presets))

        assert writes == []
        assert await _untouched(preset_db, presets) == set(presets)
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
                BulkDeleteRolePresetsAction(ids=[presets[0], missing])
            )

        written, gone = result.items
        assert written.value.id == presets[0]
        assert isinstance(gone.error, EntityNotFoundError)
        assert not gone.is_denied
        assert await _untouched(preset_db, presets) == {presets[1]}

    async def test_a_missing_id_is_denied_to_a_user(
        self, harness: OpsHarness, actors: Actors, presets: list[RolePresetID]
    ) -> None:
        """target-2."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                BulkDeleteRolePresetsAction(ids=[RolePresetID(uuid.uuid4())])
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
            result = await _processor(harness).run(BulkDeleteRolePresetsAction(ids=presets))

        written, refused = result.items
        assert written.value.id == allowed
        assert refused.is_denied
        assert isinstance(refused.error, NotEnoughPermission)
        assert writes == [[allowed]]
        assert await _untouched(preset_db, presets) == {denied}

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
                BulkDeleteRolePresetsAction(ids=[allowed, denied, allowed, denied])
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
            result = await _processor(harness).run(BulkDeleteRolePresetsAction(ids=[]))

        assert result.items == []

    async def test_the_answer_keeps_the_order_asked_in(
        self, harness: OpsHarness, actors: Actors, presets: list[RolePresetID]
    ) -> None:
        """multi-4."""
        ids = [presets[1], RolePresetID(uuid.uuid4()), presets[0]]

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(BulkDeleteRolePresetsAction(ids=ids))

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
            await _processor(silent_reads_harness).run(BulkDeleteRolePresetsAction(ids=[target]))

        records = await silent_reads_harness.audit(BulkDeleteRolePresetsAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(target), ActionOperationType.DELETE, status)
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
                BulkDeleteRolePresetsAction(ids=[allowed, denied, missing])
            )

        records = await harness.audit(BulkDeleteRolePresetsAction.action_name())
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

        monkeypatch.setattr(OpsRepository, "partial_bulk_update", broken)

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(BulkDeleteRolePresetsAction(ids=presets))

        records = await harness.audit(BulkDeleteRolePresetsAction.action_name())
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
                await _processor(harness).run(BulkDeleteRolePresetsAction(ids=presets))

        records = await harness.audit(BulkDeleteRolePresetsAction.action_name())
        assert sorted(((r.entity_type, r.entity_id), r.status) for r in records) == sorted(
            (entity_key(preset_id), OperationStatus.DENIED) for preset_id in presets
        )

    async def test_no_ids_record_nothing(
        self, harness: OpsHarness, actors: Actors, presets: list[RolePresetID]
    ) -> None:
        """record-7."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(BulkDeleteRolePresetsAction(ids=[]))

        assert await harness.audit(BulkDeleteRolePresetsAction.action_name()) == []

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
                await _processor(harness).run(BulkDeleteRolePresetsAction(ids=[presets[0]]))

        records = await harness.audit(BulkDeleteRolePresetsAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _untouched(preset_db, presets) == set(presets)


class TestResult:
    async def test_the_value_is_the_row_after_the_write(
        self, harness: OpsHarness, actors: Actors, presets: list[RolePresetID]
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(BulkDeleteRolePresetsAction(ids=[presets[0]]))

        (item,) = result.items
        assert item.value.id == presets[0]
        assert item.value.deleted is not _SEEDED_DELETED


@dataclass
class _DeleteProjectsAction(DeletePartialBulkOpsAction[ProjectRow, ProjectData]):
    """A test-only action of this shape over the project's guarded soft delete."""

    ids: Sequence[ProjectID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "test_bulk_delete_projects"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, ProjectSoftDeleteUpdater]:
        return {
            project_id: ProjectSoftDeleteUpdater(project_id=project_id) for project_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])


class TestGuard:
    """Rows that need a guard, run on the project's soft delete updater."""

    async def test_a_guarded_id_fails_alone(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-3: a project being purged fails the guard."""
        writable = await seed_project(ops_db, actors, status=ProjectStatus.ACTIVE)
        purging = await seed_project(ops_db, actors, status=ProjectStatus.PURGING)
        processor = harness.group(ProjectEntityType()).partial_bulk_delete_ops(
            _DeleteProjectsAction
        )

        with actors.acting_as(Actor.SUPERADMIN):
            result = await processor.run(_DeleteProjectsAction(ids=[writable, purging]))

        written, refused = result.items
        assert written.value is not None
        assert written.value.id == writable
        assert isinstance(refused.error, ProjectPurgeInProgress)
        assert not refused.is_denied
        assert await project_status(ops_db, writable) == ProjectStatus.DELETED
        assert await project_status(ops_db, purging) == ProjectStatus.PURGING

    async def test_a_guard_failure_is_recorded_as_an_error(
        self, ops_db: ExtendedAsyncSAEngine, silent_reads_harness: OpsHarness, actors: Actors
    ) -> None:
        """record-3: a guard failure."""
        purging = await seed_project(ops_db, actors, status=ProjectStatus.PURGING)
        processor = silent_reads_harness.group(ProjectEntityType()).partial_bulk_delete_ops(
            _DeleteProjectsAction
        )

        with actors.acting_as(Actor.SUPERADMIN):
            await processor.run(_DeleteProjectsAction(ids=[purging]))

        records = await silent_reads_harness.audit(_DeleteProjectsAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(purging), ActionOperationType.DELETE, OperationStatus.ERROR)
        ]
