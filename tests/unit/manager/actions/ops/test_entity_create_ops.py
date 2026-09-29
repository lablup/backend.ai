"""``entity_create_ops``: creating one entity in a parent scope, with the role as the
representative.

The role creator declares no unique key, so target-2 runs on a test action carrying the
resource preset creator, which declares one. target-3 does not apply: the shape's action
returns an ``EntityCreator``, whose ``precondition_checks`` is final and empty. record-2
does not apply: a create always yields its entity.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import pytest
import sqlalchemy as sa
from aiohttp import web

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.permission.types import Permission, RoleSource
from ai.backend.common.exception import BackendAIError, ResourcePresetConflict
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.ops.base import CreateEntityOpsAction
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.permission import NotEnoughPermission, VirtualEntityNotFound
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.rbac_models.role.creators import RoleCreator
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.resource_preset.creators import ResourcePresetCreator
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.permission_contoller.actions.create_role import CreateRoleAction
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
)

_MISSING_PARENT_IS_A_SERVER_ERROR = pytest.mark.xfail(
    strict=True,
    raises=VirtualEntityNotFound,
    reason="a parent scope with no node raises VirtualEntityNotFound (500), not a 404",
)

_NAME = "created-role"


@pytest.fixture
async def parent(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> DomainID:
    for actor, entity_type in (
        (Actor.GRANTED, RoleEntityType()),
        (Actor.READ_ONLY, UserEntityType()),
    ):
        await grant(
            ops_db,
            actors.user_id(actor),
            DomainEntityType(),
            actors.domain_id,
            entity_type,
            Permission.CREATE,
        )
    return actors.domain_id


def _action(scope: DomainID) -> CreateRoleAction:
    return CreateRoleAction(creator=RoleCreator(name=_NAME, scope=scope))


def _processor(harness: OpsHarness) -> Any:
    return harness.group(RoleEntityType()).entity_create_ops(CreateRoleAction)


async def _created(db: ExtendedAsyncSAEngine) -> list[RoleID]:
    async with db.begin_readonly_session() as sess:
        return list((await sess.scalars(sa.select(RoleRow.id).where(RoleRow.name == _NAME))).all())


async def _has_node(db: ExtendedAsyncSAEngine, role_id: RoleID) -> bool:
    async with db.begin_readonly_session() as sess:
        found = await sess.scalar(
            sa.select(VirtualEntityRow.id).where(
                VirtualEntityRow.entity_type == RoleEntityType(),
                VirtualEntityRow.entity_id == role_id,
            )
        )
    return found is not None


async def _in_scope(db: ExtendedAsyncSAEngine, scope: DomainID, role_id: RoleID) -> bool:
    async with db.begin_readonly_session() as sess:
        return bool(
            await sess.scalar(
                sa.select(
                    scope_membership_exists(DomainEntityType(), scope, RoleEntityType(), role_id)
                )
            )
        )


async def _seed_domain_outside_the_graph(db: ExtendedAsyncSAEngine) -> DomainID:
    domain_id = DomainID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            DomainRow(
                id=domain_id,
                name=DomainName(f"outside-{domain_id.hex[:8]}"),
                total_resource_slots=ResourceSlot(),
            )
        )
        await sess.commit()
    return domain_id


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
        parent: DomainID,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(_action(parent))
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_action(parent))
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert len(await _created(ops_db)) == (1 if error is None else 0)


class TestTarget:
    async def test_the_row_its_node_and_its_parent(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, parent: DomainID
    ) -> None:
        """target-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_action(parent))

        assert await _created(ops_db) == [result.data.id]
        assert await _has_node(ops_db, result.data.id)
        assert await _in_scope(ops_db, parent, result.data.id)

    async def test_a_user_naming_a_missing_parent_is_refused(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, parent: DomainID
    ) -> None:
        """target-4."""
        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_action(DomainID(uuid.uuid4())))

        assert await _created(ops_db) == []

    @_MISSING_PARENT_IS_A_SERVER_ERROR
    @pytest.mark.parametrize("in_db", [False, True], ids=["no-row", "no-node"])
    async def test_a_superadmin_naming_a_missing_parent(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        parent: DomainID,
        in_db: bool,
    ) -> None:
        """target-5."""
        missing = await _seed_domain_outside_the_graph(ops_db) if in_db else DomainID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(web.HTTPNotFound):
                await _processor(harness).run(_action(missing))

        assert await _created(ops_db) == []


@dataclass(frozen=True)
class _CreatePresetAction(CreateEntityOpsAction[ResourcePresetRow, ResourcePresetData]):
    """A test action of this shape carrying a creator that declares a domain conflict."""

    creator: ResourcePresetCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ResourcePresetEntityType()

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (global_entity_id(GlobalEntityName.GLOBAL),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "test_create_resource_preset"

    @override
    def to_creator(self) -> ResourcePresetCreator:
        return self.creator


async def _preset_state(db: ExtendedAsyncSAEngine) -> tuple[int, int]:
    """How many preset rows and preset nodes there are."""
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalar(sa.select(sa.func.count()).select_from(ResourcePresetRow))
        nodes = await sess.scalar(
            sa.select(sa.func.count())
            .select_from(VirtualEntityRow)
            .where(VirtualEntityRow.entity_type == ResourcePresetEntityType())
        )
    return (rows or 0, nodes or 0)


class TestUniqueKey:
    async def test_a_taken_unique_key_raises_the_declared_error(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-2: the preset name is taken."""
        action = _CreatePresetAction(
            creator=ResourcePresetCreator(
                name="taken",
                resource_slots=ResourceSlot(),
                shared_memory=None,
                resource_group_name=None,
            )
        )
        processor = harness.group(ResourcePresetEntityType()).entity_create_ops(_CreatePresetAction)
        with actors.acting_as(Actor.SUPERADMIN):
            await processor.run(action)

            with pytest.raises(ResourcePresetConflict):
                await processor.run(action)

        assert await _preset_state(ops_db) == (1, 1)


class TestRecord:
    async def test_one_row_on_the_new_entity(
        self, silent_reads_harness: OpsHarness, actors: Actors, parent: DomainID
    ) -> None:
        """record-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(silent_reads_harness).run(_action(parent))

        records = await silent_reads_harness.audit(CreateRoleAction.action_name())
        assert [
            ((r.entity_type, r.entity_id), r.operation, r.status, r.scopes) for r in records
        ] == [
            (
                entity_key(result.data.id),
                ActionOperationType.CREATE,
                OperationStatus.SUCCESS,
                frozenset([entity_key(parent)]),
            )
        ]

    @pytest.mark.parametrize(
        ("actor", "missing", "status"),
        [
            pytest.param(Actor.UNGRANTED, False, OperationStatus.DENIED, id="record-3"),
            pytest.param(Actor.SUPERADMIN, True, OperationStatus.ERROR, id="record-4"),
            pytest.param(
                Actor.ANONYMOUS,
                False,
                OperationStatus.DENIED,
                id="record-5",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_a_failed_run_leaves_one_row(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        parent: DomainID,
        actor: Actor,
        missing: bool,
        status: OperationStatus,
    ) -> None:
        """record-4 fails in the run: the parent has no node."""
        scope = DomainID(uuid.uuid4()) if missing else parent

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_action(scope))

        records = await silent_reads_harness.audit(CreateRoleAction.action_name())
        assert [(r.entity_type, r.entity_id, r.operation, r.status, r.scopes) for r in records] == [
            (
                str(RoleEntityType()),
                None,
                ActionOperationType.CREATE,
                status,
                frozenset([entity_key(scope)]),
            )
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        parent: DomainID,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-6."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "checked_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_action(parent))

        records = await harness.audit(CreateRoleAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _created(ops_db) == []


class TestResult:
    async def test_the_data_is_the_new_entity(
        self, harness: OpsHarness, actors: Actors, parent: DomainID
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_action(parent))

        assert result.data.name == _NAME
        assert result.data.source is RoleSource.CUSTOM
        assert (result.data.scope_type, result.data.scope_id) == (DomainEntityType(), parent)
