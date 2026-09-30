"""``partial_bulk_get_ops``: reading the named entities, with the project as the representative."""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Sequence
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.project.actions.bulk_get import BulkGetProjectsAction
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    MONITOR_READ_REFUSED,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    seed_project,
)

DENIALS_RECORDED_AS_ERROR_ON_A_FAILED_RUN = pytest.mark.xfail(
    strict=True, reason="a run that raises records the ids it denied as ERROR, not DENIED"
)


@pytest.fixture
async def projects(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> list[ProjectID]:
    project_ids = [await seed_project(ops_db, actors) for _ in range(2)]
    await grant(
        ops_db,
        actors.user_id(Actor.GRANTED),
        DomainEntityType(),
        actors.domain_id,
        ProjectEntityType(),
        Permission.READ,
    )
    return project_ids


async def _grant_on(db: ExtendedAsyncSAEngine, actors: Actors, project_id: ProjectID) -> None:
    """READ for the ungranted actor on this one project, row or no row."""
    await grant(
        db,
        actors.user_id(Actor.UNGRANTED),
        ProjectEntityType(),
        project_id,
        ProjectEntityType(),
        Permission.READ,
    )


def _processor(harness: OpsHarness) -> Any:
    return harness.group(ProjectEntityType()).partial_bulk_get_ops(BulkGetProjectsAction)


def _spy_reads(monkeypatch: pytest.MonkeyPatch) -> list[list[EntityIdentifier]]:
    calls: list[list[EntityIdentifier]] = []
    original = OpsRepository.bulk_get

    async def spy(
        self: OpsRepository[Any], querier: Any, entity_ids: Sequence[EntityIdentifier]
    ) -> Any:
        calls.append(list(entity_ids))
        return await original(self, querier, entity_ids)

    monkeypatch.setattr(OpsRepository, "bulk_get", spy)
    return calls


async def _action_ids(db: ExtendedAsyncSAEngine) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(AuditLogRow.action_id).where(
                AuditLogRow.action_name == BulkGetProjectsAction.action_name()
            )
        )
        return set(rows.all())


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced"),
        [
            pytest.param(Actor.SUPERADMIN, True, id="actor-1"),
            pytest.param(Actor.MONITOR, True, id="actor-2", marks=MONITOR_READ_REFUSED),
            pytest.param(Actor.GRANTED, True, id="actor-3"),
            pytest.param(Actor.UNGRANTED, False, id="actor-6"),
        ],
    )
    async def test_every_id_is_read(
        self,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        actor: Actor,
        enforced: bool,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            result = await _processor(harness).run(BulkGetProjectsAction(ids=projects))

        assert [item.value.id for item in result.items] == projects

    async def test_an_ungranted_user_is_denied_every_item(
        self,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """actor-4."""
        reads = _spy_reads(monkeypatch)

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(BulkGetProjectsAction(ids=projects))

        assert all(item.is_denied for item in result.items)
        assert all(isinstance(item.error, NotEnoughPermission) for item in result.items)
        assert [entity_id for call in reads for entity_id in call] == []

    @pytest.mark.parametrize(
        "enforced",
        [
            pytest.param(True, id="actor-5", marks=ANONYMOUS_NOT_REFUSED),
            pytest.param(False, id="actor-5-rbac-off", marks=ANONYMOUS_NOT_REFUSED),
        ],
    )
    async def test_a_caller_with_no_user_is_refused_the_run(
        self,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        monkeypatch: pytest.MonkeyPatch,
        enforced: bool,
    ) -> None:
        harness.enforce(enforced)
        reads = _spy_reads(monkeypatch)

        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(BulkGetProjectsAction(ids=projects))

        assert reads == []
        assert_refused(raised.value)


class TestTarget:
    async def test_a_missing_id_fails_alone(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """target-1."""
        missing = ProjectID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(
                BulkGetProjectsAction(ids=[projects[0], missing])
            )

        found, gone = result.items
        assert found.value.id == projects[0]
        assert isinstance(gone.error, EntityNotFoundError)
        assert not gone.is_denied

    async def test_a_missing_id_is_denied_to_a_user(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """target-2."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                BulkGetProjectsAction(ids=[ProjectID(uuid.uuid4())])
            )

        (item,) = result.items
        assert item.is_denied
        assert isinstance(item.error, NotEnoughPermission)


class TestMulti:
    async def test_a_denied_id_is_never_read(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """multi-1."""
        allowed, denied = projects
        await _grant_on(ops_db, actors, allowed)
        reads = _spy_reads(monkeypatch)

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(BulkGetProjectsAction(ids=projects))

        read, refused = result.items
        assert read.value.id == allowed
        assert refused.is_denied
        assert isinstance(refused.error, NotEnoughPermission)
        assert reads == [[allowed]]

    async def test_a_repeated_id_is_answered_the_same_at_every_place(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """multi-2."""
        allowed, denied = projects
        await _grant_on(ops_db, actors, allowed)

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(
                BulkGetProjectsAction(ids=[allowed, denied, allowed, denied])
            )

        assert result.items[0] == result.items[2]
        assert result.items[1] == result.items[3]
        assert result.items[0].value.id == allowed
        assert result.items[1].is_denied

    async def test_no_ids_answer_nothing(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """multi-3."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(BulkGetProjectsAction(ids=[]))

        assert result.items == []

    async def test_the_answer_keeps_the_order_asked_in(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """multi-4."""
        ids = [projects[1], ProjectID(uuid.uuid4()), projects[0]]

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(BulkGetProjectsAction(ids=ids))

        assert [item.entity_id for item in result.items] == ids


class TestRecord:
    @pytest.mark.parametrize(
        ("harness_fixture", "recorded"),
        [
            pytest.param("harness", True, id="record-1"),
            pytest.param("silent_reads_harness", False, id="record-1-not-selected"),
        ],
    )
    async def test_a_read_entity_follows_the_policy(
        self,
        request: pytest.FixtureRequest,
        actors: Actors,
        projects: list[ProjectID],
        harness_fixture: str,
        recorded: bool,
    ) -> None:
        harness: OpsHarness = request.getfixturevalue(harness_fixture)

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(BulkGetProjectsAction(ids=projects))

        records = await harness.audit(BulkGetProjectsAction.action_name())
        expected = [
            (entity_key(project_id), ActionOperationType.GET, OperationStatus.SUCCESS)
            for project_id in projects
        ]
        assert sorted(((r.entity_type, r.entity_id), r.operation, r.status) for r in records) == (
            sorted(expected) if recorded else []
        )

    @pytest.mark.parametrize(
        ("actor", "exists", "status"),
        [
            pytest.param(Actor.UNGRANTED, True, OperationStatus.DENIED, id="record-2"),
            pytest.param(Actor.SUPERADMIN, False, OperationStatus.ERROR, id="record-3"),
        ],
    )
    async def test_one_row_on_the_target(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        actor: Actor,
        exists: bool,
        status: OperationStatus,
    ) -> None:
        target = projects[0] if exists else ProjectID(uuid.uuid4())

        with actors.acting_as(actor):
            await _processor(silent_reads_harness).run(BulkGetProjectsAction(ids=[target]))

        records = await silent_reads_harness.audit(BulkGetProjectsAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(target), ActionOperationType.GET, status)
        ]

    async def test_each_entity_is_recorded_with_its_own_status_under_one_action(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """record-4: the row-less id carries a grant, so it reaches the read and fails there."""
        allowed, denied = projects
        missing = ProjectID(uuid.uuid4())
        await _grant_on(ops_db, actors, allowed)
        await _grant_on(ops_db, actors, missing)

        with actors.acting_as(Actor.UNGRANTED):
            await _processor(harness).run(BulkGetProjectsAction(ids=[allowed, denied, missing]))

        records = await harness.audit(BulkGetProjectsAction.action_name())
        assert {(r.entity_type, r.entity_id): r.status for r in records} == {
            entity_key(allowed): OperationStatus.SUCCESS,
            entity_key(denied): OperationStatus.DENIED,
            entity_key(missing): OperationStatus.ERROR,
        }
        assert len(records) == 3
        assert len(await _action_ids(ops_db)) == 1

    @DENIALS_RECORDED_AS_ERROR_ON_A_FAILED_RUN
    async def test_a_failed_run_keeps_its_denials(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""
        allowed, denied = projects
        await _grant_on(ops_db, actors, allowed)

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the read failed")

        monkeypatch.setattr(OpsRepository, "bulk_get", broken)

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(BulkGetProjectsAction(ids=projects))

        records = await harness.audit(BulkGetProjectsAction.action_name())
        assert {(r.entity_type, r.entity_id): r.status for r in records} == {
            entity_key(allowed): OperationStatus.ERROR,
            entity_key(denied): OperationStatus.DENIED,
        }

    @ANONYMOUS_RECORDED_AS_ERROR
    async def test_a_caller_with_no_user_is_denied_on_every_entity(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """record-6."""
        with actors.acting_as(Actor.ANONYMOUS):
            with contextlib.suppress(BackendAIError):
                await _processor(harness).run(BulkGetProjectsAction(ids=projects))

        records = await harness.audit(BulkGetProjectsAction.action_name())
        assert sorted(((r.entity_type, r.entity_id), r.status) for r in records) == sorted(
            (entity_key(project_id), OperationStatus.DENIED) for project_id in projects
        )

    async def test_no_ids_record_nothing(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """record-7."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(BulkGetProjectsAction(ids=[]))

        assert await harness.audit(BulkGetProjectsAction.action_name()) == []

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-8."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)
        reads = _spy_reads(monkeypatch)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(BulkGetProjectsAction(ids=[projects[0]]))

        records = await harness.audit(BulkGetProjectsAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert reads == []


class TestResult:
    async def test_the_value_is_the_entity_read(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(BulkGetProjectsAction(ids=[projects[0]]))

        (item,) = result.items
        assert item.error is None
        assert item.value.id == projects[0]
        assert item.value.name == f"project-{projects[0].hex[:8]}"

    async def test_a_value_a_failure_and_a_denial_are_told_apart(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """result-2."""
        allowed, denied = projects
        missing = ProjectID(uuid.uuid4())
        await _grant_on(ops_db, actors, allowed)
        await _grant_on(ops_db, actors, missing)

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(
                BulkGetProjectsAction(ids=[allowed, missing, denied])
            )

        read, gone, refused = result.items
        assert (read.value is not None, read.error is None, read.is_denied) == (True, True, False)
        assert isinstance(gone.error, EntityNotFoundError)
        assert (gone.value, gone.is_denied) == (None, False)
        assert isinstance(refused.error, NotEnoughPermission)
        assert (refused.value, refused.is_denied) == (None, True)
