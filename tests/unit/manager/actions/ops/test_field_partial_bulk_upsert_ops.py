"""``partial_bulk_upsert_ops (field)``: putting field rows under several owners at once,
with entity labels on projects as the representative.

No wired action of this shape exists yet, so every case runs on a test-only action
carrying the label upserter. The answer is per owner: an owner's rows are written in
one savepoint, so a row that fails takes that owner's other rows with it and no other
owner's.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Self, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.entity_label import EntityLabelFieldType, EntityLabelKey
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, RuntimeEntityID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.types import (
    ActionBacking,
    ActionGate,
    ActionKind,
    ActionOperationType,
    OperationStatus,
)
from ai.backend.manager.actions.v2.ops.base import PartialBulkUpsertFieldOpsAction
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_label.upserters import EntityLabelUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.entity_label.actions.lookup_owner import (
    LookupBulkEntityLabelOwnerAction,
    LookupEntityLabelOwnerAction,
)
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    seed_project,
)

type Labels = Sequence[tuple[str, str]]
type Spec = Mapping[uuid.UUID, Labels]

_TOO_LONG = "k" * 300
"""A key longer than its column, so the row fails at the write."""


@dataclass(frozen=True)
class _PutLabelsAction(
    PartialBulkUpsertFieldOpsAction[RuntimeEntityID, EntityLabelRow, EntityLabelData]
):
    """Test-only: the partial field upsert shape carrying the label upserter."""

    items: Sequence[tuple[RuntimeEntityID, EntityLabelUpserter]]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "test_put_labels"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(dict.fromkeys(owner for owner, _ in self.items))

    @override
    def to_upserters(self) -> Mapping[RuntimeEntityID, Sequence[EntityLabelUpserter]]:
        grouped: dict[RuntimeEntityID, list[EntityLabelUpserter]] = {}
        for owner, upserter in self.items:
            grouped.setdefault(owner, []).append(upserter)
        return grouped

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, items=[item for item in self.items if item[0] in allowed])


def _owner(project_id: uuid.UUID) -> RuntimeEntityID:
    return RuntimeEntityID(ProjectEntityType(), project_id)


def _put(spec: Spec) -> _PutLabelsAction:
    return _PutLabelsAction(
        items=[
            (_owner(owner), EntityLabelUpserter(key=EntityLabelKey(key), value=value))
            for owner, labels in spec.items()
            for key, value in labels
        ]
    )


async def _grant_update(
    db: ExtendedAsyncSAEngine, actors: Actors, actor: Actor, project_id: ProjectID
) -> None:
    await grant(
        db,
        actors.user_id(actor),
        ProjectEntityType(),
        project_id,
        ProjectEntityType(),
        Permission.UPDATE,
    )


@pytest.fixture
async def projects(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> list[ProjectID]:
    """Two projects the granted actor may write and the read-only actor may read."""
    laid = [await seed_project(ops_db, actors), await seed_project(ops_db, actors)]
    for project_id in laid:
        await _grant_update(ops_db, actors, Actor.GRANTED, project_id)
        await grant(
            ops_db,
            actors.user_id(Actor.READ_ONLY),
            ProjectEntityType(),
            project_id,
            ProjectEntityType(),
            Permission.READ,
        )
    return laid


async def _labels(db: ExtendedAsyncSAEngine, owner_id: uuid.UUID) -> list[tuple[str, str]]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.execute(
            sa.select(EntityLabelRow.key, EntityLabelRow.value)
            .where(EntityLabelRow.entity_id == owner_id)
            .order_by(EntityLabelRow.key)
        )
        return [(key, value) for key, value in rows.all()]


def _group(harness: OpsHarness) -> Any:
    return harness.registry.dangling_lookup_field_group(
        FieldGroupMeta(EntityLabelFieldType()),
        EntityLabelData,
        LookupEntityLabelOwnerAction,
        LookupBulkEntityLabelOwnerAction,
    )


def _processor(harness: OpsHarness) -> Any:
    return _group(harness).partial_bulk_upsert_ops(_PutLabelsAction)


def _spy_writes(monkeypatch: pytest.MonkeyPatch) -> list[list[EntityIdentifier]]:
    """Which owners each repository write was handed, still running it."""
    calls: list[list[EntityIdentifier]] = []
    original = OpsRepository.partial_bulk_upsert_field_entities

    async def recorded(self: OpsRepository[Any], upserters: Mapping[Any, Any]) -> Any:
        calls.append(list(upserters))
        return await original(self, upserters)

    monkeypatch.setattr(OpsRepository, "partial_bulk_upsert_field_entities", recorded)
    return calls


class TestWiring:
    def test_the_factory_records_a_gated_generic_bulk(self, harness: OpsHarness) -> None:
        _processor(harness)

        recorded = {
            record.action_cls: (record.kind, record.gate, record.backing)
            for record in harness.registry.wired_processors()
        }
        assert recorded[_PutLabelsAction] == (
            ActionKind.BULK,
            ActionGate.PERMISSION,
            ActionBacking.GENERIC,
        )


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced"),
        [
            pytest.param(Actor.SUPERADMIN, True, id="actor-1"),
            pytest.param(Actor.GRANTED, True, id="actor-3"),
            pytest.param(Actor.UNGRANTED, False, id="actor-6"),
        ],
    )
    async def test_every_owner_is_written(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        actor: Actor,
        enforced: bool,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            result = await _processor(harness).run(
                _put({projects[0]: [("team", "ops")], projects[1]: [("team", "ml")]})
            )

        assert [item.entity_id for item in result.items] == [_owner(p) for p in projects]
        assert all(item.error is None for item in result.items)
        assert await _labels(ops_db, projects[0]) == [("team", "ops")]
        assert await _labels(ops_db, projects[1]) == [("team", "ml")]

    @pytest.mark.parametrize(
        "actor",
        [
            pytest.param(Actor.MONITOR, id="actor-2"),
            pytest.param(Actor.UNGRANTED, id="actor-4"),
            pytest.param(Actor.READ_ONLY, id="actor-5"),
        ],
    )
    async def test_every_owner_is_denied(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        monkeypatch: pytest.MonkeyPatch,
        actor: Actor,
    ) -> None:
        writes = _spy_writes(monkeypatch)

        with actors.acting_as(actor):
            result = await _processor(harness).run(
                _put({projects[0]: [("team", "ops")], projects[1]: [("team", "ml")]})
            )

        assert all(item.is_denied for item in result.items)
        assert all(isinstance(item.error, NotEnoughPermission) for item in result.items)
        assert writes == [[]]
        for project_id in projects:
            assert await _labels(ops_db, project_id) == []

    @pytest.mark.parametrize(
        "enforced",
        [
            pytest.param(True, id="actor-7", marks=ANONYMOUS_NOT_REFUSED),
            pytest.param(False, id="actor-7-rbac-off", marks=ANONYMOUS_NOT_REFUSED),
        ],
    )
    async def test_a_caller_with_no_user_is_refused_the_run(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        monkeypatch: pytest.MonkeyPatch,
        enforced: bool,
    ) -> None:
        harness.enforce(enforced)
        writes = _spy_writes(monkeypatch)

        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(_put({projects[0]: [("team", "ops")]}))

        assert writes == []
        assert await _labels(ops_db, projects[0]) == []
        assert_refused(raised.value)


class TestMulti:
    async def test_a_denied_owner_is_left_as_it_was(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """multi-1: the caller may write the first project alone."""
        allowed, denied = projects
        await _grant_update(ops_db, actors, Actor.UNGRANTED, allowed)
        writes = _spy_writes(monkeypatch)

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(
                _put({allowed: [("team", "ops")], denied: [("team", "ml")]})
            )

        written, refused = result.items
        assert written.entity_id == _owner(allowed)
        assert written.error is None
        assert refused.entity_id == _owner(denied)
        assert refused.is_denied
        assert isinstance(refused.error, NotEnoughPermission)
        assert writes == [[_owner(allowed)]]
        assert await _labels(ops_db, allowed) == [("team", "ops")]
        assert await _labels(ops_db, denied) == []

    async def test_an_owner_named_by_several_items_is_answered_once(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """multi-2: two keys on one owner are one item carrying both rows."""
        writes = _spy_writes(monkeypatch)

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _put({projects[0]: [("team", "ops"), ("tier", "gold")]})
            )

        (item,) = result.items
        assert item.entity_id == _owner(projects[0])
        assert [(row.key, row.value) for row in item.value or []] == [
            ("team", "ops"),
            ("tier", "gold"),
        ]
        assert writes == [[_owner(projects[0])]]
        assert await _labels(ops_db, projects[0]) == [("team", "ops"), ("tier", "gold")]

    async def test_no_items_answer_nothing(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """multi-3."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_put({}))

        assert result.items == []

    async def test_the_answer_keeps_the_order_asked_in(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """multi-4."""
        owners = [projects[1], uuid.uuid4(), projects[0]]

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(
                _put({owner: [("team", "ops")] for owner in owners})
            )

        assert [item.entity_id for item in result.items] == [_owner(o) for o in owners]


class TestTarget:
    async def test_a_known_key_has_its_value_replaced(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """target-1."""
        with actors.acting_as(Actor.GRANTED):
            first = await _processor(harness).run(_put({projects[0]: [("team", "ops")]}))
            second = await _processor(harness).run(_put({projects[0]: [("team", "infra")]}))

        (before,) = first.items
        (after,) = second.items
        assert before.value is not None and after.value is not None
        assert after.value[0].id == before.value[0].id
        assert await _labels(ops_db, projects[0]) == [("team", "infra")]

    async def test_a_failing_row_takes_its_owner_down_and_no_other(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """target-2: the owner's good row is rolled back with the bad one; the other
        owner is written."""
        broken, fine = projects

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _put({
                    broken: [("team", "ops"), (_TOO_LONG, "x")],
                    fine: [("team", "ml")],
                })
            )

        failed, written = result.items
        assert failed.entity_id == _owner(broken)
        assert failed.error is not None
        assert not failed.is_denied
        assert written.entity_id == _owner(fine)
        assert written.error is None
        assert await _labels(ops_db, broken) == []
        assert await _labels(ops_db, fine) == [("team", "ml")]

    async def test_a_missing_owner_is_a_denial_for_a_user(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """target-3."""
        missing = uuid.uuid4()

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _put({projects[0]: [("team", "ops")], missing: [("team", "ml")]})
            )

        written, refused = result.items
        assert written.error is None
        assert refused.entity_id == _owner(missing)
        assert refused.is_denied
        assert isinstance(refused.error, NotEnoughPermission)
        assert await _labels(ops_db, missing) == []


class TestRecord:
    @pytest.mark.parametrize(
        ("actor", "status"),
        [
            pytest.param(Actor.GRANTED, OperationStatus.SUCCESS, id="record-1"),
            pytest.param(Actor.UNGRANTED, OperationStatus.DENIED, id="record-2"),
        ],
    )
    async def test_one_row_per_owner(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        actor: Actor,
        status: OperationStatus,
    ) -> None:
        """A write is recorded whatever the read policy says."""
        with actors.acting_as(actor):
            await _processor(silent_reads_harness).run(
                _put({
                    projects[0]: [("team", "ops"), ("tier", "gold")],
                    projects[1]: [("team", "ml")],
                })
            )

        records = await silent_reads_harness.audit(_PutLabelsAction.action_name())
        assert {((r.entity_type, r.entity_id), r.operation, r.status) for r in records} == {
            (entity_key(_owner(p)), ActionOperationType.UPDATE, status) for p in projects
        }
        assert len(records) == 2

    async def test_a_mixed_run_records_each_owner_on_its_own(
        self,
        ops_db: ExtendedAsyncSAEngine,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """record-3."""
        allowed, denied = projects
        await _grant_update(ops_db, actors, Actor.UNGRANTED, allowed)

        with actors.acting_as(Actor.UNGRANTED):
            await _processor(silent_reads_harness).run(
                _put({allowed: [("team", "ops")], denied: [("team", "ml")]})
            )

        records = await silent_reads_harness.audit(_PutLabelsAction.action_name())
        assert {(r.entity_type, r.entity_id): r.status for r in records} == {
            entity_key(_owner(allowed)): OperationStatus.SUCCESS,
            entity_key(_owner(denied)): OperationStatus.DENIED,
        }

    async def test_a_failing_row_is_an_error_on_its_owner_alone(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
    ) -> None:
        """record-4."""
        broken, fine = projects

        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(
                _put({broken: [(_TOO_LONG, "x")], fine: [("team", "ml")]})
            )

        records = await silent_reads_harness.audit(_PutLabelsAction.action_name())
        assert {(r.entity_type, r.entity_id): r.status for r in records} == {
            entity_key(_owner(broken)): OperationStatus.ERROR,
            entity_key(_owner(fine)): OperationStatus.SUCCESS,
        }

    @ANONYMOUS_RECORDED_AS_ERROR
    async def test_a_caller_with_no_user_is_denied_on_every_owner(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """record-5."""
        with actors.acting_as(Actor.ANONYMOUS):
            with contextlib.suppress(BackendAIError):
                await _processor(harness).run(
                    _put({projects[0]: [("team", "ops")], projects[1]: [("team", "ml")]})
                )

        records = await harness.audit(_PutLabelsAction.action_name())
        assert sorted(((r.entity_type, r.entity_id), r.status) for r in records) == sorted(
            (entity_key(_owner(p)), OperationStatus.DENIED) for p in projects
        )

    async def test_no_items_record_nothing(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """record-6."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_put({}))

        assert await harness.audit(_PutLabelsAction.action_name()) == []

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        projects: list[ProjectID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-7."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_put({projects[0]: [("team", "ops")]}))

        records = await harness.audit(_PutLabelsAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _labels(ops_db, projects[0]) == []


class TestResult:
    async def test_the_value_is_every_row_written_in_the_order_named(
        self, harness: OpsHarness, actors: Actors, projects: list[ProjectID]
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _put({projects[0]: [("tier", "gold"), ("team", "ops")]})
            )

        (item,) = result.items
        assert item.value is not None
        assert [(row.entity, row.key, row.value) for row in item.value] == [
            (_owner(projects[0]), "tier", "gold"),
            (_owner(projects[0]), "team", "ops"),
        ]
