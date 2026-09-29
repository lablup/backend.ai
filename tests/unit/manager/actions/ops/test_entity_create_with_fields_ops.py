"""``entity_create_with_fields_ops``: creating an entity and its field rows in a parent
scope, with the model card and its minimum resources as the representative.

target-3 does not apply: the shape's action returns an ``EntityCreator``, whose
``precondition_checks`` is final and empty. record-2 does not apply: a create always
yields its entity.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any

import pytest
import sqlalchemy as sa
from aiohttp import web

from ai.backend.common.data.entity.model_card import ModelCardEntityType, ModelCardID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    ResourceSlot,
    VFolderHostPermissionMap,
    VFolderMountPolicy,
    VFolderUsageMode,
)
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.model_card.types import ResourceRequirementEntry
from ai.backend.manager.data.project.types import ProjectStatus, ProjectType
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus, VFolderOwnershipType
from ai.backend.manager.errors.permission import NotEnoughPermission, VirtualEntityNotFound
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.errors.resource import ModelCardConflict
from ai.backend.manager.models.model_card.creators import ModelCardCreator
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.models.resource_slot.row import (
    ModelCardResourceRequirementRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.model_card.actions.create import CreateModelCardAction
from ai.backend.testutils.db import with_tables
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

_MISSING_PARENT_IS_NOT_A_404 = pytest.mark.xfail(
    strict=True,
    raises=(VirtualEntityNotFound, ForeignKeyViolationError),
    reason="a parent missing from the DB or the graph fails on the FK or the node lookup, not a 404",
)

_NAME = "created-card"
_ENTRIES = (
    ResourceRequirementEntry(slot_name="cpu", min_quantity="2"),
    ResourceRequirementEntry(slot_name="mem", min_quantity="4"),
)


@pytest.fixture
async def card_db(ops_db: ExtendedAsyncSAEngine) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(ops_db, [ResourceSlotTypeRow, ModelCardResourceRequirementRow]):
        async with ops_db.begin_session() as sess:
            sess.add_all([
                ResourceSlotTypeRow(slot_name="cpu", slot_type="count", rank=0),
                ResourceSlotTypeRow(slot_name="mem", slot_type="bytes", rank=1),
            ])
            await sess.commit()
        yield ops_db


@dataclass(frozen=True)
class _Parent:
    project_id: ProjectID
    vfolder_id: VFolderUUID


async def _seed_vfolder(
    db: ExtendedAsyncSAEngine, actors: Actors, project_id: ProjectID
) -> VFolderUUID:
    vfolder_id = VFolderUUID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            VFolderRow(
                id=vfolder_id,
                name=f"vfolder-{vfolder_id.hex[:8]}",
                host="local:volume1",
                domain_name=actors.domain_name,
                quota_scope_id=QuotaScopeID(QuotaScopeType.PROJECT, project_id),
                usage_mode=VFolderUsageMode.MODEL,
                default_mount_permission=VFolderMountPolicy.READ_WRITE,
                max_files=0,
                max_size=None,
                num_files=0,
                cur_size=0,
                creator="creator@test.com",
                unmanaged_path=None,
                ownership_type=VFolderOwnershipType.GROUP,
                user=None,
                group=project_id,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )
        )
        await sess.commit()
    return vfolder_id


async def _seed_project_outside_the_graph(db: ExtendedAsyncSAEngine, actors: Actors) -> ProjectID:
    project_id = ProjectID(uuid.uuid4())
    policy = f"project-policy-{project_id.hex[:8]}"
    async with db.begin_session() as sess:
        sess.add(
            ProjectResourcePolicyRow(
                name=policy, max_vfolder_count=0, max_quota_scope_size=-1, max_network_count=0
            )
        )
        await sess.flush()
        sess.add(
            ProjectRow(
                id=project_id,
                name=f"outside-{project_id.hex[:8]}",
                description=None,
                is_active=True,
                status=ProjectStatus.ACTIVE,
                domain_name=actors.domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                integration_id=None,
                resource_policy=policy,
                type=ProjectType.MODEL_STORE,
            )
        )
        await sess.commit()
    return project_id


@pytest.fixture
async def parent(card_db: ExtendedAsyncSAEngine, actors: Actors) -> _Parent:
    project_id = await seed_project(card_db, actors, project_type=ProjectType.MODEL_STORE)
    vfolder_id = await _seed_vfolder(card_db, actors, project_id)
    for actor, entity_type in (
        (Actor.GRANTED, ModelCardEntityType()),
        (Actor.READ_ONLY, UserEntityType()),
    ):
        await grant(
            card_db,
            actors.user_id(actor),
            ProjectEntityType(),
            project_id,
            entity_type,
            Permission.CREATE,
        )
    return _Parent(project_id=project_id, vfolder_id=vfolder_id)


def _action(
    actors: Actors,
    project_id: ProjectID,
    vfolder_id: VFolderUUID,
    entries: Sequence[ResourceRequirementEntry] = _ENTRIES,
) -> CreateModelCardAction:
    return CreateModelCardAction(
        creator=ModelCardCreator(
            name=_NAME,
            vfolder_id=vfolder_id,
            domain=actors.domain_name,
            project_id=project_id,
            creator_id=actors.user_id(Actor.SUPERADMIN),
            author=None,
            title=None,
            model_version=None,
            description=None,
            task=None,
            category=None,
            architecture=None,
            framework=[],
            label=[],
            license=None,
            readme=None,
            access_level="internal",
        ),
        min_resource=list(entries),
    )


def _processor(harness: OpsHarness) -> Any:
    return harness.group(ModelCardEntityType()).entity_create_with_fields_ops(CreateModelCardAction)


async def _cards(db: ExtendedAsyncSAEngine) -> list[ModelCardID]:
    async with db.begin_readonly_session() as sess:
        return list(
            (await sess.scalars(sa.select(ModelCardRow.id).where(ModelCardRow.name == _NAME))).all()
        )


async def _requirement_count(db: ExtendedAsyncSAEngine) -> int:
    async with db.begin_readonly_session() as sess:
        count = await sess.scalar(
            sa.select(sa.func.count()).select_from(ModelCardResourceRequirementRow)
        )
    return count or 0


async def _card_nodes(db: ExtendedAsyncSAEngine) -> int:
    async with db.begin_readonly_session() as sess:
        count = await sess.scalar(
            sa.select(sa.func.count())
            .select_from(VirtualEntityRow)
            .where(VirtualEntityRow.entity_type == ModelCardEntityType())
        )
    return count or 0


async def _in_scope(db: ExtendedAsyncSAEngine, project_id: ProjectID, card_id: ModelCardID) -> bool:
    async with db.begin_readonly_session() as sess:
        return bool(
            await sess.scalar(
                sa.select(
                    scope_membership_exists(
                        ProjectEntityType(), project_id, ModelCardEntityType(), card_id
                    )
                )
            )
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
        card_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        parent: _Parent,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)
        action = _action(actors, parent.project_id, parent.vfolder_id)

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(action)
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(action)
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert len(await _cards(card_db)) == (1 if error is None else 0)
        assert await _requirement_count(card_db) == (len(_ENTRIES) if error is None else 0)


class TestTarget:
    async def test_the_row_its_node_and_its_parent(
        self, card_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, parent: _Parent
    ) -> None:
        """target-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _action(actors, parent.project_id, parent.vfolder_id)
            )

        assert await _cards(card_db) == [result.data.id]
        assert await _card_nodes(card_db) == 1
        assert await _in_scope(card_db, parent.project_id, result.data.id)

    async def test_a_taken_unique_key_is_refused(
        self, card_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, parent: _Parent
    ) -> None:
        """target-2: name, domain and project are taken."""
        action = _action(actors, parent.project_id, parent.vfolder_id)
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(action)

            with pytest.raises(ModelCardConflict):
                await _processor(harness).run(action)

        assert len(await _cards(card_db)) == 1
        assert await _card_nodes(card_db) == 1
        assert await _requirement_count(card_db) == len(_ENTRIES)

    async def test_a_user_naming_a_missing_parent_is_refused(
        self, card_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, parent: _Parent
    ) -> None:
        """target-4."""
        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(
                    _action(actors, ProjectID(uuid.uuid4()), parent.vfolder_id)
                )

        assert await _cards(card_db) == []
        assert await _requirement_count(card_db) == 0
        assert await _card_nodes(card_db) == 0

    @_MISSING_PARENT_IS_NOT_A_404
    @pytest.mark.parametrize("in_db", [False, True], ids=["no-row", "no-node"])
    async def test_a_superadmin_naming_a_missing_parent(
        self,
        card_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        parent: _Parent,
        in_db: bool,
    ) -> None:
        """target-5."""
        missing = (
            await _seed_project_outside_the_graph(card_db, actors)
            if in_db
            else ProjectID(uuid.uuid4())
        )

        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(web.HTTPNotFound):
                await _processor(harness).run(_action(actors, missing, parent.vfolder_id))

        assert await _cards(card_db) == []
        assert await _card_nodes(card_db) == 0


class TestMulti:
    async def test_a_failing_field_row_takes_the_entity_with_it(
        self, card_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, parent: _Parent
    ) -> None:
        """multi-1: two rows name one slot."""
        entries = (*_ENTRIES, ResourceRequirementEntry(slot_name="cpu", min_quantity="8"))

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(UniqueConstraintViolationError):
                await _processor(harness).run(
                    _action(actors, parent.project_id, parent.vfolder_id, entries)
                )

        assert await _cards(card_db) == []
        assert await _card_nodes(card_db) == 0
        assert await _requirement_count(card_db) == 0

    async def test_no_field_rows(
        self, card_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, parent: _Parent
    ) -> None:
        """multi-2."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _action(actors, parent.project_id, parent.vfolder_id, ())
            )

        assert await _cards(card_db) == [result.data.id]
        assert result.fields == []
        assert await _requirement_count(card_db) == 0


class TestRecord:
    async def test_one_row_on_the_new_entity(
        self, silent_reads_harness: OpsHarness, actors: Actors, parent: _Parent
    ) -> None:
        """record-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(silent_reads_harness).run(
                _action(actors, parent.project_id, parent.vfolder_id)
            )

        records = await silent_reads_harness.audit(CreateModelCardAction.action_name())
        assert [
            ((r.entity_type, r.entity_id), r.operation, r.status, r.scopes) for r in records
        ] == [
            (
                entity_key(ModelCardID(result.data.id)),
                ActionOperationType.CREATE,
                OperationStatus.SUCCESS,
                frozenset([entity_key(parent.project_id)]),
            )
        ]

    @pytest.mark.parametrize(
        ("actor", "status"),
        [
            pytest.param(Actor.UNGRANTED, OperationStatus.DENIED, id="record-3"),
            pytest.param(
                Actor.ANONYMOUS,
                OperationStatus.DENIED,
                id="record-5",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_a_refused_run_leaves_one_row(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        parent: _Parent,
        actor: Actor,
        status: OperationStatus,
    ) -> None:
        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(
                    _action(actors, parent.project_id, parent.vfolder_id)
                )

        records = await silent_reads_harness.audit(CreateModelCardAction.action_name())
        assert [(r.entity_type, r.entity_id, r.operation, r.status, r.scopes) for r in records] == [
            (
                str(ModelCardEntityType()),
                None,
                ActionOperationType.CREATE,
                status,
                frozenset([entity_key(parent.project_id)]),
            )
        ]

    async def test_a_key_conflict_is_an_error(
        self, silent_reads_harness: OpsHarness, actors: Actors, parent: _Parent
    ) -> None:
        """record-4."""
        action = _action(actors, parent.project_id, parent.vfolder_id)
        with actors.acting_as(Actor.GRANTED):
            created = await _processor(silent_reads_harness).run(action)
            with contextlib.suppress(ModelCardConflict):
                await _processor(silent_reads_harness).run(action)

        records = await silent_reads_harness.audit(CreateModelCardAction.action_name())
        scopes = frozenset([entity_key(parent.project_id)])
        assert sorted(
            ((r.entity_type or "", r.entity_id or ""), r.operation, r.status, r.scopes)
            for r in records
        ) == sorted([
            (
                entity_key(ModelCardID(created.data.id)),
                ActionOperationType.CREATE,
                OperationStatus.SUCCESS,
                scopes,
            ),
            (
                (str(ModelCardEntityType()), ""),
                ActionOperationType.CREATE,
                OperationStatus.ERROR,
                scopes,
            ),
        ])

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        card_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        parent: _Parent,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-6."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "checked_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_action(actors, parent.project_id, parent.vfolder_id))

        records = await harness.audit(CreateModelCardAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _cards(card_db) == []


class TestResult:
    async def test_the_entity_and_every_field_row(
        self, harness: OpsHarness, actors: Actors, parent: _Parent
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _action(actors, parent.project_id, parent.vfolder_id)
            )

        assert result.data.name == _NAME
        assert result.data.project_id == parent.project_id
        assert sorted((f.model_card_id, f.slot_name, f.min_quantity) for f in result.fields) == [
            (result.data.id, entry.slot_name, entry.min_quantity) for entry in _ENTRIES
        ]
