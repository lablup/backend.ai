"""설정 정의 검색 — 슈퍼관리자 검사를 확인한다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    SearchAppConfigDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    SearchAppConfigDefinitionsPayload,
)
from ai.backend.manager.api.adapters.app_config_definition.adapter import (
    AppConfigDefinitionAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_definition import (
    EveryLaidDefinitionIsFound,
    ManyDefinitionsAndACaller,
    ManyDefinitionsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = SearchAppConfigDefinitionsPayload
type SearchingStep = Scenario[
    TestSeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEverything(When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]):
    """필터 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyDefinitionsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 필터 없이 전체를 조회합니다",
            english=f"{laid.caller.username} reads everything without a filter",
        )

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ManyDefinitionsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(SearchAppConfigDefinitionsInput())


@dataclass(frozen=True)
class TheSuperadminCountsEveryOne(
    Scenario[TestSeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-definition"

    @override
    def describe(self) -> str:
        return Says(
            "설정 정의 셋이 있고 superadmin 이 필터 없이 전체를 검색하면, 셋 다 집계됩니다",
            english=(
                "when three config definitions exist and the superadmin searches everything "
                "without a filter, all three are counted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDefinitionsAndACaller]:
        return ManyDefinitionsAndSomeone(count=3, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyDefinitionsAndACaller, Searched]:
        return EveryLaidDefinitionIsFound()


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[TestSeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-definitions"

    @override
    def describe(self) -> str:
        return Says(
            "일반 사용자가 전체를 검색하면, superadmin 권한이 없어 거부됩니다",
            english=(
                "when a regular user searches everything, it is rejected because the user "
                "has no superadmin privilege"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDefinitionsAndACaller]:
        return ManyDefinitionsAndSomeone(count=3)

    @override
    def when(self) -> When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyDefinitionsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryOne(),
    APlainUserMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: AppConfigDefinitionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
