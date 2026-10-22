"""``global_atomic_upsert_ops``: writing several global entities at once, with the
``public`` app config fragments as the representative.

The fragment table's one unique constraint is the upsert key, so the failing item of
multi-3 breaks the foreign key to the allow list instead.
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncGenerator, Sequence
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentEntityType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.app_config import AppConfigFragmentWriteNotAllowed
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_fragment.upserters import (
    PublicAppConfigFragmentUpserter,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.app_config.actions.fragment.global_bulk_upsert import (
    GlobalBulkUpsertAppConfigFragmentsAction,
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

_ALLOWED = ("theme", "locale")
_NOT_ALLOWED = "blocked"


async def _grant_global(
    db: ExtendedAsyncSAEngine, user_id: UserID, entity_type: EntityType, permission: Permission
) -> None:
    scope = global_entity_id(GlobalEntityName.GLOBAL)
    await grant(db, user_id, scope.entity_type(), scope, entity_type, permission)


@pytest.fixture
async def fragment_db(ops_db: ExtendedAsyncSAEngine) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Every config is defined; only the allowed ones may be written at ``public``."""
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
                    config_name=name, scope_type=AppConfigScopeType.PUBLIC, rank=i
                )
                for i, name in enumerate(_ALLOWED)
            ])
            await sess.commit()
        yield ops_db


@pytest.fixture
async def granted(fragment_db: ExtendedAsyncSAEngine, actors: Actors) -> None:
    for actor, permission in (
        (Actor.GRANTED, Permission.CREATE | Permission.UPDATE),
        (Actor.READ_ONLY, Permission.READ),
    ):
        await _grant_global(
            fragment_db, actors.user_id(actor), AppConfigFragmentEntityType(), permission
        )


async def _stored(db: ExtendedAsyncSAEngine) -> dict[str, dict[str, Any]]:
    async with db.begin_readonly_session() as sess:
        rows = await sess.execute(
            sa.select(AppConfigFragmentRow.config_name, AppConfigFragmentRow.config).where(
                AppConfigFragmentRow.scope_type == AppConfigScopeType.PUBLIC
            )
        )
    return {name: config for name, config in rows.all()}


async def _seed(db: ExtendedAsyncSAEngine, config_name: str, config: dict[str, Any]) -> None:
    async with db.begin_session() as sess:
        sess.add(
            AppConfigFragmentRow(
                config_name=config_name,
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id=None,
                config=config,
            )
        )
        await sess.commit()


def _processor(harness: OpsHarness) -> Any:
    return harness.group(AppConfigFragmentEntityType()).global_atomic_upsert_ops(
        GlobalBulkUpsertAppConfigFragmentsAction
    )


def _upsert(
    items: Sequence[tuple[str, dict[str, Any]]],
) -> GlobalBulkUpsertAppConfigFragmentsAction:
    return GlobalBulkUpsertAppConfigFragmentsAction(
        upserters=[
            PublicAppConfigFragmentUpserter(config_name=name, config=config)
            for name, config in items
        ]
    )


_BOTH = [("theme", {"v": 1}), ("locale", {"v": 1})]


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
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        granted: None,
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(_upsert(_BOTH))
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_upsert(_BOTH))
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert await _stored(fragment_db) == ({} if error else dict(_BOTH))

    @pytest.mark.parametrize(
        ("at_global", "entity_type"),
        [
            pytest.param(False, AppConfigFragmentEntityType(), id="actor-5"),
            pytest.param(True, ProjectEntityType(), id="actor-6"),
        ],
    )
    async def test_a_grant_off_the_global_type_is_refused(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        at_global: bool,
        entity_type: EntityType,
    ) -> None:
        """A domain grant on the type, or a global grant on another type, is not enough."""
        user_id = actors.user_id(Actor.UNGRANTED)
        if at_global:
            await _grant_global(fragment_db, user_id, entity_type, Permission.full())
        else:
            await grant(
                fragment_db,
                user_id,
                DomainEntityType(),
                actors.domain_id,
                entity_type,
                Permission.full(),
            )

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(InsufficientPrivilege):
                await _processor(harness).run(_upsert(_BOTH))

        assert await _stored(fragment_db) == {}


class TestMulti:
    async def test_every_new_key_is_created(
        self, fragment_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """multi-1."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_upsert(_BOTH))

        assert await _stored(fragment_db) == dict(_BOTH)

    async def test_existing_keys_are_updated_and_the_rest_created(
        self, fragment_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """multi-2."""
        await _seed(fragment_db, "theme", {"v": 0})

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_upsert([("theme", {"v": 2}), ("locale", {"v": 2})]))

        assert await _stored(fragment_db) == {"theme": {"v": 2}, "locale": {"v": 2}}

    async def test_a_failing_item_takes_every_earlier_write_down(
        self, fragment_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """multi-3: the last item names a config the allow list does not admit."""
        await _seed(fragment_db, "theme", {"v": 0})
        action = _upsert([("theme", {"v": 3}), ("locale", {"v": 3}), (_NOT_ALLOWED, {"v": 3})])

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(AppConfigFragmentWriteNotAllowed):
                await _processor(harness).run(action)

        assert await _stored(fragment_db) == {"theme": {"v": 0}}

    async def test_no_items_is_an_empty_success(
        self, fragment_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """multi-4."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_upsert([]))

        assert result.items == []
        assert await _stored(fragment_db) == {}

    async def test_a_repeated_key_leaves_one_row_with_the_later_value(
        self, fragment_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """multi-5."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_upsert([("theme", {"v": 1}), ("theme", {"v": 2})]))

        assert await _stored(fragment_db) == {"theme": {"v": 2}}


class TestRecord:
    @pytest.mark.parametrize(
        ("actor", "items", "status"),
        [
            pytest.param(Actor.GRANTED, _BOTH, OperationStatus.SUCCESS, id="record-1"),
            pytest.param(Actor.UNGRANTED, _BOTH, OperationStatus.DENIED, id="record-2"),
            pytest.param(
                Actor.GRANTED, [(_NOT_ALLOWED, {"v": 1})], OperationStatus.ERROR, id="record-3"
            ),
            pytest.param(
                Actor.ANONYMOUS,
                _BOTH,
                OperationStatus.DENIED,
                id="record-4",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_one_row_with_no_target(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        granted: None,
        actor: Actor,
        items: list[tuple[str, dict[str, Any]]],
        status: OperationStatus,
    ) -> None:
        """A write is recorded whatever the read policy says."""
        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_upsert(items))

        records = await silent_reads_harness.audit(
            GlobalBulkUpsertAppConfigFragmentsAction.action_name()
        )
        assert [(r.entity_type, r.entity_id, r.operation, r.status) for r in records] == [
            (str(GlobalEntityType()), None, ActionOperationType.UPSERT, status)
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        granted: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "governed_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_upsert(_BOTH))

        records = await harness.audit(GlobalBulkUpsertAppConfigFragmentsAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _stored(fragment_db) == {}


class TestResult:
    async def test_the_items_are_every_entity_written(
        self, fragment_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_upsert(_BOTH))

        assert [(item.config_name, item.config) for item in result.items] == _BOTH
        assert all(item.scope_id is None for item in result.items)
