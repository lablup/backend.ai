"""프리셋 가용성 — 지금 이 프로젝트에서 어떤 프리셋을 쓸 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_allocation.request import (
    CheckPresetAvailabilityInput,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    CheckPresetAvailabilityPayload,
)
from ai.backend.manager.api.adapters.resource_allocation.adapter import (
    ResourceAllocationAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_allocation_usage import (
    APlaceAndSomeone,
    AUsagePlace,
    ThePresetAvailability,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type CheckingStep = Scenario[
    TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, CheckPresetAvailabilityPayload
]


@dataclass(frozen=True)
class CheckingForCurrentUser(
    When[AUsagePlace, ResourceAllocationAdapter, CheckPresetAvailabilityPayload]
):
    """호출자 자신의 키페어로 프리셋 가용성을 확인한다."""

    @override
    def operation(self) -> str:
        return "check_preset_availability_for_current_user"

    @override
    def describe(self, laid: AUsagePlace) -> str:
        return Says(
            f"{laid.caller.username}이 프로젝트 {laid.project.name}에서 쓸 수 있는 프리셋을 "
            "확인합니다",
            english=(
                f"{laid.caller.username} checks which presets can be used in the project "
                f"{laid.project.name}"
            ),
        )

    @override
    async def call(
        self, adapter: ResourceAllocationAdapter, laid: AUsagePlace
    ) -> CheckPresetAvailabilityPayload:
        with ActingAs(laid.caller):
            return await adapter.check_preset_availability_for_current_user(
                CheckPresetAvailabilityInput(
                    project_id=laid.project.id, resource_group_name=laid.group.name
                )
            )


@dataclass(frozen=True)
class CheckingWithAGivenKey(
    When[AUsagePlace, ResourceAllocationAdapter, CheckPresetAvailabilityPayload]
):
    """미리 만들어 둔 키페어의 접근 키와 정책으로 프리셋 가용성을 확인한다."""

    @override
    def operation(self) -> str:
        return "check_preset_availability"

    @override
    def describe(self, laid: AUsagePlace) -> str:
        return Says(
            f"{laid.caller.username}이 프로젝트 {laid.project.name}에서 쓸 수 있는 프리셋을 "
            "확인합니다",
            english=(
                f"{laid.caller.username} checks which presets can be used in the project "
                f"{laid.project.name}"
            ),
        )

    @override
    async def call(
        self, adapter: ResourceAllocationAdapter, laid: AUsagePlace
    ) -> CheckPresetAvailabilityPayload:
        with ActingAs(laid.caller):
            return await adapter.check_preset_availability(
                input=CheckPresetAvailabilityInput(
                    project_id=laid.project.id, resource_group_name=laid.group.name
                ),
                access_key=str(laid.access_key),
                resource_policy=laid.resource_policy,
            )


@dataclass(frozen=True)
class TheSuperadminChecksForThemselves(
    Scenario[
        TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, CheckPresetAvailabilityPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-checks-available-presets-for-themselves"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 자기 키페어로 프리셋 가용성을 확인하면, 미리 저장한 프리셋이 모두 "
            "쓸 수 있는 것으로 반환됩니다",
            english=(
                "when the superadmin checks preset availability with their own keypair, every "
                "preset seeded in advance comes back marked as available"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(role=UserRole.SUPERADMIN, presets=2)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, CheckPresetAvailabilityPayload]:
        return CheckingForCurrentUser()

    @override
    def then(self) -> Then[AUsagePlace, CheckPresetAvailabilityPayload]:
        return ThePresetAvailability()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotCheckForThemselves(
    Scenario[
        TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, CheckPresetAvailabilityPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-check-preset-availability"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋 가용성을 확인하려 하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing checking preset availability is rejected for not enough "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(presets=1)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, CheckPresetAvailabilityPayload]:
        return CheckingForCurrentUser()

    @override
    def then(self) -> Then[AUsagePlace, CheckPresetAvailabilityPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminChecksWithAGivenKey(
    Scenario[
        TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, CheckPresetAvailabilityPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-checks-available-presets-with-a-given-key"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 주어진 접근 키와 정책으로 프리셋 가용성을 확인하면, 미리 저장한 "
            "프리셋이 모두 쓸 수 있는 것으로 반환됩니다",
            english=(
                "when the superadmin checks preset availability with a given key and policy, "
                "every preset seeded in advance comes back marked as available"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(role=UserRole.SUPERADMIN, presets=2)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, CheckPresetAvailabilityPayload]:
        return CheckingWithAGivenKey()

    @override
    def then(self) -> Then[AUsagePlace, CheckPresetAvailabilityPayload]:
        return ThePresetAvailability()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotCheckWithAGivenKey(
    Scenario[
        TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, CheckPresetAvailabilityPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-check-preset-availability-with-a-given-key"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 주어진 키로 프리셋 가용성을 확인하려 하면 권한 "
            "부족으로 거부됩니다",
            english=(
                "a user granted nothing checking preset availability with a given key is "
                "rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(presets=1)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, CheckPresetAvailabilityPayload]:
        return CheckingWithAGivenKey()

    @override
    def then(self) -> Then[AUsagePlace, CheckPresetAvailabilityPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[CheckingStep] = [
    TheSuperadminChecksForThemselves(),
    AUserGrantedNothingMayNotCheckForThemselves(),
    TheSuperadminChecksWithAGivenKey(),
    AUserGrantedNothingMayNotCheckWithAGivenKey(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_checking_presets(
    scenario: CheckingStep, adapter: ResourceAllocationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
