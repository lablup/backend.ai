"""``entity_partial_bulk_purge_ops``: purging named entities; the app config fragment represents it.

No wired purger of this shape declares a guard or a conflict check, so target-3 and target-4
run a test-only action over the role and domain purgers.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Self, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config import AppConfigScopeID
from ai.backend.common.data.entity.app_config_fragment import (
    AppConfigFragmentEntityType,
    AppConfigFragmentID,
)
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission, RoleSource
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import DomainHasUsers
from ai.backend.manager.errors.role_preset import SystemRoleNotEditable
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.purgers import AppConfigFragmentPurger
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.domain.purgers import DomainPurger
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.rbac_models.role.purgers import RolePurger
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.specs.purger import GuardedEntityPurger
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.app_config.actions.fragment.bulk_purge import (
    BulkPurgeAppConfigFragmentAction,
)
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    provision,
)

DENIALS_RECORDED_AS_ERROR_ON_A_FAILED_RUN = pytest.mark.xfail(
    strict=True, reason="a run that raises records the ids it denied as ERROR, not DENIED"
)


@pytest.fixture
async def fragment_db(ops_db: ExtendedAsyncSAEngine) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        ops_db, [AppConfigDefinitionRow, AppConfigAllowListRow, AppConfigFragmentRow]
    ):
        yield ops_db


async def _seed_fragment(db: ExtendedAsyncSAEngine, actors: Actors) -> AppConfigFragmentID:
    """A fragment of the actors' domain, under a config name of its own."""
    fragment_id = AppConfigFragmentID(uuid.uuid4())
    config_name = f"config-{fragment_id.hex[:8]}"
    async with db.begin_session() as sess:
        sess.add(AppConfigDefinitionRow(config_name=config_name))
        await sess.flush()
        sess.add(
            AppConfigAllowListRow(
                config_name=config_name, scope_type=AppConfigScopeType.DOMAIN, rank=0
            )
        )
        await sess.flush()
        sess.add(
            AppConfigFragmentRow(
                id=fragment_id,
                config_name=config_name,
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=AppConfigScopeID(actors.domain_id),
                config={"name": config_name},
            )
        )
        await sess.commit()
    await provision(
        db,
        AppConfigFragmentEntityType(),
        fragment_id,
        [(DomainEntityType(), actors.domain_id)],
    )
    return fragment_id


@pytest.fixture
async def fragments(
    fragment_db: ExtendedAsyncSAEngine, actors: Actors
) -> list[AppConfigFragmentID]:
    fragment_ids = [await _seed_fragment(fragment_db, actors) for _ in range(2)]
    await grant(
        fragment_db,
        actors.user_id(Actor.GRANTED),
        DomainEntityType(),
        actors.domain_id,
        AppConfigFragmentEntityType(),
        Permission.HARD_DELETE,
    )
    return fragment_ids


async def _grant_on(
    db: ExtendedAsyncSAEngine, actors: Actors, fragment_id: AppConfigFragmentID
) -> None:
    """HARD_DELETE for the ungranted actor on this one fragment, row or no row."""
    await grant(
        db,
        actors.user_id(Actor.UNGRANTED),
        AppConfigFragmentEntityType(),
        fragment_id,
        AppConfigFragmentEntityType(),
        Permission.HARD_DELETE,
    )


async def _remaining(
    db: ExtendedAsyncSAEngine, fragment_ids: list[AppConfigFragmentID]
) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(AppConfigFragmentRow.id).where(AppConfigFragmentRow.id.in_(fragment_ids))
        )
        return set(rows.all())


async def _nodes(
    db: ExtendedAsyncSAEngine, fragment_ids: list[AppConfigFragmentID]
) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(VirtualEntityRow.entity_id).where(
                VirtualEntityRow.entity_id.in_(fragment_ids)
            )
        )
        return set(rows.all())


def _purge(fragment_ids: Sequence[AppConfigFragmentID]) -> BulkPurgeAppConfigFragmentAction:
    return BulkPurgeAppConfigFragmentAction(
        purgers=[AppConfigFragmentPurger(fragment_id=fragment_id) for fragment_id in fragment_ids]
    )


def _processor(harness: OpsHarness) -> Any:
    return harness.group(AppConfigFragmentEntityType()).entity_partial_bulk_purge_ops(
        BulkPurgeAppConfigFragmentAction
    )


def _spy_writes(monkeypatch: pytest.MonkeyPatch) -> list[list[EntityIdentifier]]:
    calls: list[list[EntityIdentifier]] = []
    original = OpsRepository.partial_bulk_purge_entities

    async def spy(self: OpsRepository[Any], purgers: Mapping[EntityIdentifier, Any]) -> Any:
        calls.append(list(purgers))
        return await original(self, purgers)

    monkeypatch.setattr(OpsRepository, "partial_bulk_purge_entities", spy)
    return calls


async def _action_ids(db: ExtendedAsyncSAEngine) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(AuditLogRow.action_id).where(
                AuditLogRow.action_name == BulkPurgeAppConfigFragmentAction.action_name()
            )
        )
        return set(rows.all())


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced"),
        [
            pytest.param(Actor.SUPERADMIN, True, id="actor-1"),
            pytest.param(Actor.GRANTED, True, id="actor-3"),
            pytest.param(Actor.UNGRANTED, False, id="actor-6"),
        ],
    )
    async def test_every_id_is_purged(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        fragments: list[AppConfigFragmentID],
        actor: Actor,
        enforced: bool,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            result = await _processor(harness).run(_purge(fragments))

        assert [item.value.id for item in result.items] == fragments
        assert await _remaining(fragment_db, fragments) == set()

    @pytest.mark.parametrize(
        "actor",
        [pytest.param(Actor.MONITOR, id="actor-2"), pytest.param(Actor.UNGRANTED, id="actor-4")],
    )
    async def test_every_item_is_denied(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        fragments: list[AppConfigFragmentID],
        monkeypatch: pytest.MonkeyPatch,
        actor: Actor,
    ) -> None:
        writes = _spy_writes(monkeypatch)

        with actors.acting_as(actor):
            result = await _processor(harness).run(_purge(fragments))

        assert all(item.is_denied for item in result.items)
        assert all(isinstance(item.error, NotEnoughPermission) for item in result.items)
        assert [entity_id for call in writes for entity_id in call] == []
        assert await _remaining(fragment_db, fragments) == set(fragments)

    @pytest.mark.parametrize(
        "enforced",
        [
            pytest.param(True, id="actor-5", marks=ANONYMOUS_NOT_REFUSED),
            pytest.param(False, id="actor-5-rbac-off", marks=ANONYMOUS_NOT_REFUSED),
        ],
    )
    async def test_a_caller_with_no_user_is_refused_the_run(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        fragments: list[AppConfigFragmentID],
        monkeypatch: pytest.MonkeyPatch,
        enforced: bool,
    ) -> None:
        harness.enforce(enforced)
        writes = _spy_writes(monkeypatch)

        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(_purge(fragments))

        assert writes == []
        assert await _remaining(fragment_db, fragments) == set(fragments)
        assert_refused(raised.value)


class TestTarget:
    async def test_a_missing_id_fails_alone(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        fragments: list[AppConfigFragmentID],
    ) -> None:
        """target-1."""
        missing = AppConfigFragmentID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(_purge([fragments[0], missing]))

        purged, gone = result.items
        assert purged.value.id == fragments[0]
        assert isinstance(gone.error, EntityNotFoundError)
        assert not gone.is_denied
        assert await _remaining(fragment_db, fragments) == {fragments[1]}

    async def test_a_missing_id_is_denied_to_a_user(
        self, harness: OpsHarness, actors: Actors, fragments: list[AppConfigFragmentID]
    ) -> None:
        """target-2."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_purge([AppConfigFragmentID(uuid.uuid4())]))

        (item,) = result.items
        assert item.is_denied
        assert isinstance(item.error, NotEnoughPermission)

    async def test_the_row_and_its_node_are_gone(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        fragments: list[AppConfigFragmentID],
    ) -> None:
        """target-5."""
        assert await _nodes(fragment_db, fragments) == set(fragments)

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_purge(fragments))

        assert await _remaining(fragment_db, fragments) == set()
        assert await _nodes(fragment_db, fragments) == set()


class TestMulti:
    async def test_a_denied_entity_is_left_as_it_was(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        fragments: list[AppConfigFragmentID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """multi-1."""
        allowed, denied = fragments
        await _grant_on(fragment_db, actors, allowed)
        writes = _spy_writes(monkeypatch)

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(_purge(fragments))

        purged, refused = result.items
        assert purged.value.id == allowed
        assert refused.is_denied
        assert isinstance(refused.error, NotEnoughPermission)
        assert writes == [[allowed]]
        assert await _remaining(fragment_db, fragments) == {denied}

    async def test_a_repeated_id_is_written_once_and_answered_at_every_place(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        fragments: list[AppConfigFragmentID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """multi-2."""
        allowed, denied = fragments
        await _grant_on(fragment_db, actors, allowed)
        writes = _spy_writes(monkeypatch)

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(_purge([allowed, denied, allowed, denied]))

        assert result.items[0] == result.items[2]
        assert result.items[1] == result.items[3]
        assert result.items[0].value.id == allowed
        assert result.items[1].is_denied
        assert writes == [[allowed]]

    async def test_no_ids_answer_nothing(
        self, harness: OpsHarness, actors: Actors, fragments: list[AppConfigFragmentID]
    ) -> None:
        """multi-3."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_purge([]))

        assert result.items == []

    async def test_the_answer_keeps_the_order_asked_in(
        self, harness: OpsHarness, actors: Actors, fragments: list[AppConfigFragmentID]
    ) -> None:
        """multi-4."""
        ids = [fragments[1], AppConfigFragmentID(uuid.uuid4()), fragments[0]]

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(_purge(ids))

        assert [item.entity_id for item in result.items] == ids


class TestRecord:
    @pytest.mark.parametrize(
        ("actor", "exists", "status"),
        [
            pytest.param(Actor.GRANTED, True, OperationStatus.SUCCESS, id="record-1"),
            pytest.param(Actor.UNGRANTED, True, OperationStatus.DENIED, id="record-2"),
            pytest.param(Actor.SUPERADMIN, False, OperationStatus.ERROR, id="record-3"),
        ],
    )
    async def test_one_row_on_the_target(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        fragments: list[AppConfigFragmentID],
        actor: Actor,
        exists: bool,
        status: OperationStatus,
    ) -> None:
        target = fragments[0] if exists else AppConfigFragmentID(uuid.uuid4())

        with actors.acting_as(actor):
            await _processor(silent_reads_harness).run(_purge([target]))

        records = await silent_reads_harness.audit(BulkPurgeAppConfigFragmentAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(target), ActionOperationType.PURGE, status)
        ]

    async def test_each_entity_is_recorded_with_its_own_status_under_one_action(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        fragments: list[AppConfigFragmentID],
    ) -> None:
        """record-4: the row-less id carries a grant, so it reaches the write and fails there."""
        allowed, denied = fragments
        missing = AppConfigFragmentID(uuid.uuid4())
        await _grant_on(fragment_db, actors, allowed)
        await _grant_on(fragment_db, actors, missing)

        with actors.acting_as(Actor.UNGRANTED):
            await _processor(harness).run(_purge([allowed, denied, missing]))

        records = await harness.audit(BulkPurgeAppConfigFragmentAction.action_name())
        assert {(r.entity_type, r.entity_id): r.status for r in records} == {
            entity_key(allowed): OperationStatus.SUCCESS,
            entity_key(denied): OperationStatus.DENIED,
            entity_key(missing): OperationStatus.ERROR,
        }
        assert len(records) == 3
        assert len(await _action_ids(fragment_db)) == 1

    @DENIALS_RECORDED_AS_ERROR_ON_A_FAILED_RUN
    async def test_a_failed_run_keeps_its_denials(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        fragments: list[AppConfigFragmentID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""
        allowed, denied = fragments
        await _grant_on(fragment_db, actors, allowed)

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the write failed")

        monkeypatch.setattr(OpsRepository, "partial_bulk_purge_entities", broken)

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_purge(fragments))

        records = await harness.audit(BulkPurgeAppConfigFragmentAction.action_name())
        assert {(r.entity_type, r.entity_id): r.status for r in records} == {
            entity_key(allowed): OperationStatus.ERROR,
            entity_key(denied): OperationStatus.DENIED,
        }

    @ANONYMOUS_RECORDED_AS_ERROR
    async def test_a_caller_with_no_user_is_denied_on_every_entity(
        self, harness: OpsHarness, actors: Actors, fragments: list[AppConfigFragmentID]
    ) -> None:
        """record-6."""
        with actors.acting_as(Actor.ANONYMOUS):
            with contextlib.suppress(BackendAIError):
                await _processor(harness).run(_purge(fragments))

        records = await harness.audit(BulkPurgeAppConfigFragmentAction.action_name())
        assert sorted(((r.entity_type, r.entity_id), r.status) for r in records) == sorted(
            (entity_key(fragment_id), OperationStatus.DENIED) for fragment_id in fragments
        )

    async def test_no_ids_record_nothing(
        self, harness: OpsHarness, actors: Actors, fragments: list[AppConfigFragmentID]
    ) -> None:
        """record-7."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_purge([]))

        assert await harness.audit(BulkPurgeAppConfigFragmentAction.action_name()) == []

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        fragments: list[AppConfigFragmentID],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-8."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_purge([fragments[0]]))

        records = await harness.audit(BulkPurgeAppConfigFragmentAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _remaining(fragment_db, fragments) == set(fragments)


class TestResult:
    async def test_the_value_is_the_row_before_the_purge(
        self, harness: OpsHarness, actors: Actors, fragments: list[AppConfigFragmentID]
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_purge([fragments[0]]))

        (item,) = result.items
        assert item.value.id == fragments[0]
        assert item.value.config == {"name": f"config-{fragments[0].hex[:8]}"}


@dataclass
class _PurgeAction(PartialBulkPurgeEntityOpsAction[Any, Any]):
    """A test-only action of this shape over whichever real purgers it is handed."""

    purgers: Sequence[GuardedEntityPurger[Any, Any]]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "test_bulk_purge"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [purger.entity_id() for purger in self.purgers]

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, GuardedEntityPurger[Any, Any]]:
        return {purger.entity_id(): purger for purger in self.purgers}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, purgers=[purger for purger in self.purgers if purger.entity_id() in allowed]
        )


async def _seed_role(db: ExtendedAsyncSAEngine, actors: Actors, source: RoleSource) -> RoleID:
    role_id = RoleID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            RoleRow(
                id=role_id,
                name=f"target-{role_id.hex[:8]}",
                source=source,
                status=RoleStatus.ACTIVE,
                scope_type=DomainEntityType(),
                scope_id=actors.domain_id,
            )
        )
        await sess.commit()
    await provision(db, RoleEntityType(), role_id, [(DomainEntityType(), actors.domain_id)])
    return role_id


async def _roles_left(db: ExtendedAsyncSAEngine, role_ids: list[RoleID]) -> set[uuid.UUID]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.scalars(sa.select(RoleRow.id).where(RoleRow.id.in_(role_ids)))
        return set(rows.all())


class TestGuard:
    """Rows that need a guard, run on the role purger, which declines a SYSTEM role."""

    async def test_a_guarded_id_fails_alone(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-3."""
        custom = await _seed_role(ops_db, actors, RoleSource.CUSTOM)
        system = await _seed_role(ops_db, actors, RoleSource.SYSTEM)
        processor = harness.group(RoleEntityType()).entity_partial_bulk_purge_ops(_PurgeAction)

        with actors.acting_as(Actor.SUPERADMIN):
            result = await processor.run(
                _PurgeAction(purgers=[RolePurger(role_id=custom), RolePurger(role_id=system)])
            )

        purged, refused = result.items
        assert purged.value is not None
        assert purged.value.id == custom
        assert isinstance(refused.error, SystemRoleNotEditable)
        assert not refused.is_denied
        assert await _roles_left(ops_db, [custom, system]) == {system}

    async def test_a_guard_failure_is_recorded_as_an_error(
        self, ops_db: ExtendedAsyncSAEngine, silent_reads_harness: OpsHarness, actors: Actors
    ) -> None:
        """record-3: a guard failure."""
        system = await _seed_role(ops_db, actors, RoleSource.SYSTEM)
        processor = silent_reads_harness.group(RoleEntityType()).entity_partial_bulk_purge_ops(
            _PurgeAction
        )

        with actors.acting_as(Actor.SUPERADMIN):
            await processor.run(_PurgeAction(purgers=[RolePurger(role_id=system)]))

        records = await silent_reads_harness.audit(_PurgeAction.action_name())
        assert [((r.entity_type, r.entity_id), r.operation, r.status) for r in records] == [
            (entity_key(system), ActionOperationType.PURGE, OperationStatus.ERROR)
        ]


async def _seed_bare_domain(db: ExtendedAsyncSAEngine) -> tuple[DomainID, str]:
    domain_id = DomainID(uuid.uuid4())
    name = f"bare-{domain_id.hex[:8]}"
    async with db.begin_session() as sess:
        sess.add(DomainRow(id=domain_id, name=name, total_resource_slots=ResourceSlot()))
        await sess.commit()
    await provision(db, DomainEntityType(), domain_id)
    return domain_id, name


class TestConflict:
    async def test_a_referenced_id_fails_alone(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-4: the domain purger refuses a domain users still belong to."""
        bare_id, bare_name = await _seed_bare_domain(ops_db)
        processor = harness.group(DomainEntityType()).entity_partial_bulk_purge_ops(_PurgeAction)

        with actors.acting_as(Actor.SUPERADMIN):
            result = await processor.run(
                _PurgeAction(
                    purgers=[
                        DomainPurger(domain_id=bare_id, name=bare_name),
                        DomainPurger(domain_id=actors.domain_id, name=actors.domain_name),
                    ]
                )
            )

        purged, refused = result.items
        assert purged.value is not None
        assert purged.value.id == bare_id
        assert isinstance(refused.error, DomainHasUsers)
        assert not refused.is_denied
        async with ops_db.begin_readonly_session() as sess:
            left = await sess.scalars(
                sa.select(DomainRow.id).where(DomainRow.id.in_([bare_id, actors.domain_id]))
            )
            assert set(left.all()) == {actors.domain_id}
