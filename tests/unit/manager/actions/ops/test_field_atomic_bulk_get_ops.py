"""``atomic_bulk_get_ops``: the default keypair of each named user.

target-2 (two designated rows for one owner) has no row here: ``uq_keypairs_is_default``
and ``uq_deployment_policies_endpoint`` cap both specs of this shape at one row.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.keypair import KeyPairFieldType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.services.user.actions.keypair_ops import GetDefaultKeypairsAction
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupBulkKeypairOwnerAction,
    LookupKeypairOwnerAction,
)
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    MONITOR_READ_REFUSED,
    Actor,
    Actors,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    provision,
)


@dataclass(frozen=True)
class _Owners:
    """Users the granted actor may read, one it may not, and their default access keys."""

    first: UserID
    second: UserID
    without_default: UserID
    hidden: UserID
    default_keys: dict[UserID, AccessKey]


def _access_key() -> AccessKey:
    return AccessKey(f"AKTEST{uuid.uuid4().hex[:14].upper()}")


async def _seed_owner(
    db: ExtendedAsyncSAEngine, actors: Actors, policies: tuple[str, str], *, default: bool
) -> tuple[UserID, AccessKey]:
    """A user in the actors' domain with a non-default keypair and, if asked, a default one."""
    user_id = UserID(uuid.uuid4())
    user_policy, keypair_policy = policies
    default_key = _access_key()
    async with db.begin_session() as sess:
        sess.add(
            UserRow(
                uuid=user_id,
                username=f"owner-{user_id.hex[:8]}",
                email=f"owner-{user_id.hex[:8]}@test.com",
                resource_policy=user_policy,
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
                access_key=_access_key(),
                secret_key=SecretValue("secret"),
                user=user_id,
                is_active=True,
                is_default=False,
                resource_policy=keypair_policy,
            )
        )
        if default:
            sess.add(
                KeyPairRow(
                    access_key=default_key,
                    secret_key=SecretValue("secret"),
                    user=user_id,
                    is_active=True,
                    is_default=True,
                    resource_policy=keypair_policy,
                )
            )
        await sess.commit()
    await provision(db, UserEntityType(), user_id, [(DomainEntityType(), actors.domain_id)])
    return user_id, default_key


@pytest.fixture
async def owners(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> _Owners:
    suffix = uuid.uuid4().hex[:8]
    policies = (f"owner-user-policy-{suffix}", f"owner-keypair-policy-{suffix}")
    async with ops_db.begin_session() as sess:
        sess.add(
            UserResourcePolicyRow(
                name=policies[0],
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
        )
        sess.add(
            KeyPairResourcePolicyRow(
                name=policies[1],
                total_resource_slots=ResourceSlot(),
                max_concurrent_sessions=1,
                max_concurrent_sftp_sessions=1,
                max_containers_per_session=1,
                idle_timeout=0,
            )
        )
        await sess.commit()
    first, first_key = await _seed_owner(ops_db, actors, policies, default=True)
    second, second_key = await _seed_owner(ops_db, actors, policies, default=True)
    without_default, _ = await _seed_owner(ops_db, actors, policies, default=False)
    hidden, hidden_key = await _seed_owner(ops_db, actors, policies, default=True)
    for user_id in (first, second, without_default):
        await grant(
            ops_db,
            actors.user_id(Actor.GRANTED),
            UserEntityType(),
            user_id,
            UserEntityType(),
            Permission.READ,
        )
    return _Owners(
        first=first,
        second=second,
        without_default=without_default,
        hidden=hidden,
        default_keys={first: first_key, second: second_key, hidden: hidden_key},
    )


def _processor(harness: OpsHarness) -> Any:
    keypair_group = harness.group(UserEntityType()).field_group(
        FieldGroupMeta(KeyPairFieldType()),
        KeyPairData,
        LookupKeypairOwnerAction,
        LookupBulkKeypairOwnerAction,
    )
    return keypair_group.atomic_bulk_get_ops(GetDefaultKeypairsAction)


def _designated_keys(result: Any) -> dict[UserID, AccessKey]:
    return {owner: data.access_key for owner, data in result.designated.items()}


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced", "error"),
        [
            pytest.param(Actor.SUPERADMIN, True, None, id="actor-1"),
            pytest.param(Actor.MONITOR, True, None, id="actor-2", marks=MONITOR_READ_REFUSED),
            pytest.param(Actor.GRANTED, True, None, id="actor-3"),
            pytest.param(Actor.UNGRANTED, True, NotEnoughPermission, id="actor-4"),
            pytest.param(
                Actor.ANONYMOUS, True, BackendAIError, id="actor-5", marks=ANONYMOUS_NOT_REFUSED
            ),
            pytest.param(
                Actor.ANONYMOUS,
                False,
                BackendAIError,
                id="actor-5-rbac-off",
                marks=ANONYMOUS_NOT_REFUSED,
            ),
            pytest.param(Actor.UNGRANTED, False, None, id="actor-6"),
        ],
    )
    async def test_actor(
        self,
        harness: OpsHarness,
        actors: Actors,
        owners: _Owners,
        repository_calls: Callable[[str], list[Any]],
        actor: Actor,
        enforced: bool,
        error: type[Exception] | None,
    ) -> None:
        harness.enforce(enforced)
        action = GetDefaultKeypairsAction(user_ids=[owners.first, owners.second])
        reads = repository_calls("owned_fields")

        with actors.acting_as(actor):
            if error is None:
                result = await _processor(harness).run(action)
                assert set(result.designated) == {owners.first, owners.second}
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(action)
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)
                assert reads == []


class TestMulti:
    async def test_one_unreadable_owner_refuses_all(
        self,
        harness: OpsHarness,
        actors: Actors,
        owners: _Owners,
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """multi-1."""
        action = GetDefaultKeypairsAction(user_ids=[owners.first, owners.hidden])
        reads = repository_calls("owned_fields")

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(action)

        assert reads == []

    async def test_an_owner_named_twice_reads_as_once(
        self, harness: OpsHarness, actors: Actors, owners: _Owners
    ) -> None:
        """multi-2."""
        with actors.acting_as(Actor.GRANTED):
            once = await _processor(harness).run(GetDefaultKeypairsAction(user_ids=[owners.first]))
            twice = await _processor(harness).run(
                GetDefaultKeypairsAction(user_ids=[owners.first, owners.first])
            )

        assert _designated_keys(twice) == _designated_keys(once)

    async def test_no_owner_is_an_empty_result(
        self, harness: OpsHarness, actors: Actors, owners: _Owners
    ) -> None:
        """multi-3."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(GetDefaultKeypairsAction(user_ids=[]))

        assert dict(result.designated) == {}


class TestTarget:
    async def test_an_owner_designating_nothing_is_left_out(
        self, harness: OpsHarness, actors: Actors, owners: _Owners
    ) -> None:
        """target-1."""
        action = GetDefaultKeypairsAction(user_ids=[owners.first, owners.without_default])

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(action)

        assert _designated_keys(result) == {owners.first: owners.default_keys[owners.first]}

    async def test_superadmin_missing_owner_is_left_out(
        self, harness: OpsHarness, actors: Actors, owners: _Owners
    ) -> None:
        """target-3."""
        action = GetDefaultKeypairsAction(user_ids=[owners.first, UserID(uuid.uuid4())])

        with actors.acting_as(Actor.SUPERADMIN):
            result = await _processor(harness).run(action)

        assert _designated_keys(result) == {owners.first: owners.default_keys[owners.first]}

    async def test_user_missing_owner_is_refused(
        self,
        harness: OpsHarness,
        actors: Actors,
        owners: _Owners,
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """target-4."""
        action = GetDefaultKeypairsAction(user_ids=[owners.first, UserID(uuid.uuid4())])
        reads = repository_calls("owned_fields")

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(NotEnoughPermission):
                await _processor(harness).run(action)

        assert reads == []


class TestRecord:
    @pytest.mark.parametrize(
        ("actor", "hidden", "status", "error"),
        [
            pytest.param(Actor.GRANTED, False, OperationStatus.SUCCESS, None, id="record-1"),
            pytest.param(
                Actor.GRANTED, True, OperationStatus.DENIED, NotEnoughPermission, id="record-2"
            ),
            pytest.param(
                Actor.ANONYMOUS,
                False,
                OperationStatus.DENIED,
                BackendAIError,
                id="record-4",
                marks=ANONYMOUS_RECORDED_AS_ERROR,
            ),
        ],
    )
    async def test_one_row_per_owner(
        self,
        harness: OpsHarness,
        actors: Actors,
        owners: _Owners,
        actor: Actor,
        hidden: bool,
        status: OperationStatus,
        error: type[Exception] | None,
    ) -> None:
        user_ids = [owners.first, owners.hidden if hidden else owners.second]
        action = GetDefaultKeypairsAction(user_ids=user_ids)

        with actors.acting_as(actor):
            if error is None:
                await _processor(harness).run(action)
            else:
                with pytest.raises(error) as raised:
                    await _processor(harness).run(action)
                if actor is Actor.ANONYMOUS:
                    assert_refused(raised.value)

        records = await harness.audit(GetDefaultKeypairsAction.action_name())
        assert sorted(((r.entity_type, r.entity_id), r.operation, r.status) for r in records) == (
            sorted((entity_key(user_id), ActionOperationType.GET, status) for user_id in user_ids)
        )

    async def test_an_execution_failure_is_an_error_per_owner(
        self,
        harness: OpsHarness,
        actors: Actors,
        owners: _Owners,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-3, with the read failing after the check passed."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the read failed")

        monkeypatch.setattr(OpsRepository, "owned_fields", broken)
        user_ids = [owners.first, owners.second]

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(GetDefaultKeypairsAction(user_ids=user_ids))

        records = await harness.audit(GetDefaultKeypairsAction.action_name())
        assert sorted(((r.entity_type, r.entity_id), r.status) for r in records) == sorted(
            (entity_key(user_id), OperationStatus.ERROR) for user_id in user_ids
        )

    async def test_a_read_is_not_recorded_unless_opted_in(
        self, silent_reads_harness: OpsHarness, actors: Actors, owners: _Owners
    ) -> None:
        """record-1, with the read left out of the policy."""
        action = GetDefaultKeypairsAction(user_ids=[owners.first, owners.second])

        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(action)

        assert await silent_reads_harness.audit(GetDefaultKeypairsAction.action_name()) == []

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        harness: OpsHarness,
        actors: Actors,
        owners: _Owners,
        monkeypatch: pytest.MonkeyPatch,
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """record-5."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)
        reads = repository_calls("owned_fields")

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(GetDefaultKeypairsAction(user_ids=[owners.first]))

        assert reads == []

        records = await harness.audit(GetDefaultKeypairsAction.action_name())
        assert [r.status for r in records] == [OperationStatus.ERROR]


class TestResult:
    async def test_each_owner_maps_to_its_default_keypair(
        self, harness: OpsHarness, actors: Actors, owners: _Owners
    ) -> None:
        """result-1."""
        action = GetDefaultKeypairsAction(user_ids=[owners.first, owners.second])

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(action)

        assert _designated_keys(result) == {
            owners.first: owners.default_keys[owners.first],
            owners.second: owners.default_keys[owners.second],
        }
        for owner, data in result.designated.items():
            assert data.user_id == owner
            assert data.is_default is True
