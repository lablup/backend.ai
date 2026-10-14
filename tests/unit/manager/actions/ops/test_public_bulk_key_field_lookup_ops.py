"""``public_bulk_key_field_lookup_ops``: several access keys resolved into keypairs and owners.

target-1 is not applicable: the one wired action keys on the keypair access key, a primary key.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.services.user.actions.bulk_lookup_keypairs import BulkLookupKeypairsAction
from ai.backend.manager.services.user.actions.lookup_keypair_owner import KeypairAccessKeyLookupKey
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    Actor,
    Actors,
    AuditRecord,
    OpsHarness,
    assert_refused,
    entity_key,
    provision,
)

_EVERY_CALLER = [
    pytest.param(Actor.SUPERADMIN, True, id="superadmin"),
    pytest.param(Actor.MONITOR, True, id="monitor"),
    pytest.param(Actor.GRANTED, True, id="granted"),
    pytest.param(Actor.UNGRANTED, True, id="ungranted"),
    pytest.param(Actor.UNGRANTED, False, id="rbac-off"),
]


@dataclass(frozen=True)
class _Keypair:
    owner_id: UserID
    keypair_id: KeyPairID
    access_key: AccessKey


@pytest.fixture
async def keypairs(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> tuple[_Keypair, _Keypair]:
    """Two keypairs, each of its own user; no actor is granted on either user."""
    seeded = tuple(
        _Keypair(UserID(uuid.uuid4()), KeyPairID(uuid.uuid4()), _missing_key()) for _ in range(2)
    )
    async with ops_db.begin_session() as sess:
        for keypair in seeded:
            suffix = keypair.owner_id.hex[:8]
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
        for keypair in seeded:
            suffix = keypair.owner_id.hex[:8]
            sess.add(
                UserRow(
                    uuid=keypair.owner_id,
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
        for keypair in seeded:
            suffix = keypair.owner_id.hex[:8]
            sess.add(
                KeyPairRow(
                    id=keypair.keypair_id,
                    user=keypair.owner_id,
                    access_key=keypair.access_key,
                    secret_key=SecretValue("test-secret"),
                    is_active=True,
                    is_admin=False,
                    resource_policy=f"keypair-policy-{suffix}",
                    rate_limit=1000,
                )
            )
        await sess.commit()
    for keypair in seeded:
        await provision(ops_db, UserEntityType(), keypair.owner_id)
    first, second = seeded
    return first, second


def _processor(harness: OpsHarness) -> Any:
    return harness.group(UserEntityType()).public_bulk_key_field_lookup_ops(
        BulkLookupKeypairsAction
    )


def _missing_key() -> AccessKey:
    return AccessKey(f"AK{uuid.uuid4().hex[:18]}")


def _action(*access_keys: AccessKey) -> BulkLookupKeypairsAction:
    return BulkLookupKeypairsAction(access_keys=list(access_keys))


async def _records(harness: OpsHarness) -> list[AuditRecord]:
    return await harness.audit(BulkLookupKeypairsAction.action_name())


class TestActor:
    @ANONYMOUS_NOT_REFUSED
    async def test_an_anonymous_caller_is_refused_before_running(
        self,
        harness: OpsHarness,
        actors: Actors,
        keypairs: tuple[_Keypair, _Keypair],
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """actor-1."""
        reads = repository_calls("fields_by_keys")

        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(_action(*(k.access_key for k in keypairs)))

        assert_refused(raised.value)
        assert reads == []

    @pytest.mark.parametrize(("actor", "enforced"), _EVERY_CALLER)
    async def test_every_caller_gets_an_answer_per_key(
        self,
        harness: OpsHarness,
        actors: Actors,
        keypairs: tuple[_Keypair, _Keypair],
        actor: Actor,
        enforced: bool,
    ) -> None:
        """actor-2: the owners are not checked here; the partial read that follows is."""
        harness.enforce(enforced)
        first, second = keypairs

        with actors.acting_as(actor):
            result = await _processor(harness).run(_action(first.access_key, second.access_key))

        assert [(r.status, r.entity_id) for r in result.key_results()] == [
            (OperationStatus.SUCCESS, first.owner_id),
            (OperationStatus.SUCCESS, second.owner_id),
        ]


class TestMulti:
    async def test_only_the_missing_key_fails(
        self, harness: OpsHarness, actors: Actors, keypairs: tuple[_Keypair, _Keypair]
    ) -> None:
        """multi-1."""
        first, second = keypairs

        with actors.acting_as(Actor.UNGRANTED):
            result = await _processor(harness).run(
                _action(first.access_key, _missing_key(), second.access_key)
            )

        assert [(r.status, r.entity_id) for r in result.key_results()] == [
            (OperationStatus.SUCCESS, first.owner_id),
            (OperationStatus.ERROR, None),
            (OperationStatus.SUCCESS, second.owner_id),
        ]

    async def test_no_keys_is_an_empty_success(
        self, harness: OpsHarness, actors: Actors, keypairs: tuple[_Keypair, _Keypair]
    ) -> None:
        """multi-3."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_action())

        assert list(result.key_results()) == []
        assert dict(result.resolved) == {}

    async def test_the_answers_follow_the_order_given(
        self, harness: OpsHarness, actors: Actors, keypairs: tuple[_Keypair, _Keypair]
    ) -> None:
        """multi-4."""
        first, second = keypairs
        keys = [second.access_key, _missing_key(), first.access_key, second.access_key]

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_action(*keys))

        assert [r.key for r in result.key_results()] == [
            KeypairAccessKeyLookupKey(key) for key in keys
        ]


class TestRecord:
    async def test_each_resolved_key_is_recorded_on_its_owner(
        self, harness: OpsHarness, actors: Actors, keypairs: tuple[_Keypair, _Keypair]
    ) -> None:
        """record-1."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_action(*(k.access_key for k in keypairs)))

        records = await _records(harness)
        assert sorted(
            ((r.entity_type, r.entity_id), r.operation, r.status, r.lookup_key) for r in records
        ) == sorted([
            (
                entity_key(keypair.owner_id),
                ActionOperationType.LOOKUP,
                OperationStatus.SUCCESS,
                f"access_key={keypair.access_key}",
            )
            for keypair in keypairs
        ])

    async def test_a_missing_key_is_an_error_on_no_entity(
        self, silent_reads_harness: OpsHarness, actors: Actors, keypairs: tuple[_Keypair, _Keypair]
    ) -> None:
        """record-2: resolved keys are left out by the policy, so the miss stands alone."""
        first, _ = keypairs
        missing = _missing_key()

        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(_action(first.access_key, missing))

        records = await _records(silent_reads_harness)
        assert [(r.entity_id, r.status, r.lookup_key) for r in records] == [
            (None, OperationStatus.ERROR, f"access_key={missing}")
        ]

    @ANONYMOUS_RECORDED_AS_ERROR
    async def test_an_anonymous_caller_is_denied_per_key_on_no_entity(
        self, harness: OpsHarness, actors: Actors, keypairs: tuple[_Keypair, _Keypair]
    ) -> None:
        """record-3."""
        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError):
                await _processor(harness).run(_action(*(k.access_key for k in keypairs)))

        records = await _records(harness)
        assert sorted((r.entity_id, r.status, r.lookup_key or "") for r in records) == sorted(
            (None, OperationStatus.DENIED, f"access_key={k.access_key}") for k in keypairs
        )


class TestResult:
    async def test_the_mapping_names_the_rows_and_the_answers_name_the_owners(
        self, harness: OpsHarness, actors: Actors, keypairs: tuple[_Keypair, _Keypair]
    ) -> None:
        """result-1."""
        first, second = keypairs

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                _action(first.access_key, _missing_key(), second.access_key)
            )

        assert dict(result.resolved) == {
            first.access_key: first.keypair_id,
            second.access_key: second.keypair_id,
        }
        assert [r.entity_id for r in result.key_results()] == [
            first.owner_id,
            None,
            second.owner_id,
        ]
