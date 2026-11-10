"""``global_create_with_fields_ops``: a global entity and its field rows in one
transaction, with the deployment preset and its slot quantities as the representative."""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator, Sequence
from decimal import Decimal
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetEntityType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.deployment_revision_preset.types import ResourceSlotEntryData
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import DeploymentRevisionPresetConflict
from ai.backend.manager.models.deployment_revision_preset.creators import (
    DeploymentPresetCreator,
    PresetResourceSlotCreator,
)
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow, ResourceSlotTypeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.deployment_revision_preset.actions.create import (
    CreateDeploymentPresetAction,
)
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    grant,
)

_RUNTIME_VARIANT = RuntimeVariantID(uuid.uuid4())
_SLOTS = (("cpu", "2"), ("mem", "1024"))


async def _grant_global(
    db: ExtendedAsyncSAEngine, user_id: UserID, entity_type: EntityType, permission: Permission
) -> None:
    scope = global_entity_id(GlobalEntityName.GLOBAL)
    await grant(db, user_id, scope.entity_type(), scope, entity_type, permission)


@pytest.fixture
async def preset_db(ops_db: ExtendedAsyncSAEngine) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(ops_db, [ResourceSlotTypeRow, PresetResourceSlotRow]):
        async with ops_db.begin_session() as sess:
            sess.add_all([
                ResourceSlotTypeRow(slot_name=name, slot_type="count", display_name=name, rank=i)
                for i, (name, _) in enumerate(_SLOTS)
            ])
            await sess.commit()
        yield ops_db


@pytest.fixture
async def granted(preset_db: ExtendedAsyncSAEngine, actors: Actors) -> None:
    for actor, permission in (
        (Actor.GRANTED, Permission.CREATE),
        (Actor.READ_ONLY, Permission.READ),
    ):
        await _grant_global(
            preset_db, actors.user_id(actor), DeploymentPresetEntityType(), permission
        )


async def _presets(db: ExtendedAsyncSAEngine, name: str) -> list[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        return list(
            (
                await sess.scalars(
                    sa.select(DeploymentRevisionPresetRow.id).where(
                        DeploymentRevisionPresetRow.name == name
                    )
                )
            ).all()
        )


async def _slot_rows(db: ExtendedAsyncSAEngine) -> list[tuple[str, Decimal]]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.execute(
            sa.select(PresetResourceSlotRow.slot_name, PresetResourceSlotRow.quantity)
        )
    return sorted((name, quantity) for name, quantity in rows.all())


def _processor(harness: OpsHarness) -> Any:
    return harness.group(DeploymentPresetEntityType()).global_create_with_fields_ops(
        CreateDeploymentPresetAction
    )


def _create(name: str, slots: Sequence[tuple[str, str]] = _SLOTS) -> CreateDeploymentPresetAction:
    return CreateDeploymentPresetAction(
        creator=DeploymentPresetCreator(
            runtime_variant_id=_RUNTIME_VARIANT,
            name=name,
            description=None,
            image_id=ImageID(uuid.uuid4()),
            model_definition=None,
            resource_opts=[],
            cluster_mode="single-node",
            cluster_size=1,
            startup_command=None,
            bootstrap_script=None,
            environ={},
            runtime_variant_preset_values=[],
            replica_count=1,
            deployment_strategy=DeploymentStrategy.ROLLING,
            deployment_strategy_spec={},
        ),
        slot_creators=[
            PresetResourceSlotCreator(
                entry=ResourceSlotEntryData(resource_type=slot, quantity=quantity)
            )
            for slot, quantity in slots
        ],
    )


def _new_name() -> str:
    return f"preset-{uuid.uuid4().hex[:8]}"


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
        preset_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        granted: None,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)
        name = _new_name()

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(_create(name))
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_create(name))
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert len(await _presets(preset_db, name)) == (0 if error else 1)
        assert len(await _slot_rows(preset_db)) == (0 if error else len(_SLOTS))

    @pytest.mark.parametrize(
        ("at_global", "entity_type"),
        [
            pytest.param(False, DeploymentPresetEntityType(), id="actor-5"),
            pytest.param(True, ProjectEntityType(), id="actor-6"),
        ],
    )
    async def test_a_grant_off_the_global_type_is_refused(
        self,
        preset_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        at_global: bool,
        entity_type: EntityType,
    ) -> None:
        """A domain grant on the type, or a global grant on another type, is not enough."""
        user_id = actors.user_id(Actor.UNGRANTED)
        if at_global:
            await _grant_global(preset_db, user_id, entity_type, Permission.full())
        else:
            await grant(
                preset_db,
                user_id,
                DomainEntityType(),
                actors.domain_id,
                entity_type,
                Permission.full(),
            )
        name = _new_name()

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(InsufficientPrivilege):
                await _processor(harness).run(_create(name))

        assert await _presets(preset_db, name) == []


class TestTarget:
    async def test_a_new_key_creates_the_entity_and_its_fields(
        self, preset_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """target-1."""
        name = _new_name()

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_create(name))

        assert len(await _presets(preset_db, name)) == 1
        assert await _slot_rows(preset_db) == [("cpu", Decimal(2)), ("mem", Decimal(1024))]

    async def test_a_taken_key_leaves_nothing(
        self, preset_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """target-2: the creator declares its own error for the name."""
        name = _new_name()
        with actors.acting_as(Actor.SUPERADMIN):
            first = await _processor(harness).run(_create(name, slots=[]))

            with pytest.raises(DeploymentRevisionPresetConflict):
                await _processor(harness).run(_create(name))

        assert await _presets(preset_db, name) == [first.data.id]
        assert await _slot_rows(preset_db) == []


class TestMulti:
    async def test_a_failing_field_row_takes_the_entity_down(
        self, preset_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """multi-1: two slot rows share a key."""
        name = _new_name()

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(UniqueConstraintViolationError):
                await _processor(harness).run(_create(name, slots=[("cpu", "1"), ("cpu", "2")]))

        assert await _presets(preset_db, name) == []
        assert await _slot_rows(preset_db) == []

    async def test_no_field_rows_creates_the_entity_alone(
        self, preset_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """multi-2."""
        name = _new_name()

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_create(name, slots=[]))

        assert await _presets(preset_db, name) == [result.data.id]
        assert result.fields == []


class TestRecord:
    @pytest.mark.parametrize(
        ("actor", "taken", "status"),
        [
            pytest.param(Actor.GRANTED, False, OperationStatus.SUCCESS, id="record-1"),
            pytest.param(Actor.UNGRANTED, False, OperationStatus.DENIED, id="record-2"),
            pytest.param(Actor.GRANTED, True, OperationStatus.ERROR, id="record-3"),
            pytest.param(
                Actor.ANONYMOUS,
                False,
                OperationStatus.DENIED,
                id="record-4",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_one_row_with_no_target(
        self,
        preset_db: ExtendedAsyncSAEngine,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        granted: None,
        actor: Actor,
        taken: bool,
        status: OperationStatus,
    ) -> None:
        """A write is recorded whatever the read policy says."""
        name = _new_name()
        if taken:
            async with preset_db.begin_session() as sess:
                sess.add(_create(name).creator.build_row())
                await sess.commit()

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_create(name))

        records = await silent_reads_harness.audit(CreateDeploymentPresetAction.action_name())
        assert [(r.entity_type, r.entity_id, r.operation, r.status) for r in records] == [
            (str(GlobalEntityType()), None, ActionOperationType.CREATE, status)
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        preset_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        granted: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "governed_permissions", broken)
        name = _new_name()

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_create(name))

        records = await harness.audit(CreateDeploymentPresetAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _presets(preset_db, name) == []


class TestResult:
    async def test_the_data_and_every_field_row(
        self, preset_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """result-1."""
        name = _new_name()

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_create(name))

        assert await _presets(preset_db, name) == [result.data.id]
        assert result.data.name == name
        assert sorted((f.resource_type, Decimal(f.quantity)) for f in result.fields) == [
            ("cpu", Decimal(2)),
            ("mem", Decimal(1024)),
        ]
