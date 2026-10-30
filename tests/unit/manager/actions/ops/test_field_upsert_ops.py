"""``upsert_ops (field)``: putting one field row under its owner, with an entity label on
a project as the representative.

A label's one unique key is the upsert key, so target-3 has no spec to run on.
"""

from __future__ import annotations

import contextlib
import uuid
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.entity_label import EntityLabelFieldType, EntityLabelKey
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.errors.base.not_found import NotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_label.upserters import EntityLabelUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.entity_label.actions.lookup_owner import (
    LookupBulkEntityLabelOwnerAction,
    LookupEntityLabelOwnerAction,
)
from ai.backend.manager.services.entity_label.actions.upsert import UpsertEntityLabelAction
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
    seed_project,
)

_MISSING_OWNER_IS_WRITTEN = pytest.mark.xfail(
    strict=True, reason="a label upsert under an owner id naming no entity writes the row"
)

_KEY = EntityLabelKey("team")


@pytest.fixture
async def project(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> ProjectID:
    project_id = await seed_project(ops_db, actors)
    for actor, permission in (
        (Actor.GRANTED, Permission.UPDATE),
        (Actor.READ_ONLY, Permission.READ),
    ):
        await grant(
            ops_db,
            actors.user_id(actor),
            ProjectEntityType(),
            project_id,
            ProjectEntityType(),
            permission,
        )
    return project_id


def _owner(project_id: uuid.UUID) -> RuntimeEntityID:
    return RuntimeEntityID(ProjectEntityType(), project_id)


async def _labels(db: ExtendedAsyncSAEngine, owner_id: uuid.UUID) -> list[tuple[str, str]]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.execute(
            sa.select(EntityLabelRow.key, EntityLabelRow.value).where(
                EntityLabelRow.entity_id == owner_id
            )
        )
        return [(key, value) for key, value in rows.all()]


def _processor(harness: OpsHarness) -> Any:
    labels = harness.registry.dangling_lookup_field_group(
        FieldGroupMeta(EntityLabelFieldType()),
        EntityLabelData,
        LookupEntityLabelOwnerAction,
        LookupBulkEntityLabelOwnerAction,
    )
    return labels.upsert_ops(UpsertEntityLabelAction)


def _put(owner_id: uuid.UUID, value: str = "ops", key: str = _KEY) -> UpsertEntityLabelAction:
    return UpsertEntityLabelAction(
        owner=_owner(owner_id), upserter=EntityLabelUpserter(key=EntityLabelKey(key), value=value)
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
        project: ProjectID,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(_put(project))
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_put(project))
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert await _labels(ops_db, project) == ([] if error else [(_KEY, "ops")])


class TestTarget:
    async def test_a_new_key_makes_a_row(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, project: ProjectID
    ) -> None:
        """target-1."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_put(project))

        assert await _labels(ops_db, project) == [(_KEY, "ops")]

    async def test_a_known_key_updates_its_row(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, project: ProjectID
    ) -> None:
        """target-2."""
        with actors.acting_as(Actor.GRANTED):
            first = await _processor(harness).run(_put(project, "ops"))
            second = await _processor(harness).run(_put(project, "infra"))

        assert second.data.id == first.data.id
        assert await _labels(ops_db, project) == [(_KEY, "infra")]

    @_MISSING_OWNER_IS_WRITTEN
    async def test_a_missing_owner_is_not_found_for_a_superadmin(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-4."""
        missing = uuid.uuid4()

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(NotFoundError):
                await _processor(harness).run(_put(missing))

        assert await _labels(ops_db, missing) == []

    async def test_a_missing_owner_is_a_denial_for_a_user(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, project: ProjectID
    ) -> None:
        """target-5."""
        missing = uuid.uuid4()

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_put(missing))

        assert await _labels(ops_db, missing) == []


class TestRecord:
    @pytest.mark.parametrize(
        ("actor", "exists", "status"),
        [
            pytest.param(Actor.GRANTED, True, OperationStatus.SUCCESS, id="record-1"),
            pytest.param(Actor.UNGRANTED, True, OperationStatus.DENIED, id="record-2"),
            pytest.param(
                Actor.SUPERADMIN,
                False,
                OperationStatus.ERROR,
                id="record-3",
                marks=_MISSING_OWNER_IS_WRITTEN,
            ),
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
        project: ProjectID,
        actor: Actor,
        exists: bool,
        status: OperationStatus,
    ) -> None:
        """A write is recorded whatever the read policy says."""
        owner = project if exists else uuid.uuid4()

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_put(owner))

        records = await silent_reads_harness.audit(UpsertEntityLabelAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(_owner(owner)), ActionOperationType.UPDATE, status)
        ]

    async def test_a_failed_write_is_an_error_on_the_owner(
        self, silent_reads_harness: OpsHarness, actors: Actors, project: ProjectID
    ) -> None:
        """record-3: a key longer than its column."""
        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(Exception) as raised:
                await _processor(silent_reads_harness).run(_put(project, key="k" * 300))

        records = await silent_reads_harness.audit(UpsertEntityLabelAction.action_name())
        assert [((r.entity_type, r.entity_id), r.status, r.description) for r in records] == [
            (entity_key(_owner(project)), OperationStatus.ERROR, str(raised.value))
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
                await _processor(harness).run(_put(project))

        records = await harness.audit(UpsertEntityLabelAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _labels(ops_db, project) == []


class TestResult:
    async def test_the_data_is_the_row_written(
        self, harness: OpsHarness, actors: Actors, project: ProjectID
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_put(project, "infra"))

        assert (result.data.entity, result.data.key, result.data.value) == (
            _owner(project),
            _KEY,
            "infra",
        )
