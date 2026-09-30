"""``global_create_ops``: creating one global entity, with the user resource policy as the
representative."""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.login_client_type import LoginClientTypeEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_policy import UserResourcePolicyEntityType
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.auth import InsufficientPrivilege, LoginClientTypeConflict
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.login_client_type.creators import LoginClientTypeCreator
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.resource_policy.creators import UserResourcePolicyCreator
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.login_client_type.actions.create import (
    CreateLoginClientTypeAction,
)
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
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


async def _grant_global(
    db: ExtendedAsyncSAEngine, user_id: UserID, entity_type: EntityType, permission: Permission
) -> None:
    scope = global_entity_id(GlobalEntityName.GLOBAL)
    await grant(db, user_id, scope.entity_type(), scope, entity_type, permission)


@pytest.fixture
async def granted(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> None:
    for actor, permission in (
        (Actor.GRANTED, Permission.CREATE),
        (Actor.READ_ONLY, Permission.READ),
    ):
        await _grant_global(
            ops_db, actors.user_id(actor), UserResourcePolicyEntityType(), permission
        )


async def _count(db: ExtendedAsyncSAEngine, name: str) -> int:
    async with db.begin_readonly_session() as sess:
        count = await sess.scalar(
            sa.select(sa.func.count()).where(UserResourcePolicyRow.name == name)
        )
    return count or 0


def _processor(harness: OpsHarness) -> Any:
    return harness.group(UserResourcePolicyEntityType()).global_create_ops(
        CreateUserResourcePolicyAction
    )


def _create(name: str) -> CreateUserResourcePolicyAction:
    return CreateUserResourcePolicyAction(
        creator=UserResourcePolicyCreator(
            name=name,
            max_vfolder_count=3,
            max_quota_scope_size=-1,
            max_session_count_per_model_session=2,
            max_customized_image_count=1,
        )
    )


def _new_name() -> str:
    return f"policy-{uuid.uuid4().hex[:8]}"


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
        name = _new_name()

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(_create(name))
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(_create(name))
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        assert await _count(ops_db, name) == (0 if error else 1)

    @pytest.mark.parametrize(
        ("at_global", "entity_type"),
        [
            pytest.param(False, UserResourcePolicyEntityType(), id="actor-5"),
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
        name = _new_name()

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(InsufficientPrivilege):
                await _processor(harness).run(_create(name))

        assert await _count(ops_db, name) == 0


class TestTarget:
    async def test_a_new_key_creates_a_row(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """target-1."""
        name = _new_name()

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_create(name))

        assert await _count(ops_db, name) == 1

    async def test_a_taken_key_is_refused(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """target-2: the creator declares no check, so the generic error surfaces."""
        name = _new_name()
        with actors.acting_as(Actor.SUPERADMIN):
            await _processor(harness).run(_create(name))

            with pytest.raises(UniqueConstraintViolationError):
                await _processor(harness).run(_create(name))

        assert await _count(ops_db, name) == 1


@pytest.fixture
async def login_client_type_db(
    ops_db: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(ops_db, [LoginClientTypeRow]):
        yield ops_db


class TestDeclaredConflict:
    async def test_a_taken_key_raises_the_declared_error(
        self, login_client_type_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors
    ) -> None:
        """target-2: the login client type creator declares its own error for the name."""
        processor = harness.group(LoginClientTypeEntityType()).global_create_ops(
            CreateLoginClientTypeAction
        )
        action = CreateLoginClientTypeAction(
            creator=LoginClientTypeCreator(name="cli", description=None)
        )
        with actors.acting_as(Actor.SUPERADMIN):
            await processor.run(action)

            with pytest.raises(LoginClientTypeConflict):
                await processor.run(action)

        async with login_client_type_db.begin_readonly_session() as sess:
            count = await sess.scalar(
                sa.select(sa.func.count()).where(LoginClientTypeRow.name == "cli")
            )
        assert count == 1


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
        ops_db: ExtendedAsyncSAEngine,
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
            async with ops_db.begin_session() as sess:
                sess.add(
                    UserResourcePolicyRow(
                        name=name,
                        max_vfolder_count=0,
                        max_quota_scope_size=-1,
                        max_session_count_per_model_session=0,
                        max_customized_image_count=0,
                    )
                )
                await sess.commit()

        with actors.acting_as(actor):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_create(name))

        records = await silent_reads_harness.audit(CreateUserResourcePolicyAction.action_name())
        assert [(r.entity_type, r.entity_id, r.operation, r.status) for r in records] == [
            (str(GlobalEntityType()), None, ActionOperationType.CREATE, status)
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
        name = _new_name()

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_create(name))

        records = await harness.audit(CreateUserResourcePolicyAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]
        assert await _count(ops_db, name) == 0


class TestResult:
    async def test_the_data_is_the_new_entity(
        self, ops_db: ExtendedAsyncSAEngine, harness: OpsHarness, actors: Actors, granted: None
    ) -> None:
        """result-1."""
        name = _new_name()

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_create(name))

        async with ops_db.begin_readonly_session() as sess:
            stored = await sess.scalar(
                sa.select(UserResourcePolicyRow.uuid).where(UserResourcePolicyRow.name == name)
            )
        assert result.data.uuid == stored
        assert (result.data.name, result.data.max_vfolder_count) == (name, 3)
