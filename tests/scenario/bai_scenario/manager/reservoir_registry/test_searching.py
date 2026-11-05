"""Reservoir 레지스트리 검색."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    AdminSearchReservoirRegistriesInput,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    AdminSearchReservoirRegistriesPayload,
)
from ai.backend.manager.api.adapters.reservoir_registry.adapter import (
    ReservoirRegistryAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.reservoir_registry import (
    ManyRegistriesAndACaller,
    ManyRegistriesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchingStep = Scenario[
    TestSeedingSession,
    ManyRegistriesAndACaller,
    ReservoirRegistryAdapter,
    AdminSearchReservoirRegistriesPayload,
]


@dataclass(frozen=True)
class Searching(
    When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, AdminSearchReservoirRegistriesPayload]
):
    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 Reservoir 레지스트리를 검색합니다",
            english=f"{laid.caller.username} searches Reservoir registries",
        )

    @override
    async def call(
        self, adapter: ReservoirRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> AdminSearchReservoirRegistriesPayload:
        with ActingAs(laid.caller):
            return await adapter.search(AdminSearchReservoirRegistriesInput())


@dataclass(frozen=True)
class EveryRegistryIsReturned(
    Then[ManyRegistriesAndACaller, AdminSearchReservoirRegistriesPayload]
):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 레지스트리가 모두 반환됩니다",
            english="every registry seeded in advance comes back",
        )

    @override
    def look(
        self,
        laid: ManyRegistriesAndACaller,
        answered: Answered[AdminSearchReservoirRegistriesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held(
                "items",
                sorted((one.id, one.name) for one in payload.items),
                SameAs(
                    sorted((one.id, one.name) for one in laid.laid),
                    Says(
                        "미리 저장한 레지스트리",
                        english="the registries seeded in advance",
                    ),
                ),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheSuperadminSearches(
    Scenario[
        TestSeedingSession,
        ManyRegistriesAndACaller,
        ReservoirRegistryAdapter,
        AdminSearchReservoirRegistriesPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searching-reservoir-registries-counts-every-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 Reservoir 레지스트리를 검색하면 미리 저장한 레지스트리가 모두 "
            "반환됩니다. 이 호출은 전역 역할을 검사합니다",
            english=(
                "when the superadmin searches Reservoir registries, every registry seeded in "
                "advance comes back. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[
        ManyRegistriesAndACaller, ReservoirRegistryAdapter, AdminSearchReservoirRegistriesPayload
    ]:
        return Searching()

    @override
    def then(
        self,
    ) -> Then[ManyRegistriesAndACaller, AdminSearchReservoirRegistriesPayload]:
        return EveryRegistryIsReturned()


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[
        TestSeedingSession,
        ManyRegistriesAndACaller,
        ReservoirRegistryAdapter,
        AdminSearchReservoirRegistriesPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-reservoir-registries"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 Reservoir 레지스트리를 검색하려 하면 권한 부족으로 "
            "거부됩니다. 이 호출은 전역 역할을 검사합니다",
            english=(
                "when a user who is not the superadmin tries to search Reservoir registries, it "
                "is rejected for lack of permission. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone()

    @override
    def when(
        self,
    ) -> When[
        ManyRegistriesAndACaller, ReservoirRegistryAdapter, AdminSearchReservoirRegistriesPayload
    ]:
        return Searching()

    @override
    def then(
        self,
    ) -> Then[ManyRegistriesAndACaller, AdminSearchReservoirRegistriesPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminSearches(),
    APlainUserMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep,
    adapter: ReservoirRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
