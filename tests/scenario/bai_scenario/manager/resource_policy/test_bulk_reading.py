"""정책 여럿을 id 로 읽기 — 자리마다 따로 답한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.resource_policy import (
    FAMILIES,
    APolicyAndACaller,
    APolicyAndSomeone,
    Family,
    TheOnlyLoadedPolicy,
    TheOnlyTargetIsRefused,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[Any]
type ReadingStep = Scenario[
    TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Loaded
]


@dataclass(frozen=True)
class ReadingTheId(When[APolicyAndACaller[Any], ResourcePolicyAdapter, Loaded]):
    """미리 만들어 둔 정책을 id 로 읽는다."""

    family: Family[Any, Any]

    @override
    def operation(self) -> str:
        return self.family.calls.bulk_get

    @override
    def describe(self, laid: APolicyAndACaller[Any]) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.policy.name}의 id 로 여럿을 읽습니다",
            english=f"{laid.caller.username} reads several by the id of {laid.policy.name}",
        )

    @override
    async def call(self, adapter: ResourcePolicyAdapter, laid: APolicyAndACaller[Any]) -> Loaded:
        ids: list[UUID] = [laid.policy.uuid]
        with ActingAs(laid.caller):
            return await self.family.bulk_get(adapter, ids)


@dataclass(frozen=True)
class AUserReadingPoliciesReadsById(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Loaded]
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"a-user-reading-policies-reads-a-{self.family.label}-by-id"

    @override
    def describe(self) -> str:
        return Says(
            f"public 에서 그 정책을 읽을 수 있는 사용자가 id 로 {self.family.kind} 하나를 "
            "읽으면, 그 항목에 정책 전체가 응답으로 옵니다",
            english=(
                f"when a user who can read it in public reads one {self.family.label} by id, the "
                "whole policy comes back for that item"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, granted=True)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Loaded]:
        return ReadingTheId(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Loaded]:
        return TheOnlyLoadedPolicy(self.family, self.started)


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedPerId(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Loaded]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-user-granted-nothing-reading-a-{self.family.label}-by-id-is-refused-per-item"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 정책 하나를 id 로 읽으면, 호출은 거부되지 않고 그 "
            "항목이 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing reading one policy by id is not rejected as a call, and "
                "that item is rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Loaded]:
        return ReadingTheId(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Loaded]:
        return TheOnlyTargetIsRefused()


SCENARIOS: list[ReadingStep] = [
    *(AUserReadingPoliciesReadsById(family, started=datetime.now(UTC)) for family in FAMILIES),
    *(AUserGrantedNothingIsRefusedPerId(family) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_bulk_reading(
    scenario: ReadingStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
