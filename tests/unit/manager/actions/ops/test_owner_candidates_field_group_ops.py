"""The operations of an owner-candidates field group, with audit records as the
representative: ``partial_bulk_get_ops`` reads named records, ``nested_field_search_ops``
searches the scopes nested under one.

A record is reached through the entity it is about, a scope it recorded, or the user who
triggered it.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.data.entity.audit_log import AuditLogFieldType, AuditLogID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.types import ActionKind, OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogScopeData
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.audit_log.owner_candidates import AuditLogOwnerCandidates
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.audit_log.searchers import AuditLogScopeSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.audit_log.actions.bulk_get import BulkGetAuditLogsAction
from ai.backend.manager.services.audit_log.actions.scoped_search_scopes import (
    ScopedSearchAuditLogScopesAction,
)
from ai.backend.testutils.ops_contract import (
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    seed_project,
)

_OPERATION = ScopedSearchAuditLogScopesAction.action_name()
_BULK_GET = BulkGetAuditLogsAction.action_name()


@dataclass(frozen=True)
class _World:
    about_project: ProjectID
    """The project ``about`` is about."""
    scope_project: ProjectID
    """The project ``linked`` recorded as its scope."""
    about: AuditLogID
    """A record about a project, with no scope."""
    linked: AuditLogID
    """A relation record naming no entity, with one project scope."""
    triggered: AuditLogID
    """A global record naming no entity, triggered by the read-only actor."""


async def _seed_record(
    db: ExtendedAsyncSAEngine,
    *,
    action_kind: ActionKind,
    entity_type: EntityType | None = None,
    entity_id: uuid.UUID | None = None,
    triggered_by: str | None = None,
    scopes: Sequence[tuple[EntityType, uuid.UUID]] = (),
) -> AuditLogID:
    record_id = AuditLogID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            AuditLogRow(
                id=record_id,
                action_kind=action_kind,
                entity_type=entity_type,
                entity_id=entity_id,
                operation="update",
                action_name="seeded",
                action_id=uuid.uuid4(),
                description="seeded",
                status=OperationStatus.SUCCESS,
                triggered_by=triggered_by,
            )
        )
        await sess.flush()
        sess.add_all([
            AuditLogScopeRow(audit_log_id=record_id, scope_type=scope_type, scope_id=scope_id)
            for scope_type, scope_id in scopes
        ])
        await sess.commit()
    return record_id


@pytest.fixture
async def world(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> _World:
    """The read-only actor reads the scope project alone; the granted actor both projects."""
    about_project = await seed_project(ops_db, actors)
    scope_project = await seed_project(ops_db, actors)
    for actor, project_id in (
        (Actor.GRANTED, about_project),
        (Actor.GRANTED, scope_project),
        (Actor.READ_ONLY, scope_project),
    ):
        await grant(
            ops_db,
            actors.user_id(actor),
            ProjectEntityType(),
            project_id,
            ProjectEntityType(),
            Permission.READ,
        )
    return _World(
        about_project=about_project,
        scope_project=scope_project,
        about=await _seed_record(
            ops_db,
            action_kind=ActionKind.SINGLE_ENTITY,
            entity_type=ProjectEntityType(),
            entity_id=about_project,
        ),
        linked=await _seed_record(
            ops_db,
            action_kind=ActionKind.RELATION,
            scopes=[(ProjectEntityType(), scope_project)],
        ),
        triggered=await _seed_record(
            ops_db,
            action_kind=ActionKind.GLOBAL,
            triggered_by=str(actors.user_id(Actor.READ_ONLY)),
        ),
    )


def _audit_logs(harness: OpsHarness) -> Any:
    return harness.registry.dangling_owner_candidates_field_group(
        FieldGroupMeta(AuditLogFieldType()), AuditLogData, AuditLogOwnerCandidates()
    )


def _processor(harness: OpsHarness) -> Any:
    return _audit_logs(harness).nested_field_search_ops(
        ScopedSearchAuditLogScopesAction, AuditLogScopeData
    )


def _bulk_get(harness: OpsHarness) -> Any:
    return _audit_logs(harness).partial_bulk_get_ops(BulkGetAuditLogsAction)


def _search(audit_log_id: AuditLogID) -> ScopedSearchAuditLogScopesAction:
    return ScopedSearchAuditLogScopesAction(
        audit_log_id=audit_log_id, searcher=AuditLogScopeSearcher(pagination=NoPagination())
    )


def _found(items: Sequence[AuditLogScopeData]) -> set[tuple[AuditLogID, str, uuid.UUID]]:
    return {(item.audit_log_id, item.scope_type, item.scope_id) for item in items}


class TestNestedSearchActor:
    async def test_a_superadmin_reads_the_scopes_of_any_record(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(_search(world.linked))

        assert _found(result.items) == {
            (world.linked, ProjectEntityType.name(), world.scope_project)
        }

    async def test_an_ungranted_caller_is_refused(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(NotEnoughPermission) as raised:
                await _processor(harness).run(_search(world.linked))

        assert_refused(raised.value)


class TestNestedSearchOwner:
    async def test_a_record_naming_no_entity_is_reached_through_its_scope(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        with actors.acting_as(Actor.READ_ONLY):
            result = await _processor(harness).run(_search(world.linked))

        assert _found(result.items) == {
            (world.linked, ProjectEntityType.name(), world.scope_project)
        }

    async def test_a_record_is_reached_through_the_user_who_triggered_it(
        self, harness: OpsHarness, actors: Actors, world: _World, ops_db: ExtendedAsyncSAEngine
    ) -> None:
        reader = actors.user_id(Actor.READ_ONLY)
        await grant(ops_db, reader, UserEntityType(), reader, UserEntityType(), Permission.READ)

        with actors.acting_as(Actor.READ_ONLY):
            result = await _processor(harness).run(_search(world.triggered))

        assert result.items == []

    async def test_a_record_about_an_unreadable_entity_is_refused(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        with actors.acting_as(Actor.READ_ONLY):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_search(world.about))


class TestNestedSearchTarget:
    async def test_a_missing_record_is_not_found_and_records_nothing(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        with actors.acting_as(Actor.SUPERADMIN):
            with pytest.raises(FieldNotFoundError):
                await _processor(harness).run(_search(AuditLogID(uuid.uuid4())))

        assert await harness.audit(_OPERATION) == []


class TestNestedSearchRecord:
    async def test_a_reached_record_is_recorded_on_the_candidate_that_passed(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        with actors.acting_as(Actor.READ_ONLY):
            await _processor(harness).run(_search(world.linked))

        records = await harness.audit(_OPERATION)
        assert [((r.entity_type, r.entity_id), r.status) for r in records] == [
            (entity_key(world.scope_project), OperationStatus.SUCCESS)
        ]
        assert str(world.linked) in records[0].description

    async def test_a_refused_record_is_recorded_on_its_first_candidate(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        with actors.acting_as(Actor.READ_ONLY):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_search(world.about))

        records = await harness.audit(_OPERATION)
        assert [((r.entity_type, r.entity_id), r.status) for r in records] == [
            (entity_key(world.about_project), OperationStatus.DENIED)
        ]


class TestBulkGet:
    async def test_a_superadmin_reads_every_record(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        ids = [world.about, world.linked, world.triggered]

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _bulk_get(harness).run(BulkGetAuditLogsAction(ids=ids))

        assert set(result.successes) == set(ids)
        assert result.errors == {}

    async def test_each_record_is_reached_through_any_one_owner(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        """``linked`` names no entity and is reached through its scope; ``about`` is about
        a project the reader may not read."""
        with actors.acting_as(Actor.READ_ONLY):
            result = await _bulk_get(harness).run(
                BulkGetAuditLogsAction(ids=[world.about, world.linked])
            )

        assert set(result.successes) == {world.linked}
        assert {k: type(v) for k, v in result.errors.items()} == {world.about: NotEnoughPermission}

    async def test_a_missing_record_fails_alone(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        missing = AuditLogID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _bulk_get(harness).run(
                BulkGetAuditLogsAction(ids=[world.linked, missing])
            )

        assert set(result.successes) == {world.linked}
        assert {k: type(v) for k, v in result.errors.items()} == {missing: FieldNotFoundError}

    async def test_runs_are_recorded_on_the_owner_that_answered(
        self, harness: OpsHarness, actors: Actors, world: _World
    ) -> None:
        with actors.acting_as(Actor.READ_ONLY):
            await _bulk_get(harness).run(BulkGetAuditLogsAction(ids=[world.about, world.linked]))

        records = await harness.audit(_BULK_GET)
        assert sorted(((r.entity_type, r.entity_id), r.status) for r in records) == sorted([
            (entity_key(world.scope_project), OperationStatus.SUCCESS),
            (entity_key(world.about_project), OperationStatus.DENIED),
        ])
