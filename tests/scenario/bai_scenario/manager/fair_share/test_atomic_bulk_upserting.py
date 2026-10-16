"""도메인 fair share 가중치 여럿 한 번에 정하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.fair_share.request import (
    BulkUpsertDomainFairShareWeightInput,
    DomainWeightEntryInput,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertDomainFairShareWeightPayload,
)
from ai.backend.manager.api.adapters.fair_share.adapter import FairShareAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.fair_share import (
    WEIGHT,
    DomainsInAGroupAndACaller,
    DomainsInAGroupAndSomeone,
    EveryWeightIsWritten,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Upserted = BulkUpsertDomainFairShareWeightPayload
type FairShareStep = Scenario[TestSeedingSession, DomainsInAGroupAndACaller, FairShareAdapter, Any]


@dataclass(frozen=True)
class SettingEveryWeight(When[DomainsInAGroupAndACaller, FairShareAdapter, Upserted]):
    """그룹 안 도메인들의 가중치를 한 번에 정한다."""

    @override
    def operation(self) -> str:
        return "atomic_bulk_upsert_domain"

    @override
    def describe(self, laid: DomainsInAGroupAndACaller) -> str:
        return (
            f"{laid.caller.username}이 {laid.group.name} 안 도메인 {len(laid.domains)}개의 "
            "가중치를 한 번에 정함"
        )

    @override
    async def call(self, adapter: FairShareAdapter, laid: DomainsInAGroupAndACaller) -> Upserted:
        with ActingAs(laid.caller):
            return await adapter.atomic_bulk_upsert_domain(
                BulkUpsertDomainFairShareWeightInput(
                    resource_group_name=laid.group.name,
                    inputs=[
                        DomainWeightEntryInput(domain_name=domain.name, weight=WEIGHT)
                        for domain in laid.domains
                    ],
                )
            )


@dataclass(frozen=True)
class TheSuperadminSetsSeveralWeights(
    Scenario[TestSeedingSession, DomainsInAGroupAndACaller, FairShareAdapter, Upserted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-sets-several-domain-weights-at-once"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 도메인 둘의 가중치를 한 번에 정하면, 둘을 정했다는 개수가 온다"

    @override
    def given(self) -> Given[TestSeedingSession, DomainsInAGroupAndACaller]:
        return DomainsInAGroupAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[DomainsInAGroupAndACaller, FairShareAdapter, Upserted]:
        return SettingEveryWeight()

    @override
    def then(self) -> Then[DomainsInAGroupAndACaller, Upserted]:
        return EveryWeightIsWritten()


@dataclass(frozen=True)
class AUserGrantedUpdateOnTheGroupMayNotSetSeveralWeights(
    Scenario[TestSeedingSession, DomainsInAGroupAndACaller, FairShareAdapter, Upserted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-on-the-group-may-not-set-several-domain-weights"

    @override
    def describe(self) -> str:
        return (
            "그 그룹에 앉힌 역할로 수정 권한을 받은 사용자가 도메인 둘의 가중치를 한 번에 "
            "정하려 하면 권한 부족으로 거부된다. 가중치 쓰기는 그룹이 아니라 전역 대상으로 권한을 본다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, DomainsInAGroupAndACaller]:
        return DomainsInAGroupAndSomeone(granted=Permission.UPDATE, besides=1)

    @override
    def when(self) -> When[DomainsInAGroupAndACaller, FairShareAdapter, Upserted]:
        return SettingEveryWeight()

    @override
    def then(self) -> Then[DomainsInAGroupAndACaller, Upserted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSetSeveralWeights(
    Scenario[TestSeedingSession, DomainsInAGroupAndACaller, FairShareAdapter, Upserted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-set-several-domain-weights"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 도메인 둘의 가중치를 한 번에 정하려 하면 "
            "권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, DomainsInAGroupAndACaller]:
        return DomainsInAGroupAndSomeone(besides=1)

    @override
    def when(self) -> When[DomainsInAGroupAndACaller, FairShareAdapter, Upserted]:
        return SettingEveryWeight()

    @override
    def then(self) -> Then[DomainsInAGroupAndACaller, Upserted]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[FairShareStep] = [
    TheSuperadminSetsSeveralWeights(),
    AUserGrantedUpdateOnTheGroupMayNotSetSeveralWeights(),
    AUserGrantedNothingMayNotSetSeveralWeights(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_atomic_bulk_upserting(
    scenario: FairShareStep, adapter: FairShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
