"""``single_get_ops``: reading one entity by id, with the project as the representative."""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Callable
from typing import Any

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.project.actions.search_projects import GetProjectAction
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    ANONYMOUS_RUNS_UNENFORCED,
    MONITOR_READ_REFUSED,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    seed_project,
)


@pytest.fixture
async def project(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> ProjectID:
    project_id = await seed_project(ops_db, actors)
    await grant(
        ops_db,
        actors.user_id(Actor.GRANTED),
        DomainEntityType(),
        actors.domain_id,
        ProjectEntityType(),
        Permission.READ,
    )
    return project_id


def _processor(harness: OpsHarness) -> Any:
    return harness.group(ProjectEntityType()).single_get_ops(GetProjectAction)


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced", "error"),
        [
            pytest.param(Actor.SUPERADMIN, True, None, id="actor-1"),
            pytest.param(Actor.MONITOR, True, None, id="actor-2", marks=MONITOR_READ_REFUSED),
            pytest.param(Actor.GRANTED, True, None, id="actor-3"),
            pytest.param(Actor.UNGRANTED, True, NotEnoughPermission, id="actor-4"),
            pytest.param(
                Actor.ANONYMOUS, True, BackendAIError, id="actor-5", marks=ANONYMOUS_NOT_REFUSED
            ),
            pytest.param(
                Actor.ANONYMOUS,
                False,
                BackendAIError,
                id="actor-5-rbac-off",
                marks=ANONYMOUS_RUNS_UNENFORCED,
            ),
            pytest.param(Actor.UNGRANTED, False, None, id="actor-6"),
        ],
    )
    async def test_actor(
        self,
        harness: OpsHarness,
        actors: Actors,
        project: ProjectID,
        repository_calls: Callable[[str], list[Any]],
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)
        action = GetProjectAction(project_id=project)
        reads = repository_calls("get")

        with actors.acting_as(actor):
            if error is None:
                result = await _processor(harness).run(action)
                assert result.data.id == project
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(action)
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert len(reads) == (0 if error else 1)


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
        missing = ProjectID(uuid.uuid4())

        with actors.acting_as(actor):
            with pytest.raises(error):
                await _processor(harness).run(GetProjectAction(project_id=missing))


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
        harness: OpsHarness,
        actors: Actors,
        project: ProjectID,
        actor: Actor,
        exists: bool,
        status: OperationStatus,
    ) -> None:
        target = project if exists else ProjectID(uuid.uuid4())

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(harness).run(GetProjectAction(project_id=target))

        records = await harness.audit(GetProjectAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(target), ActionOperationType.GET, status)
        ]

    async def test_a_read_is_not_recorded_unless_opted_in(
        self, silent_reads_harness: OpsHarness, actors: Actors, project: ProjectID
    ) -> None:
        """record-1, with the read left out of the policy."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(GetProjectAction(project_id=project))

        assert await silent_reads_harness.audit(GetProjectAction.action_name()) == []

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        harness: OpsHarness,
        actors: Actors,
        project: ProjectID,
        repository_calls: Callable[[str], list[Any]],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""
        reads = repository_calls("get")

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(GetProjectAction(project_id=project))

        records = await harness.audit(GetProjectAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert reads == []


class TestResult:
    async def test_the_data_is_the_entity_read(
        self, harness: OpsHarness, actors: Actors, project: ProjectID
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(GetProjectAction(project_id=project))

        assert result.data.id == project
        assert result.data.name == f"project-{project.hex[:8]}"
