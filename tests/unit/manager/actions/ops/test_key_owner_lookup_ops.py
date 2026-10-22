"""``key_owner_lookup_ops``: an access key resolved into the user owning its keypair.

target-1 is not applicable: every wired key is a primary key. The keypair access key, the
kernel id, the auto-scaling rule id and the replica (routing) id.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerByKeyOpsAction
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.endpoint.row import EndpointAutoScalingRuleRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupAutoScalingRuleDeploymentAction,
)
from ai.backend.manager.services.resource_slot.actions.lookup_kernel_owner import (
    LookupKernelOwnerAction,
)
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupKeypairOwnerByAccessKeyAction,
)
from ai.backend.testutils.db import with_tables
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
    owner_id: UserID
    keypair_id: KeyPairID
    access_key: AccessKey


class _Disconnected(Exception):
    pass


@pytest.fixture
async def target(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> _Target:
    """A keypair of a user the granted actor may read."""
    owner_id = UserID(uuid.uuid4())
    keypair_id = KeyPairID(uuid.uuid4())
    access_key = AccessKey(f"AK{owner_id.hex[:16]}")
    suffix = owner_id.hex[:8]
    async with ops_db.begin_session() as sess:
        sess.add(
            UserResourcePolicyRow(
                name=f"owner-policy-{suffix}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
        )
        sess.add(
            KeyPairResourcePolicyRow(
                name=f"keypair-policy-{suffix}",
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=1,
                max_concurrent_sftp_sessions=1,
                max_containers_per_session=1,
                idle_timeout=3600,
            )
        )
        await sess.flush()
        sess.add(
            UserRow(
                uuid=owner_id,
                username=f"owner-{suffix}",
                email=f"owner-{suffix}@test.com",
                resource_policy=f"owner-policy-{suffix}",
                status=UserStatus.ACTIVE,
                need_password_change=False,
                sudo_session_enabled=False,
                domain_name=actors.domain_name,
                domain_id=actors.domain_id,
                role=UserRole.USER,
            )
        )
        await sess.flush()
        sess.add(
            KeyPairRow(
                id=keypair_id,
                user=owner_id,
                access_key=access_key,
                secret_key=SecretValue("test-secret"),
                is_active=True,
                is_admin=False,
                resource_policy=f"keypair-policy-{suffix}",
                rate_limit=1000,
            )
        )
        await sess.commit()
    await provision(ops_db, UserEntityType(), owner_id)
    await grant(
        ops_db,
        actors.user_id(Actor.GRANTED),
        UserEntityType(),
        owner_id,
        UserEntityType(),
        Permission.READ,
    )
    return _Target(owner_id=owner_id, keypair_id=keypair_id, access_key=access_key)


@pytest.fixture
async def rule_db(ops_db: ExtendedAsyncSAEngine) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """The auto-scaling rule table, which the base tables leave out."""
    async with with_tables(
        ops_db,
        [PrometheusQueryPresetCategoryRow, PrometheusQueryPresetRow, EndpointAutoScalingRuleRow],
    ):
        yield ops_db


_OTHER_KEYS = [
    pytest.param(
        LookupKernelOwnerAction(kernel_id=KernelID(uuid.uuid4())),
        SessionID(uuid.uuid4()),
        id="target-2-kernel-owner",
    ),
    pytest.param(
        LookupAutoScalingRuleDeploymentAction(rule_id=uuid.uuid4()),
        DeploymentID(uuid.uuid4()),
        id="target-2-auto-scaling-rule",
    ),
]


def _processor(harness: OpsHarness) -> Any:
    return harness.group(UserEntityType()).key_owner_lookup_ops(LookupKeypairOwnerByAccessKeyAction)


def _missing_key() -> AccessKey:
    return AccessKey(f"AKMISS{uuid.uuid4().hex[:12]}")


def _action(access_key: AccessKey) -> LookupKeypairOwnerByAccessKeyAction:
    return LookupKeypairOwnerByAccessKeyAction(access_key=access_key)


async def _records(harness: OpsHarness) -> list[AuditRecord]:
    return await harness.audit(LookupKeypairOwnerByAccessKeyAction.action_name())


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced", "exists", "error"),
        [
            pytest.param(Actor.SUPERADMIN, True, True, None, id="actor-2"),
            pytest.param(Actor.SUPERADMIN, True, False, FieldNotFoundError, id="actor-3"),
            pytest.param(Actor.GRANTED, True, True, None, id="actor-4"),
            pytest.param(Actor.GRANTED, True, False, GenericBadRequest, id="actor-5"),
            pytest.param(Actor.UNGRANTED, True, True, GenericBadRequest, id="actor-6"),
            pytest.param(Actor.MONITOR, True, True, None, id="actor-7", marks=MONITOR_READ_REFUSED),
            pytest.param(
                Actor.MONITOR,
                True,
                False,
                FieldNotFoundError,
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
        action = _action(target.access_key if exists else _missing_key())

        with actors.acting_as(actor):
            if error is None:
                result = await _processor(harness).run(action)
                assert result.owner_entity_id == target.owner_id
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
        reads = repository_calls("field_owner_by_key")

        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(_action(target.access_key))

        assert_refused(raised.value)
        assert reads == []


class TestTarget:
    async def test_a_miss_and_a_denial_carry_neither_the_key_nor_the_id(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """target-2: the two answers are one answer, naming nothing the caller gave or got."""
        missing = _missing_key()

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(GenericBadRequest) as missing_error:
                await _processor(harness).run(_action(missing))
            with pytest.raises(GenericBadRequest) as denied_error:
                await _processor(harness).run(_action(target.access_key))

        assert str(missing_error.value) == str(denied_error.value)
        assert missing_error.value.status_code == denied_error.value.status_code
        assert missing_error.value.error_code() == denied_error.value.error_code()
        for message in (str(missing_error.value), str(denied_error.value)):
            assert missing not in message
            assert target.access_key not in message
            assert str(target.owner_id) not in message

    @pytest.mark.parametrize(("action", "owner_id"), _OTHER_KEYS)
    async def test_other_keys_merge_a_miss_and_a_denial(
        self,
        harness: OpsHarness,
        actors: Actors,
        rule_db: ExtendedAsyncSAEngine,
        monkeypatch: pytest.MonkeyPatch,
        action: LookupFieldOwnerByKeyOpsAction[Any],
        owner_id: EntityIdentifier,
    ) -> None:
        """target-2 over the other wired keys; the denial resolves to an owner nobody granted."""
        processor = harness.group(action.entity_type()).key_owner_lookup_ops(type(action))

        async def resolved(*_: Any, **__: Any) -> EntityIdentifier:
            return owner_id

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(GenericBadRequest) as missing_error:
                await processor.run(action)
            monkeypatch.setattr(OpsRepository, "field_owner_by_key", resolved)
            with pytest.raises(GenericBadRequest) as denied_error:
                await processor.run(action)

        assert str(missing_error.value) == str(denied_error.value)
        assert missing_error.value.status_code == denied_error.value.status_code
        assert str(owner_id) not in str(denied_error.value)
        assert [r.status for r in harness.lookup_results] == [
            OperationStatus.ERROR,
            OperationStatus.DENIED,
        ]

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

        monkeypatch.setattr(V2ReadOps, "lookup_field_owner_by_key", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(_Disconnected):
                await _processor(harness).run(_action(target.access_key))

        records = await _records(harness)
        assert [(r.entity_id, r.status) for r in records] == [(None, OperationStatus.ERROR)]


class TestRecord:
    async def test_a_success_is_recorded_on_the_owner_with_the_key(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """record-1."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_action(target.access_key))

        records = await _records(harness)
        assert [
            ((r.entity_type, r.entity_id), r.operation, r.status, r.lookup_kind, r.lookup_key)
            for r in records
        ] == [
            (
                entity_key(target.owner_id),
                ActionOperationType.LOOKUP,
                OperationStatus.SUCCESS,
                "keypair_access_key",
                f"access_key={target.access_key}",
            )
        ]

    async def test_a_success_is_not_recorded_unless_opted_in(
        self, silent_reads_harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """record-1, with the read left out of the policy."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(_action(target.access_key))

        assert await _records(silent_reads_harness) == []

    async def test_a_miss_is_an_error_on_no_entity(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """record-2."""
        missing = _missing_key()

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(GenericBadRequest):
                await _processor(harness).run(_action(missing))

        records = await _records(harness)
        assert [(r.entity_id, r.status, r.lookup_kind, r.lookup_key) for r in records] == [
            (None, OperationStatus.ERROR, "keypair_access_key", f"access_key={missing}")
        ]

    async def test_a_denial_is_recorded_on_the_owner(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """record-3."""
        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(GenericBadRequest):
                await _processor(harness).run(_action(target.access_key))

        records = await _records(harness)
        assert [((r.entity_type, r.entity_id), r.status) for r in records] == [
            (entity_key(target.owner_id), OperationStatus.DENIED)
        ]

    async def test_the_two_causes_are_recorded_apart(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """record-4: the audit table has no error_code column, so the run results carry it."""
        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(GenericBadRequest):
                await _processor(harness).run(_action(_missing_key()))
            with pytest.raises(GenericBadRequest):
                await _processor(harness).run(_action(target.access_key))

        missed, denied = harness.lookup_results
        assert (missed.status, denied.status) == (OperationStatus.ERROR, OperationStatus.DENIED)
        assert missed.error_code != denied.error_code
        assert "No field row matches the given key" in missed.description
        assert str(target.owner_id) in denied.description
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
                await _processor(harness).run(_action(target.access_key))

        records = await _records(harness)
        assert [(r.entity_id, r.status, r.lookup_key) for r in records] == [
            (None, OperationStatus.DENIED, f"access_key={target.access_key}")
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
                await _processor(harness).run(_action(target.access_key))

        records = await _records(harness)
        assert [r.status for r in records] == [OperationStatus.ERROR]


class TestResult:
    async def test_the_owner_id_is_the_user(
        self, harness: OpsHarness, actors: Actors, target: _Target
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_action(target.access_key))

        assert result.owner_entity_id == target.owner_id
