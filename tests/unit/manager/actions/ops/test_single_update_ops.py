"""``single_update_ops``: editing one entity, with the domain as the representative.

target-4 runs a test action of this shape carrying the project soft-delete updater,
the spec that declares two guards.
"""

from __future__ import annotations

import contextlib
import uuid
from dataclasses import dataclass
from typing import Any, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.domain.types import DomainStatus
from ai.backend.manager.data.project.types import ProjectData, ProjectStatus, ProjectType
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import DomainPurgeInProgress, ProjectPurgeInProgress
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.updaters import DomainUpdater
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.project.updaters import ProjectSoftDeleteUpdater
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.domain.actions.update_domain import UpdateDomainAction
from ai.backend.manager.types import OptionalState, TriState
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
    provision,
    seed_project,
)


@dataclass(frozen=True)
class _TwoGuardAction(UpdateSingleEntityOpsAction[ProjectRow, ProjectData]):
    """This shape carrying an updater that declares two guards."""

    updater: ProjectSoftDeleteUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.project_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "two_guard_update"

    @override
    def to_updater(self) -> ProjectSoftDeleteUpdater:
        return self.updater


_GUARD_SKIPS_EMPTY_UPDATE = pytest.mark.xfail(
    strict=True, reason="an update with no values returns the row without evaluating the guards"
)


async def _seed_domain(db: ExtendedAsyncSAEngine, status: DomainStatus) -> DomainID:
    domain_id = DomainID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            DomainRow(
                id=domain_id,
                name=DomainName(f"target-{domain_id.hex[:8]}"),
                total_resource_slots=ResourceSlot(),
                status=status,
            )
        )
        await sess.commit()
    await provision(db, DomainEntityType(), domain_id)
    return domain_id


@pytest.fixture
async def domain(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> DomainID:
    domain_id = await _seed_domain(ops_db, DomainStatus.ACTIVE)
    for actor, permission in (
        (Actor.GRANTED, Permission.UPDATE),
        (Actor.READ_ONLY, Permission.READ),
    ):
        await grant(
            ops_db,
            actors.user_id(actor),
            DomainEntityType(),
            domain_id,
            DomainEntityType(),
            permission,
        )
    return domain_id


@pytest.fixture
async def purging_domain(ops_db: ExtendedAsyncSAEngine) -> DomainID:
    return await _seed_domain(ops_db, DomainStatus.PURGING)


async def _description(db: ExtendedAsyncSAEngine, domain_id: DomainID) -> str | None:
    async with db.begin_readonly_session() as sess:
        return await sess.scalar(sa.select(DomainRow.description).where(DomainRow.id == domain_id))


def _processor(harness: OpsHarness) -> Any:
    return harness.group(DomainEntityType()).single_update_ops(UpdateDomainAction)


def _describe(domain_id: DomainID, description: str = "edited") -> UpdateDomainAction:
    return UpdateDomainAction(
        updater=DomainUpdater(domain_id=domain_id, description=TriState.update(description))
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
        domain: DomainID,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(_describe(domain))
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_describe(domain))
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert await _description(ops_db, domain) == (None if error else "edited")


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
        domain: DomainID,
        actor: Actor,
        error: type[Exception],
    ) -> None:
        with actors.acting_as(actor):
            with pytest.raises(error):
                await _processor(harness).run(_describe(DomainID(uuid.uuid4())))

    async def test_a_failing_guard_leaves_the_row(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        purging_domain: DomainID,
    ) -> None:
        """target-3."""
        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(DomainPurgeInProgress):
                await _processor(harness).run(_describe(purging_domain))

        assert await _description(ops_db, purging_domain) is None

    async def test_the_first_failing_guard_answers(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-4: a personal project being purged fails both guards."""
        both = await seed_project(
            ops_db, actors, project_type=ProjectType.PERSONAL, status=ProjectStatus.PURGING
        )
        processor = harness.group(ProjectEntityType()).single_update_ops(_TwoGuardAction)
        action = _TwoGuardAction(updater=ProjectSoftDeleteUpdater(project_id=both))

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(ProjectPurgeInProgress):
                await processor.run(action)

        assert await project_status(ops_db, both) == ProjectStatus.PURGING

    @_GUARD_SKIPS_EMPTY_UPDATE
    async def test_an_empty_update_still_evaluates_the_guard(
        self, harness: OpsHarness, actors: Actors, purging_domain: DomainID
    ) -> None:
        """target-5."""
        action = UpdateDomainAction(updater=DomainUpdater(domain_id=purging_domain))

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(DomainPurgeInProgress):
                await _processor(harness).run(action)

    async def test_an_empty_update_passing_the_guard_returns_the_row(
        self, harness: OpsHarness, actors: Actors, domain: DomainID
    ) -> None:
        """target-6."""
        action = UpdateDomainAction(updater=DomainUpdater(domain_id=domain))

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(action)

        assert result.data.id == domain

    async def test_a_value_colliding_with_another_row_leaves_the_row(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, domain: DomainID
    ) -> None:
        """target-7."""
        action = UpdateDomainAction(
            updater=DomainUpdater(
                domain_id=domain, new_name=OptionalState.update(actors.domain_name)
            )
        )

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(UniqueConstraintViolationError):
                await _processor(harness).run(action)

        async with ops_db.begin_readonly_session() as sess:
            name = await sess.scalar(sa.select(DomainRow.name).where(DomainRow.id == domain))
        assert name == f"target-{domain.hex[:8]}"


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
        domain: DomainID,
        actor: Actor,
        exists: bool,
        status: OperationStatus,
    ) -> None:
        """A write is recorded whatever the read policy says."""
        target = domain if exists else DomainID(uuid.uuid4())

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_describe(target))

        records = await silent_reads_harness.audit(UpdateDomainAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(target), ActionOperationType.UPDATE, status)
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        domain: DomainID,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_describe(domain))

        records = await harness.audit(UpdateDomainAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _description(ops_db, domain) is None


class TestResult:
    async def test_the_data_is_the_row_after_the_write(
        self, harness: OpsHarness, actors: Actors, domain: DomainID
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_describe(domain, "after"))

        assert result.data.id == domain
        assert result.data.description == "after"
