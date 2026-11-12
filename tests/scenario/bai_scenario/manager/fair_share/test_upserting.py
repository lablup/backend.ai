"""도메인 fair share 가중치 하나 정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.fair_share.request import UpsertDomainFairShareWeightInput
from ai.backend.common.dto.manager.v2.fair_share.response import DomainFairShareNode
from ai.backend.manager.api.adapters.fair_share.adapter import FairShareAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.fair_share import (
    WEIGHT,
    DomainsInAGroupAndACaller,
    DomainsInAGroupAndSomeone,
    TheDomainWeight,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Upserted = DomainFairShareNode
type FairShareStep = Scenario[TestSeedingSession, DomainsInAGroupAndACaller, FairShareAdapter, Any]


@dataclass(frozen=True)
class SettingTheWeight(When[DomainsInAGroupAndACaller, FairShareAdapter, Upserted]):
    """그룹 안 첫 도메인의 가중치를 정한다."""

    @override
    def operation(self) -> str:
        return "upsert_domain"

    @override
    def describe(self, laid: DomainsInAGroupAndACaller) -> str:
        return Says(
            (
                f"{laid.caller.username} 이 {laid.group.name} 안 {laid.domains[0].name}의 가중치를 "
                "정합니다"
            ),
            english=(
                f"{laid.caller.username} sets the weight of {laid.domains[0].name} in "
                f"{laid.group.name}"
            ),
        )

    @override
    async def call(self, adapter: FairShareAdapter, laid: DomainsInAGroupAndACaller) -> Upserted:
        with ActingAs(laid.caller):
            payload = await adapter.upsert_domain(
                UpsertDomainFairShareWeightInput(
                    resource_group_name=laid.group.name,
                    domain_name=laid.domains[0].name,
                    weight=WEIGHT,
                )
            )
        return payload.domain_fair_share


@dataclass(frozen=True)
class TheSuperadminSetsTheWeight(
    Scenario[TestSeedingSession, DomainsInAGroupAndACaller, FairShareAdapter, Upserted]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-sets-a-domain-weight"

    @override
    def describe(self) -> str:
        return Says(
            (
                "superadmin 이 그룹 안 도메인의 가중치를 정하면 그 가중치를 담은 기록이 오고 나머지 "
                "설정은 그룹 기본값입니다"
            ),
            english=(
                "when the superadmin sets the weight of a domain in the group, the record comes "
                "back carrying that weight and the rest of the settings are the group defaults"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, DomainsInAGroupAndACaller]:
        return DomainsInAGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[DomainsInAGroupAndACaller, FairShareAdapter, Upserted]:
        return SettingTheWeight()

    @override
    def then(self) -> Then[DomainsInAGroupAndACaller, Upserted]:
        return TheDomainWeight(started=self.started)


@dataclass(frozen=True)
class AUserGrantedUpdateOnTheGroupMayNotSetTheWeight(
    Scenario[TestSeedingSession, DomainsInAGroupAndACaller, FairShareAdapter, Upserted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-on-the-group-may-not-set-a-domain-weight"

    @override
    def describe(self) -> str:
        return Says(
            (
                "그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 도메인의 가중치를 정하려 하면 "
                "권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 "
                "검사합니다"
            ),
            english=(
                "when a user granted the update permission through a role assigned on the group "
                "tries to set the weight of a domain, it is rejected for a lack of permission. A "
                "weight write checks permission against the global target, not the group"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, DomainsInAGroupAndACaller]:
        return DomainsInAGroupAndSomeone(granted=Permission.UPDATE)

    @override
    def when(self) -> When[DomainsInAGroupAndACaller, FairShareAdapter, Upserted]:
        return SettingTheWeight()

    @override
    def then(self) -> Then[DomainsInAGroupAndACaller, Upserted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSetTheWeight(
    Scenario[TestSeedingSession, DomainsInAGroupAndACaller, FairShareAdapter, Upserted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-set-a-domain-weight"

    @override
    def describe(self) -> str:
        return Says(
            (
                "아무 권한도 받지 않은 사용자가 도메인의 가중치를 정하려 하면 권한 부족으로 "
                "거부됩니다"
            ),
            english=(
                "when a user granted nothing tries to set the weight of a domain, it is rejected "
                "for a lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, DomainsInAGroupAndACaller]:
        return DomainsInAGroupAndSomeone()

    @override
    def when(self) -> When[DomainsInAGroupAndACaller, FairShareAdapter, Upserted]:
        return SettingTheWeight()

    @override
    def then(self) -> Then[DomainsInAGroupAndACaller, Upserted]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[FairShareStep] = [
    TheSuperadminSetsTheWeight(started=datetime.now(UTC)),
    AUserGrantedUpdateOnTheGroupMayNotSetTheWeight(),
    AUserGrantedNothingMayNotSetTheWeight(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_upserting(
    scenario: FairShareStep, adapter: FairShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
