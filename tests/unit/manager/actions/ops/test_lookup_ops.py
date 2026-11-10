"""``lookup_ops``: resolving one key into one entity, with a user's email as the key.

target-1 is not applicable: every wired spec's key is held unique by the schema. User email,
resource slot and user/project/keypair resource policy names are unique or primary keys;
runtime variant and VFS storage names are unique; storage namespace has a unique
(storage_id, namespace); a resource preset's two partial unique indexes cover exactly the
lookup's two branches (name with no resource group, name with the given resource group).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.user.actions.lookup import LookupUserAction
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    MONITOR_READ_REFUSED,
    Actor,
    Actors,
    AuditRecord,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    provision,
)

_MISS_MERGED_FOR_MONITOR = pytest.mark.xfail(
    strict=True, reason="only a superadmin gets the miss unmerged (_caller_is_superadmin)"
)


@dataclass(frozen=True)
class _Target:
    user_id: UserID
    email: str


class _Disconnected(Exception):
    pass


@pytest.fixture
async def target(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> _Target:
    """A user in the actors' domain the granted actor may read."""
    user_id = UserID(uuid.uuid4())
    email = f"target-{user_id.hex[:8]}@test.com"
    policy = f"target-policy-{user_id.hex[:8]}"
    async with ops_db.begin_session() as sess:
        sess.add(
            UserResourcePolicyRow(
                name=policy,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
        )
        await sess.flush()
        sess.add(
            UserRow(
                uuid=user_id,
                username=f"target-{user_id.hex[:8]}",
                email=email,
                resource_policy=policy,
                status=UserStatus.ACTIVE,
                need_password_change=False,
                sudo_session_enabled=False,
                domain_name=actors.domain_name,
                domain_id=actors.domain_id,
                role=UserRole.USER,
            )
        )
        await sess.commit()
    await provision(ops_db, UserEntityType(), user_id)
    await grant(
        ops_db,
        actors.user_id(Actor.GRANTED),
        UserEntityType(),
        user_id,
        UserEntityType(),
        Permission.READ,
    )
    return _Target(user_id=user_id, email=email)


def _processor(harness: OpsHarness) -> Any:
    return harness.group(UserEntityType()).lookup_ops(LookupUserAction)


def _missing_email() -> str:
    return f"nobody-{uuid.uuid4().hex[:8]}@test.com"


async def _records(harness: OpsHarness) -> list[AuditRecord]:
    return await harness.audit(LookupUserAction.action_name())


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced", "exists", "error"),
        [
            pytest.param(Actor.SUPERADMIN, True, True, None, id="actor-2"),
            pytest.param(Actor.SUPERADMIN, True, False, EntityNotFoundError, id="actor-3"),
            pytest.param(Actor.GRANTED, True, True, None, id="actor-4"),
            pytest.param(Actor.GRANTED, True, False, GenericBadRequest, id="actor-5"),
            pytest.param(Actor.UNGRANTED, True, True, GenericBadRequest, id="actor-6"),
            pytest.param(Actor.MONITOR, True, True, None, id="actor-7", marks=MONITOR_READ_REFUSED),
            pytest.param(
                Actor.MONITOR,
                True,
                False,
                EntityNotFoundError,
                id="actor-8",
                marks=_MISS_MERGED_FOR_MONITOR,
            ),
            pytest.param(Actor.UNGRANTED, False, True, None, id="actor-9-present"),
            pytest.param(Actor.UNGRANTED, False, False, GenericBadRequest, id="actor-9-missing"),
        ],
    )
    async def test_actor(
        self,
        harness: OpsHarness,
        actors: Actors,
        target: _Target,
        actor: Actor,
        enforced: bool,
        exists: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)
        action = LookupUserAction(email=target.email if exists else _missing_email())

        with actors.acting_as(actor):
            if error is None:
                result = await _processor(harness).run(action)
                assert result.resolved_entity_id == target.user_id
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(action)
                assert type(raised.value) is error

    @ANONYMOUS_NOT_REFUSED
    async def test_an_anonymous_caller_is_refused_before_running(
        self,
        harness: OpsHarness,
        actors: Actors,
        target: _Target,
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """actor-1."""
        reads = repository_calls("lookup")

        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(LookupUserAction(email=target.email))

        assert_refused(raised.value)
        assert reads == []


class TestTarget:
    async def test_a_miss_and_a_denial_carry_neither_the_key_nor_the_id(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """target-2: the two answers are one answer, naming nothing the caller gave or got."""
        missing = _missing_email()

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(GenericBadRequest) as missing_error:
                await _processor(harness).run(LookupUserAction(email=missing))
            with pytest.raises(GenericBadRequest) as denied_error:
                await _processor(harness).run(LookupUserAction(email=target.email))

        assert str(missing_error.value) == str(denied_error.value)
        assert missing_error.value.status_code == denied_error.value.status_code
        assert missing_error.value.error_code() == denied_error.value.error_code()
        for message in (str(missing_error.value), str(denied_error.value)):
            assert missing not in message
            assert target.email not in message
            assert str(target.user_id) not in message

    async def test_a_failure_that_is_neither_is_raised_unchanged(
        self,
        harness: OpsHarness,
        actors: Actors,
        target: _Target,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """target-3."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise _Disconnected("the database is gone")

        monkeypatch.setattr(V2ReadOps, "lookup_entity_id", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(_Disconnected):
                await _processor(harness).run(LookupUserAction(email=target.email))

        records = await _records(harness)
        assert [(r.entity_id, r.status) for r in records] == [(None, OperationStatus.ERROR)]


class TestRecord:
    async def test_a_success_is_recorded_on_the_entity_with_the_key(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """record-1."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(LookupUserAction(email=target.email))

        records = await _records(harness)
        assert [
            ((r.entity_type, r.entity_id), r.operation, r.status, r.lookup_kind, r.lookup_key)
            for r in records
        ] == [
            (
                entity_key(target.user_id),
                ActionOperationType.LOOKUP,
                OperationStatus.SUCCESS,
                "user_email",
                f"email={target.email}",
            )
        ]

    async def test_a_success_is_not_recorded_unless_opted_in(
        self, silent_reads_harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """record-1, with the read left out of the policy."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(LookupUserAction(email=target.email))

        assert await _records(silent_reads_harness) == []

    async def test_a_miss_is_an_error_on_no_entity(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """record-2."""
        missing = _missing_email()

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(GenericBadRequest):
                await _processor(harness).run(LookupUserAction(email=missing))

        records = await _records(harness)
        assert [(r.entity_id, r.status, r.lookup_kind, r.lookup_key) for r in records] == [
            (None, OperationStatus.ERROR, "user_email", f"email={missing}")
        ]

    async def test_a_denial_is_recorded_on_the_resolved_entity(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """record-3."""
        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(GenericBadRequest):
                await _processor(harness).run(LookupUserAction(email=target.email))

        records = await _records(harness)
        assert [((r.entity_type, r.entity_id), r.status) for r in records] == [
            (entity_key(target.user_id), OperationStatus.DENIED)
        ]

    async def test_the_two_causes_are_recorded_apart(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """record-4: the audit table has no error_code column, so the run results carry it."""
        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(GenericBadRequest):
                await _processor(harness).run(LookupUserAction(email=_missing_email()))
            with pytest.raises(GenericBadRequest):
                await _processor(harness).run(LookupUserAction(email=target.email))

        missed, denied = harness.lookup_results
        assert (missed.status, denied.status) == (OperationStatus.ERROR, OperationStatus.DENIED)
        assert missed.error_code != denied.error_code
        assert "No UserRow matches the given key" in missed.description
        assert str(target.user_id) in denied.description
        records = await _records(harness)
        assert sorted(r.status for r in records) == sorted([
            OperationStatus.ERROR,
            OperationStatus.DENIED,
        ])

    @ANONYMOUS_RECORDED_AS_ERROR
    async def test_an_anonymous_caller_is_denied_on_no_entity(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """record-5."""
        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError):
                await _processor(harness).run(LookupUserAction(email=target.email))

        records = await _records(harness)
        assert [(r.entity_id, r.status, r.lookup_key) for r in records] == [
            (None, OperationStatus.DENIED, f"email={target.email}")
        ]

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        harness: OpsHarness,
        actors: Actors,
        target: _Target,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-6."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(LookupUserAction(email=target.email))

        records = await _records(harness)
        assert [r.status for r in records] == [OperationStatus.ERROR]


class TestResult:
    async def test_the_resolved_id_is_the_entity(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(LookupUserAction(email=target.email))

        assert result.resolved_entity_id == target.user_id
        assert result.entity_id() == target.user_id
