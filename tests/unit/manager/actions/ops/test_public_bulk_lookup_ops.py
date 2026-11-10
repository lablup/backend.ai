"""``public_bulk_lookup_ops``: resolving several keys any caller may resolve, with domain names.

target-1 is not applicable, although the bulk read keeps the last of several matches without
detecting them: every wired bulk key is a primary key. Domain and resource group names, agent
ids, and role assignment ids (both role-assignment lookups key on the assignment row id).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.domain.actions.bulk_lookup import BulkLookupDomainsAction
from ai.backend.manager.services.domain.actions.lookup import DomainNameKey
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
    pytest.param(Actor.UNGRANTED, True, id="ungranted"),
    pytest.param(Actor.UNGRANTED, False, id="rbac-off"),
]


@dataclass(frozen=True)
class _Domain:
    id: DomainID
    name: DomainName


@pytest.fixture
async def domains(ops_db: ExtendedAsyncSAEngine) -> tuple[_Domain, _Domain]:
    """Two domains, each with its node."""
    seeded = tuple(_Domain(DomainID(uuid.uuid4()), _missing_name()) for _ in range(2))
    async with ops_db.begin_session() as sess:
        sess.add_all([
            DomainRow(id=domain.id, name=domain.name, total_resource_slots=ResourceSlot())
            for domain in seeded
        ])
        await sess.commit()
    for domain in seeded:
        await provision(ops_db, DomainEntityType(), domain.id)
    first, second = seeded
    return first, second


def _processor(harness: OpsHarness) -> Any:
    return harness.group(DomainEntityType()).public_bulk_lookup_ops(BulkLookupDomainsAction)


def _missing_name() -> DomainName:
    return DomainName(f"domain-{uuid.uuid4().hex[:8]}")


async def _records(harness: OpsHarness) -> list[AuditRecord]:
    return await harness.audit(BulkLookupDomainsAction.action_name())


class TestActor:
    @ANONYMOUS_NOT_REFUSED
    async def test_an_anonymous_caller_is_refused_before_running(
        self,
        harness: OpsHarness,
        actors: Actors,
        domains: tuple[_Domain, _Domain],
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """actor-1."""
        reads = repository_calls("bulk_lookup")

        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(
                    BulkLookupDomainsAction(names=[domain.name for domain in domains])
                )

        assert_refused(raised.value)
        assert reads == []

    @pytest.mark.parametrize(("actor", "enforced"), _EVERY_CALLER)
    async def test_every_caller_gets_an_answer_per_key(
        self,
        harness: OpsHarness,
        actors: Actors,
        domains: tuple[_Domain, _Domain],
        actor: Actor,
        enforced: bool,
    ) -> None:
        """actor-2."""
        harness.enforce(enforced)
        first, second = domains

        with actors.acting_as(actor):
            result = await _processor(harness).run(
                BulkLookupDomainsAction(names=[first.name, second.name])
            )

        assert [(r.status, r.entity_id) for r in result.key_results()] == [
            (OperationStatus.SUCCESS, first.id),
            (OperationStatus.SUCCESS, second.id),
        ]


class TestMulti:
    async def test_only_the_missing_key_fails(
        self, harness: OpsHarness, actors: Actors, domains: tuple[_Domain, _Domain]
    ) -> None:
        """multi-1."""
        first, second = domains

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                BulkLookupDomainsAction(names=[first.name, _missing_name(), second.name])
            )

        assert [(r.status, r.entity_id) for r in result.key_results()] == [
            (OperationStatus.SUCCESS, first.id),
            (OperationStatus.ERROR, None),
            (OperationStatus.SUCCESS, second.id),
        ]

    async def test_a_repeated_key_is_answered_the_same_at_every_position(
        self, harness: OpsHarness, actors: Actors, domains: tuple[_Domain, _Domain]
    ) -> None:
        """multi-2."""
        first, _ = domains
        missing = _missing_name()

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                BulkLookupDomainsAction(names=[first.name, missing, first.name, missing])
            )

        assert [(r.key, r.status, r.entity_id) for r in result.key_results()] == [
            (DomainNameKey(name=first.name), OperationStatus.SUCCESS, first.id),
            (DomainNameKey(name=missing), OperationStatus.ERROR, None),
            (DomainNameKey(name=first.name), OperationStatus.SUCCESS, first.id),
            (DomainNameKey(name=missing), OperationStatus.ERROR, None),
        ]

    async def test_no_keys_is_an_empty_success(
        self, harness: OpsHarness, actors: Actors, domains: tuple[_Domain, _Domain]
    ) -> None:
        """multi-3."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(BulkLookupDomainsAction(names=[]))

        assert list(result.key_results()) == []
        assert dict(result.resolved) == {}

    async def test_the_answers_follow_the_order_given(
        self, harness: OpsHarness, actors: Actors, domains: tuple[_Domain, _Domain]
    ) -> None:
        """multi-4."""
        first, second = domains
        missing = _missing_name()
        names = [second.name, missing, first.name]

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(BulkLookupDomainsAction(names=names))

        assert [r.key for r in result.key_results()] == [DomainNameKey(name=n) for n in names]


class TestRecord:
    async def test_each_resolved_key_is_recorded_on_its_entity(
        self, harness: OpsHarness, actors: Actors, domains: tuple[_Domain, _Domain]
    ) -> None:
        """record-1."""
        first, second = domains

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(BulkLookupDomainsAction(names=[first.name, second.name]))

        records = await _records(harness)
        assert sorted(
            ((r.entity_type, r.entity_id), r.operation, r.status, r.lookup_key) for r in records
        ) == sorted([
            (
                entity_key(domain.id),
                ActionOperationType.LOOKUP,
                OperationStatus.SUCCESS,
                f"name={domain.name}",
            )
            for domain in domains
        ])

    async def test_a_resolved_key_is_not_recorded_unless_opted_in(
        self, silent_reads_harness: OpsHarness, actors: Actors, domains: tuple[_Domain, _Domain]
    ) -> None:
        """record-1, with the read left out of the policy."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(
                BulkLookupDomainsAction(names=[domain.name for domain in domains])
            )

        assert await _records(silent_reads_harness) == []

    async def test_each_missing_key_is_an_error_on_no_entity(
        self, silent_reads_harness: OpsHarness, actors: Actors, domains: tuple[_Domain, _Domain]
    ) -> None:
        """record-2: resolved keys are left out by the policy, so the misses stand alone."""
        first, _ = domains
        missing = sorted([_missing_name(), _missing_name()])

        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(
                BulkLookupDomainsAction(names=[missing[0], first.name, missing[1]])
            )

        records = await _records(silent_reads_harness)
        assert sorted((r.entity_id, r.status, r.lookup_key or "") for r in records) == [
            (None, OperationStatus.ERROR, f"name={name}") for name in missing
        ]

    @ANONYMOUS_RECORDED_AS_ERROR
    async def test_an_anonymous_caller_is_denied_per_key_on_no_entity(
        self, harness: OpsHarness, actors: Actors, domains: tuple[_Domain, _Domain]
    ) -> None:
        """record-3."""
        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError):
                await _processor(harness).run(
                    BulkLookupDomainsAction(names=[domain.name for domain in domains])
                )

        records = await _records(harness)
        assert sorted((r.entity_id, r.status, r.lookup_key or "") for r in records) == sorted(
            (None, OperationStatus.DENIED, f"name={domain.name}") for domain in domains
        )


class TestResult:
    async def test_the_mapping_and_the_per_key_answers(
        self, harness: OpsHarness, actors: Actors, domains: tuple[_Domain, _Domain]
    ) -> None:
        """result-1."""
        first, second = domains
        missing = _missing_name()

        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(
                BulkLookupDomainsAction(names=[first.name, missing, second.name])
            )

        assert dict(result.resolved) == {first.name: first.id, second.name: second.id}
        assert [(r.key, r.status, r.entity_id) for r in result.key_results()] == [
            (DomainNameKey(name=first.name), OperationStatus.SUCCESS, first.id),
            (DomainNameKey(name=missing), OperationStatus.ERROR, None),
            (DomainNameKey(name=second.name), OperationStatus.SUCCESS, second.id),
        ]
