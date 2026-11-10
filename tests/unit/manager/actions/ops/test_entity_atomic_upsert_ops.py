"""``entity_atomic_upsert_ops``: writing several entities in one scope at once, with the
app config fragment as the representative.

A fragment carries no unique key besides its upsert key, so multi-3 fails an item on the
allow-list FK instead.
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncGenerator, Sequence
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config_fragment import (
    AppConfigFragmentEntityType,
    AppConfigFragmentID,
)
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.errors.app_config import AppConfigFragmentWriteNotAllowed
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_fragment.upserters import AppConfigFragmentUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.app_config.actions.fragment.bulk_upsert import (
    BulkUpsertAppConfigFragmentsAction,
)
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
    provision,
)

_ALLOWED = ("alpha", "beta")
_NOT_ALLOWED = "gamma"


@pytest.fixture
async def fragment_db(
    ops_db: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        ops_db, [AppConfigDefinitionRow, AppConfigAllowListRow, AppConfigFragmentRow]
    ):
        async with ops_db.begin_session() as sess:
            sess.add_all([
                AppConfigDefinitionRow(config_name=name) for name in (*_ALLOWED, _NOT_ALLOWED)
            ])
            await sess.flush()
            sess.add_all([
                AppConfigAllowListRow(
                    config_name=name, scope_type=AppConfigScopeType.DOMAIN, rank=0
                )
                for name in _ALLOWED
            ])
            await sess.commit()
        yield ops_db


@pytest.fixture
async def owner(fragment_db: ExtendedAsyncSAEngine, actors: Actors) -> DomainID:
    for actor, entity_type in (
        (Actor.GRANTED, AppConfigFragmentEntityType()),
        (Actor.READ_ONLY, UserEntityType()),
    ):
        await grant(
            fragment_db,
            actors.user_id(actor),
            DomainEntityType(),
            actors.domain_id,
            entity_type,
            Permission.CREATE | Permission.UPDATE,
        )
    return actors.domain_id


def _action(
    owner: DomainID, items: Sequence[tuple[str, int]]
) -> BulkUpsertAppConfigFragmentsAction:
    return BulkUpsertAppConfigFragmentsAction(
        owner=owner,
        upserters=[
            AppConfigFragmentUpserter(config_name=name, owner=owner, config={"value": value})
            for name, value in items
        ],
    )


def _processor(harness: OpsHarness) -> Any:
    return harness.group(AppConfigFragmentEntityType()).entity_atomic_upsert_ops(
        BulkUpsertAppConfigFragmentsAction
    )


async def _stored(db: ExtendedAsyncSAEngine) -> dict[str, tuple[AppConfigFragmentID, Any]]:
    """Every fragment row, by config name: its id and its config."""
    async with db.begin_readonly_session() as sess:
        rows = (await sess.scalars(sa.select(AppConfigFragmentRow))).all()
    return {row.config_name: (row.id, row.config) for row in rows}


async def _seed_fragment(
    db: ExtendedAsyncSAEngine, owner: DomainID, name: str, value: int
) -> AppConfigFragmentID:
    async with db.begin_session() as sess:
        row = AppConfigFragmentRow(
            config_name=name,
            scope_type=AppConfigScopeType.DOMAIN,
            scope_id=owner,
            config={"value": value},
        )
        sess.add(row)
        await sess.flush()
        fragment_id = AppConfigFragmentID(row.id)
        await sess.commit()
    await provision(db, AppConfigFragmentEntityType(), fragment_id, [(DomainEntityType(), owner)])
    return fragment_id


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
                Actor.ANONYMOUS, True, BackendAIError, id="actor-7", marks=ANONYMOUS_NOT_REFUSED
            ),
            pytest.param(
                Actor.ANONYMOUS,
                False,
                BackendAIError,
                id="actor-7-rbac-off",
                marks=ANONYMOUS_RUNS_UNENFORCED,
            ),
            pytest.param(Actor.UNGRANTED, False, None, id="actor-8"),
        ],
    )
    async def test_actor(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)
        action = _action(owner, [("alpha", 1)])

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(action)
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(action)
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert set(await _stored(fragment_db)) == (set() if error else {"alpha"})

    @pytest.mark.parametrize("held", [Permission.CREATE, Permission.UPDATE])
    async def test_one_of_the_two_bits_is_refused(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
        held: Permission,
    ) -> None:
        """actor-6."""
        await grant(
            fragment_db,
            actors.user_id(Actor.UNGRANTED),
            DomainEntityType(),
            owner,
            AppConfigFragmentEntityType(),
            held,
        )

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(_action(owner, [("alpha", 1)]))

        assert await _stored(fragment_db) == {}


class TestMulti:
    async def test_every_new_key_is_created(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        """multi-1."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_action(owner, [("alpha", 1), ("beta", 2)]))

        stored = await _stored(fragment_db)
        assert {name: config for name, (_, config) in stored.items()} == {
            "alpha": {"value": 1},
            "beta": {"value": 2},
        }

    async def test_an_existing_key_is_updated_in_place(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        """multi-2."""
        existing = await _seed_fragment(fragment_db, owner, "alpha", 0)

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_action(owner, [("alpha", 1), ("beta", 2)]))

        stored = await _stored(fragment_db)
        assert stored["alpha"] == (existing, {"value": 1})
        assert stored["beta"][1] == {"value": 2}

    async def test_a_failing_item_undoes_every_item(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        """multi-3: the last item names a config the allow list does not."""
        existing = await _seed_fragment(fragment_db, owner, "alpha", 0)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(AppConfigFragmentWriteNotAllowed):
                await _processor(harness).run(
                    _action(owner, [("alpha", 1), ("beta", 2), (_NOT_ALLOWED, 3)])
                )

        assert await _stored(fragment_db) == {"alpha": (existing, {"value": 0})}

    async def test_no_items(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        """multi-4."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_action(owner, []))

        assert result.items == []
        assert await _stored(fragment_db) == {}

    async def test_a_repeated_key_keeps_the_later_value(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        """multi-5."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_action(owner, [("alpha", 1), ("alpha", 2)]))

        async with fragment_db.begin_readonly_session() as sess:
            rows = (await sess.execute(sa.select(AppConfigFragmentRow.config))).scalars().all()
        assert rows == [{"value": 2}]


class TestRecord:
    async def test_one_row_per_entity_written(
        self, silent_reads_harness: OpsHarness, actors: Actors, owner: DomainID
    ) -> None:
        """record-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(silent_reads_harness).run(
                _action(owner, [("alpha", 1), ("beta", 2)])
            )

        records = await silent_reads_harness.audit(BulkUpsertAppConfigFragmentsAction.action_name())
        scopes = frozenset([entity_key(owner)])
        assert sorted(
            ((r.entity_type, r.entity_id), r.operation, r.status, r.scopes) for r in records
        ) == sorted(
            (entity_key(item.id), ActionOperationType.UPSERT, OperationStatus.SUCCESS, scopes)
            for item in result.items
        )

    @pytest.mark.parametrize(
        ("actor", "items", "status"),
        [
            pytest.param(Actor.GRANTED, [], OperationStatus.SUCCESS, id="record-2"),
            pytest.param(Actor.UNGRANTED, [("alpha", 1)], OperationStatus.DENIED, id="record-3"),
            pytest.param(
                Actor.GRANTED,
                [("alpha", 1), (_NOT_ALLOWED, 2)],
                OperationStatus.ERROR,
                id="record-4",
            ),
            pytest.param(
                Actor.ANONYMOUS,
                [("alpha", 1)],
                OperationStatus.DENIED,
                id="record-5",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_a_run_touching_nothing_leaves_one_row(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
        actor: Actor,
        items: list[tuple[str, int]],
        status: OperationStatus,
    ) -> None:
        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_action(owner, items))

        records = await silent_reads_harness.audit(BulkUpsertAppConfigFragmentsAction.action_name())
        assert [(r.entity_type, r.entity_id, r.operation, r.status, r.scopes) for r in records] == [
            (
                str(AppConfigFragmentEntityType()),
                None,
                ActionOperationType.UPSERT,
                status,
                frozenset([entity_key(owner)]),
            )
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-6."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "checked_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_action(owner, [("alpha", 1)]))

        records = await harness.audit(BulkUpsertAppConfigFragmentsAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _stored(fragment_db) == {}


class TestResult:
    async def test_the_items_are_every_entity_written(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_action(owner, [("alpha", 1), ("beta", 2)]))

        stored = await _stored(fragment_db)
        assert sorted(
            (item.id, item.config_name, item.config, item.scope_id) for item in result.items
        ) == sorted(
            (fragment_id, name, config, owner) for name, (fragment_id, config) in stored.items()
        )
