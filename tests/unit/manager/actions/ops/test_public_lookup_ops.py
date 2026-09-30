"""``public_lookup_ops``: resolving one key any caller may resolve, with a domain's name.

target-1 is not applicable: domain, resource group and agent keys are primary keys; project
(domain, name) and artifact registry name are unique. A session's (user, name) is unique
among non-terminal sessions only, but the lookup excludes terminal sessions, so two
terminated sessions of one name resolve to nothing.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType, DomainName
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    ANONYMOUS_RECORDED_AS_ERROR,
    Actor,
    Actors,
    AuditRecord,
    OpsHarness,
    assert_refused,
    entity_key,
)

_EVERY_CALLER = [
    pytest.param(Actor.SUPERADMIN, True, id="superadmin"),
    pytest.param(Actor.MONITOR, True, id="monitor"),
    pytest.param(Actor.UNGRANTED, True, id="ungranted"),
    pytest.param(Actor.UNGRANTED, False, id="rbac-off"),
]


def _processor(harness: OpsHarness) -> Any:
    return harness.group(DomainEntityType()).public_lookup_ops(LookupDomainAction)


def _missing_name() -> DomainName:
    return DomainName(f"nowhere-{uuid.uuid4().hex[:8]}")


async def _records(harness: OpsHarness) -> list[AuditRecord]:
    return await harness.audit(LookupDomainAction.action_name())


class TestActor:
    @ANONYMOUS_NOT_REFUSED
    async def test_an_anonymous_caller_is_refused_before_running(
        self,
        harness: OpsHarness,
        actors: Actors,
        repository_calls: Callable[[str], list[Any]],
    ) -> None:
        """actor-1."""
        reads = repository_calls("lookup")

        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError) as raised:
                await _processor(harness).run(LookupDomainAction(name=actors.domain_name))

        assert_refused(raised.value)
        assert reads == []

    @pytest.mark.parametrize(("actor", "enforced"), _EVERY_CALLER)
    async def test_every_caller_resolves_a_present_key(
        self, harness: OpsHarness, actors: Actors, actor: Actor, enforced: bool
    ) -> None:
        """actor-2."""
        harness.enforce(enforced)

        with actors.acting_as(actor):
            result = await _processor(harness).run(LookupDomainAction(name=actors.domain_name))

        assert result.resolved_entity_id == actors.domain_id

    @pytest.mark.parametrize(("actor", "enforced"), _EVERY_CALLER)
    async def test_every_caller_gets_the_miss_as_is(
        self, harness: OpsHarness, actors: Actors, actor: Actor, enforced: bool
    ) -> None:
        """actor-3."""
        harness.enforce(enforced)

        with actors.acting_as(actor):
            with pytest.raises(EntityNotFoundError):
                await _processor(harness).run(LookupDomainAction(name=_missing_name()))


class TestRecord:
    async def test_a_success_is_recorded_on_the_entity_with_the_key(
        self, harness: OpsHarness, actors: Actors
    ) -> None:
        """record-1."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(LookupDomainAction(name=actors.domain_name))

        records = await _records(harness)
        assert [
            ((r.entity_type, r.entity_id), r.operation, r.status, r.lookup_kind, r.lookup_key)
            for r in records
        ] == [
            (
                entity_key(actors.domain_id),
                ActionOperationType.LOOKUP,
                OperationStatus.SUCCESS,
                "domain_name",
                f"name={actors.domain_name}",
            )
        ]

    async def test_a_success_is_not_recorded_unless_opted_in(
        self, silent_reads_harness: OpsHarness, actors: Actors
    ) -> None:
        """record-1, with the read left out of the policy."""
        with actors.acting_as(Actor.GRANTED):
            await _processor(silent_reads_harness).run(LookupDomainAction(name=actors.domain_name))

        assert await _records(silent_reads_harness) == []

    async def test_a_miss_is_an_error_on_no_entity(
        self, harness: OpsHarness, actors: Actors
    ) -> None:
        """record-2."""
        missing = _missing_name()

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(EntityNotFoundError):
                await _processor(harness).run(LookupDomainAction(name=missing))

        records = await _records(harness)
        assert [(r.entity_id, r.status, r.lookup_kind, r.lookup_key) for r in records] == [
            (None, OperationStatus.ERROR, "domain_name", f"name={missing}")
        ]

    @ANONYMOUS_RECORDED_AS_ERROR
    async def test_an_anonymous_caller_is_denied_on_no_entity(
        self, harness: OpsHarness, actors: Actors
    ) -> None:
        """record-3."""
        with actors.acting_as(Actor.ANONYMOUS):
            with pytest.raises(BackendAIError):
                await _processor(harness).run(LookupDomainAction(name=actors.domain_name))

        records = await _records(harness)
        assert [(r.entity_id, r.status, r.lookup_key) for r in records] == [
            (None, OperationStatus.DENIED, f"name={actors.domain_name}")
        ]


class TestResult:
    async def test_the_resolved_id_is_the_entity(self, harness: OpsHarness, actors: Actors) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(LookupDomainAction(name=actors.domain_name))

        assert result.resolved_entity_id == actors.domain_id
