"""설정 정의 검색 — 슈퍼관리자 검사를 확인한다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_definition import (
    EveryLaidDefinitionIsFound,
    ManyDefinitionsAndACaller,
    ManyDefinitionsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

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
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type Searched = SearchAppConfigDefinitionsPayload
type SearchingStep = Scenario[
    SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEverything(When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]):
    """필터 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyDefinitionsAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ManyDefinitionsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(SearchAppConfigDefinitionsInput())


@dataclass(frozen=True)
class TheSuperadminCountsEveryOne(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-definition"

    @override
    def describe(self) -> str:
        return "설정 정의 셋이 있고 슈퍼관리자가 필터 없이 전체를 검색하면, 셋 다 집계된다"

    @override
    def given(self) -> Given[SeedingSession, ManyDefinitionsAndACaller]:
        return ManyDefinitionsAndSomeone(count=3, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyDefinitionsAndACaller, Searched]:
        return EveryLaidDefinitionIsFound()


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-definitions"

    @override
    def describe(self) -> str:
        return "일반 사용자가 전체를 검색하면, 슈퍼관리자 권한이 없어 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyDefinitionsAndACaller]:
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
