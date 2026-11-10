"""``single_restore_ops``: restoring one soft-deleted entity, with the project as the
representative.

target-4 runs a test action of this shape carrying the project soft-delete updater,
the spec that declares two guards.
"""

from __future__ import annotations

import contextlib
import uuid
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.ops.base import RestoreSingleEntityOpsAction
from ai.backend.manager.data.project.types import ProjectData, ProjectStatus, ProjectType
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import ProjectPurgeInProgress
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.updaters import (
    ProjectRestoreUpdater,
    ProjectSoftDeleteUpdater,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.project.actions.restore_project import RestoreProjectAction
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
    project_status,
    seed_project,
)


@dataclass(frozen=True)
class _TwoGuardAction(RestoreSingleEntityOpsAction[ProjectRow, ProjectData]):
    """This shape carrying an updater that declares two guards."""

    updater: ProjectSoftDeleteUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.project_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "two_guard_restore"

    @override
    def to_updater(self) -> ProjectSoftDeleteUpdater:
        return self.updater


@pytest.fixture
async def project(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> ProjectID:
    project_id = await seed_project(ops_db, actors, status=ProjectStatus.DELETED)
    for actor, permission in (
        (Actor.GRANTED, Permission.SOFT_DELETE),
        (Actor.READ_ONLY, Permission.READ),
    ):
        await grant(
            ops_db,
            actors.user_id(actor),
            DomainEntityType(),
            actors.domain_id,
            ProjectEntityType(),
            permission,
        )
    return project_id


def _processor(harness: OpsHarness) -> Any:
    return harness.group(ProjectEntityType()).single_restore_ops(RestoreProjectAction)


def _restore(project_id: ProjectID) -> RestoreProjectAction:
    return RestoreProjectAction(updater=ProjectRestoreUpdater(project_id=project_id))


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
        project: ProjectID,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(_restore(project))
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_restore(project))
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        expected = ProjectStatus.DELETED if error else ProjectStatus.ACTIVE
        assert await project_status(ops_db, project) == expected


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
        project: ProjectID,
        actor: Actor,
        error: type[Exception],
    ) -> None:
        with actors.acting_as(actor):
            with pytest.raises(error):
                await _processor(harness).run(_restore(ProjectID(uuid.uuid4())))

    async def test_a_failing_guard_leaves_the_row(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-3."""
        purging = await seed_project(ops_db, actors, status=ProjectStatus.PURGING)

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(ProjectPurgeInProgress):
                await _processor(harness).run(_restore(purging))

        assert await project_status(ops_db, purging) == ProjectStatus.PURGING

    async def test_the_first_failing_guard_answers(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-4: a personal project being purged fails both guards."""
        both = await seed_project(
            ops_db, actors, project_type=ProjectType.PERSONAL, status=ProjectStatus.PURGING
        )
        processor = harness.group(ProjectEntityType()).single_restore_ops(_TwoGuardAction)
        action = _TwoGuardAction(updater=ProjectSoftDeleteUpdater(project_id=both))

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(ProjectPurgeInProgress):
                await processor.run(action)

        assert await project_status(ops_db, both) == ProjectStatus.PURGING

    async def test_the_status_returns_to_active(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, project: ProjectID
    ) -> None:
        """target-5."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_restore(project))

        assert await project_status(ops_db, project) == ProjectStatus.ACTIVE


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
        project: ProjectID,
        actor: Actor,
        exists: bool,
        status: OperationStatus,
    ) -> None:
        target = project if exists else ProjectID(uuid.uuid4())

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_restore(target))

        records = await silent_reads_harness.audit(RestoreProjectAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(target), ActionOperationType.RESTORE, status)
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        project: ProjectID,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_restore(project))

        records = await harness.audit(RestoreProjectAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await project_status(ops_db, project) == ProjectStatus.DELETED


class TestResult:
    async def test_the_data_is_the_row_after_the_write(
        self, harness: OpsHarness, actors: Actors, project: ProjectID
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_restore(project))

        assert result.data.id == project
        assert result.data.is_active is True
