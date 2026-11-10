"""``global_upsert_ops``, with the client IP masking policy (keyed by its target).

target-3 is not applicable: no entity upserter's table has a unique constraint besides its
upsert key and a server-generated id.
"""

from __future__ import annotations

import contextlib
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyEntityType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.client_ip_masking.actions.upsert import (
    UpsertClientIPMaskingPolicyAction,
)
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    grant,
)

_TARGET = ClientIPMaskingTarget.LOGIN_HISTORY


async def _grant_global(
    db: ExtendedAsyncSAEngine, user_id: UserID, entity_type: EntityType, permission: Permission
) -> None:
    scope = global_entity_id(GlobalEntityName.GLOBAL)
    await grant(db, user_id, scope.entity_type(), scope, entity_type, permission)


@pytest.fixture
async def granted(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> None:
    for actor, permission in (
        (Actor.GRANTED, Permission.CREATE | Permission.UPDATE),
        (Actor.READ_ONLY, Permission.READ),
    ):
        await _grant_global(
            ops_db, actors.user_id(actor), ClientIPMaskingPolicyEntityType(), permission
        )


async def _modes(db: ExtendedAsyncSAEngine) -> list[ClientIPMaskingMode]:
    async with db.begin_readonly_session() as sess:
        return list(
            (
                await sess.scalars(
                    sa.select(ClientIPMaskingPolicyRow.mode).where(
                        ClientIPMaskingPolicyRow.target_type == _TARGET
                    )
                )
            ).all()
        )


def _processor(harness: OpsHarness) -> Any:
    return harness.group(ClientIPMaskingPolicyEntityType()).global_upsert_ops(
        UpsertClientIPMaskingPolicyAction
    )


def _upsert(
    mode: ClientIPMaskingMode = ClientIPMaskingMode.DROP, ipv4_prefix: int | None = None
) -> UpsertClientIPMaskingPolicyAction:
    return UpsertClientIPMaskingPolicyAction(
        target_type=_TARGET, mode=mode, ipv4_prefix=ipv4_prefix, ipv6_prefix=None
    )


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
        ops_db: ExtendedAsyncSAEngine,
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
                await _processor(harness).run(_upsert())
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_upsert())
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert await _modes(ops_db) == ([] if error else [ClientIPMaskingMode.DROP])

    @pytest.mark.parametrize(
        ("at_global", "entity_type"),
        [
            pytest.param(False, ClientIPMaskingPolicyEntityType(), id="actor-5"),
            pytest.param(True, ProjectEntityType(), id="actor-6"),
        ],
    )
    async def test_a_grant_off_the_global_type_is_refused(
        self,
        ops_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        at_global: bool,
        entity_type: EntityType,
    ) -> None:
        """A domain grant on the type, or a global grant on another type, is not enough."""
        user_id = actors.user_id(Actor.UNGRANTED)
        if at_global:
            await _grant_global(ops_db, user_id, entity_type, Permission.full())
        else:
            await grant(
                ops_db,
                user_id,
                DomainEntityType(),
                actors.domain_id,
                entity_type,
                Permission.full(),
            )

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(InsufficientPrivilege):
                await _processor(harness).run(_upsert())

        assert await _modes(ops_db) == []


class TestTarget:
    async def test_a_new_key_creates_a_row(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """target-1."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_upsert())

        assert await _modes(ops_db) == [ClientIPMaskingMode.DROP]

    async def test_an_existing_key_updates_the_row(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """target-2."""
        with actors.acting_as(Actor.GRANTED):
            first = await _processor(harness).run(_upsert(ClientIPMaskingMode.DROP))
            second = await _processor(harness).run(
                _upsert(ClientIPMaskingMode.TRUNCATE, ipv4_prefix=16)
            )

        assert second.data.id == first.data.id
        assert await _modes(ops_db) == [ClientIPMaskingMode.TRUNCATE]


class TestRecord:
    @pytest.mark.parametrize(
        ("actor", "ipv4_prefix", "status"),
        [
            pytest.param(Actor.GRANTED, None, OperationStatus.SUCCESS, id="record-1"),
            pytest.param(Actor.UNGRANTED, None, OperationStatus.DENIED, id="record-2"),
            pytest.param(Actor.GRANTED, 99, OperationStatus.ERROR, id="record-3"),
            pytest.param(
                Actor.ANONYMOUS,
                None,
                OperationStatus.DENIED,
                id="record-4",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_one_row_with_no_target(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        granted: None,
        actor: Actor,
        ipv4_prefix: int | None,
        status: OperationStatus,
    ) -> None:
        """A write is recorded whatever the read policy says; record-3 breaks a check."""
        action = _upsert(ClientIPMaskingMode.TRUNCATE, ipv4_prefix=ipv4_prefix)

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(action)

        records = await silent_reads_harness.audit(UpsertClientIPMaskingPolicyAction.action_name())
        assert [(r.entity_type, r.entity_id, r.operation, r.status) for r in records] == [
            (str(GlobalEntityType()), None, ActionOperationType.UPSERT, status)
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        ops_db: ExtendedAsyncSAEngine,
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
                await _processor(harness).run(_upsert())

        records = await harness.audit(UpsertClientIPMaskingPolicyAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _modes(ops_db) == []


class TestResult:
    async def test_the_data_is_the_row_after_the_write(
        self, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _upsert(ClientIPMaskingMode.TRUNCATE, ipv4_prefix=16)
            )

        assert (result.data.target_type, result.data.mode, result.data.ipv4_prefix) == (
            _TARGET,
            ClientIPMaskingMode.TRUNCATE,
            16,
        )
