"""프리셋 검색 — 스코프 타입 필터로 검색한 결과를 검증한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.role_preset.request import (
    RolePresetFilter,
    SearchRolePresetsInput,
)
from ai.backend.common.dto.manager.v2.role_preset.response import SearchRolePresetsPayload
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.role_preset import (
    OnlyThePresetForPublicComesBack,
    PresetsForPublicAndEveryProjectAndACaller,
    PresetsForPublicAndEveryProjectAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchingStep = Scenario[
    TestSeedingSession,
    PresetsForPublicAndEveryProjectAndACaller,
    RolePresetAdapter,
    SearchRolePresetsPayload,
]


@dataclass(frozen=True)
class SearchingByScopeType(
    When[PresetsForPublicAndEveryProjectAndACaller, RolePresetAdapter, SearchRolePresetsPayload]
):
    """스코프 타입 필터에 값 하나를 지정해 검색한다."""

    scope_type: str

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: PresetsForPublicAndEveryProjectAndACaller) -> str:
        return f"{laid.caller.username}이 스코프 타입이 {self.scope_type}인 프리셋을 검색"

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: PresetsForPublicAndEveryProjectAndACaller
    ) -> SearchRolePresetsPayload:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchRolePresetsInput(
                    filter=RolePresetFilter(scope_type=StringFilter(equals=self.scope_type))
                )
            )


@dataclass(frozen=True)
class AGlobalScopeTypeFindsThePresetForPublic(
    Scenario[
        TestSeedingSession,
        PresetsForPublicAndEveryProjectAndACaller,
        RolePresetAdapter,
        SearchRolePresetsPayload,
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-global-scope-type-finds-the-preset-for-public"

    @override
    def describe(self) -> str:
        return Says(
            f"슈퍼관리자가 스코프 타입 {GlobalEntityType()}로 프리셋을 검색하면, "
            f"{GlobalEntityName.PUBLIC} 하나에만 역할을 만드는 프리셋만 반환된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsForPublicAndEveryProjectAndACaller]:
        return PresetsForPublicAndEveryProjectAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[
        PresetsForPublicAndEveryProjectAndACaller, RolePresetAdapter, SearchRolePresetsPayload
    ]:
        return SearchingByScopeType(str(GlobalEntityType()))

    @override
    def then(self) -> Then[PresetsForPublicAndEveryProjectAndACaller, SearchRolePresetsPayload]:
        return OnlyThePresetForPublicComesBack(self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearch(
    Scenario[
        TestSeedingSession,
        PresetsForPublicAndEveryProjectAndACaller,
        RolePresetAdapter,
        SearchRolePresetsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-presets"

    @override
    def describe(self) -> str:
        return Says("아무 권한도 받지 않은 사용자가 프리셋을 검색하려 하면, 권한 부족으로 거부된다")

    @override
    def given(self) -> Given[TestSeedingSession, PresetsForPublicAndEveryProjectAndACaller]:
        return PresetsForPublicAndEveryProjectAndSomeone()

    @override
    def when(
        self,
    ) -> When[
        PresetsForPublicAndEveryProjectAndACaller, RolePresetAdapter, SearchRolePresetsPayload
    ]:
        return SearchingByScopeType(str(GlobalEntityType()))

    @override
    def then(self) -> Then[PresetsForPublicAndEveryProjectAndACaller, SearchRolePresetsPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    AGlobalScopeTypeFindsThePresetForPublic(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
