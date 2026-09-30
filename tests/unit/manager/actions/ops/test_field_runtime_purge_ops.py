"""``runtime_purge_ops (field)``: removing one field row whose owner's type is a value on
the row, with an entity label as the representative.

target-4 and target-5 are not applicable: labels are the only field rows whose owner's
type is a value on the row, the runtime owner lookup reads the label table alone, and the
label purger declares no guard.
"""

from __future__ import annotations

import contextlib
import uuid
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.entity_label import (
    EntityLabelFieldType,
    EntityLabelID,
    EntityLabelKey,
)
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.entity_label.actions.lookup_owner import (
    LookupBulkEntityLabelOwnerAction,
    LookupEntityLabelOwnerAction,
)
from ai.backend.manager.services.entity_label.actions.purge import PurgeEntityLabelAction
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
    seed_project,
)

_OWNER_LOOKUP = LookupEntityLabelOwnerAction.action_name()
_OPERATION = PurgeEntityLabelAction.action_name()


async def _seed_label(
    db: ExtendedAsyncSAEngine, entity_type: EntityType, entity_id: uuid.UUID
) -> EntityLabelID:
    async with db.begin_session() as sess:
        row = EntityLabelRow(
            entity_type=entity_type,
            entity_id=entity_id,
            key=EntityLabelKey("team"),
            value="ops",
        )
        sess.add(row)
        await sess.flush()
        label_id = row.id
        await sess.commit()
    return label_id


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


@pytest.fixture
async def label(ops_db: ExtendedAsyncSAEngine, project: ProjectID) -> EntityLabelID:
    return await _seed_label(ops_db, ProjectEntityType(), project)


async def _label_exists(db: ExtendedAsyncSAEngine, label_id: EntityLabelID) -> bool:
    async with db.begin_readonly_session() as sess:
        found = await sess.scalar(sa.select(EntityLabelRow.id).where(EntityLabelRow.id == label_id))
    return found is not None


def _processor(harness: OpsHarness) -> Any:
    labels = harness.registry.dangling_lookup_field_group(
        FieldGroupMeta(EntityLabelFieldType()),
        EntityLabelData,
        LookupEntityLabelOwnerAction,
        LookupBulkEntityLabelOwnerAction,
    )
    return labels.runtime_purge_ops(PurgeEntityLabelAction)


def _project_key(project_id: ProjectID) -> tuple[str, str]:
    return entity_key(RuntimeEntityID(ProjectEntityType(), project_id))


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
        label: EntityLabelID,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(PurgeEntityLabelAction(label_id=label))
            else:
                with pytest.raises(error):
                    await _processor(harness).run(PurgeEntityLabelAction(label_id=label))

        assert await _label_exists(ops_db, label) == (error is not None)

    @ANONYMOUS_NOT_REFUSED
    async def test_a_caller_with_no_user_is_refused(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        label: EntityLabelID,
    ) -> None:
        """actor-1."""
        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(PurgeEntityLabelAction(label_id=label))

        assert await _label_exists(ops_db, label)
        assert_refused(raised.value)

    @MONITOR_READ_REFUSED
    async def test_a_monitor_passes_the_lookup_and_is_denied_the_write(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        project: ProjectID,
        label: EntityLabelID,
    ) -> None:
        """actor-6."""
        with actors.acting_as(Actor.MONITOR):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(PurgeEntityLabelAction(label_id=label))

        assert await _label_exists(ops_db, label)
        assert _rows(await harness.audit(_OWNER_LOOKUP)) == [
            (_project_key(project), ActionOperationType.LOOKUP, OperationStatus.SUCCESS)
        ]
        assert _rows(await harness.audit(_OPERATION)) == [
            (_project_key(project), ActionOperationType.UPDATE, OperationStatus.DENIED)
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
        project: ProjectID,
        actor: Actor,
        error: type[Exception],
    ) -> None:
        with actors.acting_as(actor):
            with pytest.raises(error):
                await _processor(harness).run(
                    PurgeEntityLabelAction(label_id=EntityLabelID(uuid.uuid4()))
                )

    @pytest.mark.parametrize(
        "exists", [pytest.param(False, id="missing"), pytest.param(True, id="denied")]
    )
    async def test_the_refusal_names_neither_the_row_nor_its_owner(
        self,
        harness: OpsHarness,
        actors: Actors,
        project: ProjectID,
        label: EntityLabelID,
        exists: bool,
    ) -> None:
        """target-3."""
        target = label if exists else EntityLabelID(uuid.uuid4())

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(GenericBadRequest) as caught:
                await _processor(harness).run(PurgeEntityLabelAction(label_id=target))

        assert str(target) not in str(caught.value)
        assert str(project) not in str(caught.value)

    @FIELD_WRITE_NEEDS_OWNER_READ
    async def test_each_row_answers_to_its_own_owner(
        self,
        ops_db: ExtendedAsyncSAEngine,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        project: ProjectID,
        label: EntityLabelID,
    ) -> None:
        """target-6: the caller holds UPDATE on the project and READ on the domain."""
        on_domain = await _seed_label(ops_db, DomainEntityType(), actors.domain_id)
        await grant(
            ops_db,
            actors.user_id(Actor.UNGRANTED),
            ProjectEntityType(),
            project,
            ProjectEntityType(),
            Permission.UPDATE,
        )
        await grant(
            ops_db,
            actors.user_id(Actor.UNGRANTED),
            DomainEntityType(),
            actors.domain_id,
            DomainEntityType(),
            Permission.READ,
        )

        with actors.acting_as(Actor.UNGRANTED):
            await _processor(silent_reads_harness).run(PurgeEntityLabelAction(label_id=label))
            with pytest.raises(NotEnoughPermission):
                await _processor(silent_reads_harness).run(
                    PurgeEntityLabelAction(label_id=on_domain)
                )

        assert not await _label_exists(ops_db, label)
        assert await _label_exists(ops_db, on_domain)
        domain_key = entity_key(RuntimeEntityID(DomainEntityType(), actors.domain_id))
        assert set(_rows(await silent_reads_harness.audit(_OPERATION))) == {
            (_project_key(project), ActionOperationType.UPDATE, OperationStatus.SUCCESS),
            (domain_key, ActionOperationType.UPDATE, OperationStatus.DENIED),
        }

    async def test_each_row_is_recorded_on_its_own_owner(
        self,
        ops_db: ExtendedAsyncSAEngine,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        project: ProjectID,
        label: EntityLabelID,
    ) -> None:
        """target-6: the recording half, run by the superadmin."""
        on_domain = await _seed_label(ops_db, DomainEntityType(), actors.domain_id)

        with actors.acting_as(Actor.SUPERADMIN):
            await _processor(silent_reads_harness).run(PurgeEntityLabelAction(label_id=label))
            await _processor(silent_reads_harness).run(PurgeEntityLabelAction(label_id=on_domain))

        domain_key = entity_key(RuntimeEntityID(DomainEntityType(), actors.domain_id))
        assert set(_rows(await silent_reads_harness.audit(_OPERATION))) == {
            (_project_key(project), ActionOperationType.UPDATE, OperationStatus.SUCCESS),
            (domain_key, ActionOperationType.UPDATE, OperationStatus.SUCCESS),
        }

    async def test_the_row_goes_and_its_owner_stays(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        project: ProjectID,
        label: EntityLabelID,
    ) -> None:
        """target-7."""
        with actors.acting_as(Actor.SUPERADMIN):
            await _processor(harness).run(PurgeEntityLabelAction(label_id=label))

        assert not await _label_exists(ops_db, label)
        async with ops_db.begin_readonly_session() as sess:
            left = await sess.scalar(sa.select(ProjectRow.id).where(ProjectRow.id == project))
        assert left == project


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
        project: ProjectID,
        label: EntityLabelID,
        record_reads: bool,
    ) -> None:
        harness = OpsHarness(ops_db, record_reads=record_reads)

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(PurgeEntityLabelAction(label_id=label))

        lookup = (_project_key(project), ActionOperationType.LOOKUP, OperationStatus.SUCCESS)
        assert _rows(await harness.audit(_OWNER_LOOKUP)) == ([lookup] if record_reads else [])
        assert _rows(await harness.audit(_OPERATION)) == [
            (_project_key(project), ActionOperationType.UPDATE, OperationStatus.SUCCESS)
        ]

    async def test_a_denied_owner_lookup_leaves_no_operation_row(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        project: ProjectID,
        label: EntityLabelID,
    ) -> None:
        """record-2."""
        with actors.acting_as(Actor.UNGRANTED):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(PurgeEntityLabelAction(label_id=label))

        assert _rows(await silent_reads_harness.audit(_OWNER_LOOKUP)) == [
            (_project_key(project), ActionOperationType.LOOKUP, OperationStatus.DENIED)
        ]
        assert await silent_reads_harness.audit(_OPERATION) == []

    async def test_a_denied_operation_follows_a_passed_lookup(
        self, harness: OpsHarness, actors: Actors, project: ProjectID, label: EntityLabelID
    ) -> None:
        """record-3."""
        with actors.acting_as(Actor.READ_ONLY):
            with contextlib.suppress(Exception):
                await _processor(harness).run(PurgeEntityLabelAction(label_id=label))

        assert _rows(await harness.audit(_OWNER_LOOKUP)) == [
            (_project_key(project), ActionOperationType.LOOKUP, OperationStatus.SUCCESS)
        ]
        assert _rows(await harness.audit(_OPERATION)) == [
            (_project_key(project), ActionOperationType.UPDATE, OperationStatus.DENIED)
        ]

    async def test_a_missing_row_is_a_lookup_error_by_its_key(
        self, harness: OpsHarness, actors: Actors, project: ProjectID
    ) -> None:
        """record-4."""
        missing = EntityLabelID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            with contextlib.suppress(Exception):
                await _processor(harness).run(PurgeEntityLabelAction(label_id=missing))

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
        label: EntityLabelID,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(PurgeEntityLabelAction(label_id=label))

        assert [r.status for r in await harness.audit(_OWNER_LOOKUP)] == [OperationStatus.ERROR]
        assert await harness.audit(_OPERATION) == []
        assert await _label_exists(ops_db, label)


class TestResult:
    async def test_the_data_is_the_row_before_the_purge(
        self, harness: OpsHarness, actors: Actors, project: ProjectID, label: EntityLabelID
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(PurgeEntityLabelAction(label_id=label))

        assert (result.data.id, result.data.entity, result.data.key, result.data.value) == (
            label,
            RuntimeEntityID(ProjectEntityType(), project),
            "team",
            "ops",
        )
