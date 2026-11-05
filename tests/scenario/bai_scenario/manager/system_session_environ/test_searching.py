"""시스템 세션 환경변수 전체 검색과 범위별 검색."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminSearchSystemSessionEnvironsInput,
    ScopedSearchSystemSessionEnvironsInput,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    AdminSearchSystemSessionEnvironsPayload,
    ScopedSearchSystemSessionEnvironsPayload,
)
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironScope,
)
from ai.backend.manager.api.adapters.system_session_environ.adapter import (
    SystemSessionEnvironAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.system_session_environ import (
    ManyEnvironsAndACaller,
    ManyEnvironsAndSomeone,
    TheEnvironIsListed,
    TheScopedEnvironsAreListed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchingStep = Scenario[TestSeedingSession, Any, SystemSessionEnvironAdapter, Any]


@dataclass(frozen=True)
class SearchingEveryScope(
    When[
        ManyEnvironsAndACaller,
        SystemSessionEnvironAdapter,
        AdminSearchSystemSessionEnvironsPayload,
    ]
):
    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: ManyEnvironsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 범위를 가리지 않고 시스템 세션 환경변수를 검색합니다",
            english=(f"{laid.caller.username} searches system session environs across every scope"),
        )

    @override
    async def call(
        self, adapter: SystemSessionEnvironAdapter, laid: ManyEnvironsAndACaller
    ) -> AdminSearchSystemSessionEnvironsPayload:
        with ActingAs(laid.caller):
            return await adapter.global_search(AdminSearchSystemSessionEnvironsInput())


@dataclass(frozen=True)
class SearchingInPublic(
    When[
        ManyEnvironsAndACaller,
        SystemSessionEnvironAdapter,
        ScopedSearchSystemSessionEnvironsPayload,
    ]
):
    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ManyEnvironsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 public 범위의 시스템 세션 환경변수를 검색합니다",
            english=f"{laid.caller.username} searches system session environs in the public scope",
        )

    @override
    async def call(
        self, adapter: SystemSessionEnvironAdapter, laid: ManyEnvironsAndACaller
    ) -> ScopedSearchSystemSessionEnvironsPayload:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchSystemSessionEnvironsInput(scope=SystemSessionEnvironScope(public=True))
            )


@dataclass(frozen=True)
class TheSuperadminSearchesEveryScope(
    Scenario[
        TestSeedingSession,
        ManyEnvironsAndACaller,
        SystemSessionEnvironAdapter,
        AdminSearchSystemSessionEnvironsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searching-every-scope-counts-every-row"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 범위를 가리지 않고 검색하면 미리 저장한 행이 모두 반환됩니다. 이 호출은 "
            "전역 역할을 검사합니다",
            english=(
                "when the superadmin searches across every scope, every row seeded in advance "
                "comes back. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyEnvironsAndACaller]:
        return ManyEnvironsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[
        ManyEnvironsAndACaller,
        SystemSessionEnvironAdapter,
        AdminSearchSystemSessionEnvironsPayload,
    ]:
        return SearchingEveryScope()

    @override
    def then(
        self,
    ) -> Then[ManyEnvironsAndACaller, AdminSearchSystemSessionEnvironsPayload]:
        return TheEnvironIsListed()


@dataclass(frozen=True)
class APlainUserMayNotSearchEveryScope(
    Scenario[
        TestSeedingSession,
        ManyEnvironsAndACaller,
        SystemSessionEnvironAdapter,
        AdminSearchSystemSessionEnvironsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-every-scope"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 범위를 가리지 않고 검색하려 하면 권한 부족으로 "
            "거부됩니다. 이 호출은 전역 역할을 검사합니다",
            english=(
                "when a user who is not the superadmin searches across every scope, it is "
                "rejected for lack of permission. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyEnvironsAndACaller]:
        return ManyEnvironsAndSomeone()

    @override
    def when(
        self,
    ) -> When[
        ManyEnvironsAndACaller,
        SystemSessionEnvironAdapter,
        AdminSearchSystemSessionEnvironsPayload,
    ]:
        return SearchingEveryScope()

    @override
    def then(
        self,
    ) -> Then[ManyEnvironsAndACaller, AdminSearchSystemSessionEnvironsPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheSuperadminSearchesPublic(
    Scenario[
        TestSeedingSession,
        ManyEnvironsAndACaller,
        SystemSessionEnvironAdapter,
        ScopedSearchSystemSessionEnvironsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searching-public-counts-the-public-rows"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 public 범위를 검색하면 그 범위의 미리 저장한 행이 모두 반환됩니다",
            english=(
                "when the superadmin searches the public scope, every row seeded in advance "
                "there comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyEnvironsAndACaller]:
        return ManyEnvironsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[
        ManyEnvironsAndACaller,
        SystemSessionEnvironAdapter,
        ScopedSearchSystemSessionEnvironsPayload,
    ]:
        return SearchingInPublic()

    @override
    def then(
        self,
    ) -> Then[ManyEnvironsAndACaller, ScopedSearchSystemSessionEnvironsPayload]:
        return TheScopedEnvironsAreListed()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchPublic(
    Scenario[
        TestSeedingSession,
        ManyEnvironsAndACaller,
        SystemSessionEnvironAdapter,
        ScopedSearchSystemSessionEnvironsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-the-public-scope"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 public 범위를 검색하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing searches the public scope, it is rejected for lack "
                "of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyEnvironsAndACaller]:
        return ManyEnvironsAndSomeone()

    @override
    def when(
        self,
    ) -> When[
        ManyEnvironsAndACaller,
        SystemSessionEnvironAdapter,
        ScopedSearchSystemSessionEnvironsPayload,
    ]:
        return SearchingInPublic()

    @override
    def then(
        self,
    ) -> Then[ManyEnvironsAndACaller, ScopedSearchSystemSessionEnvironsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminSearchesEveryScope(),
    APlainUserMayNotSearchEveryScope(),
    TheSuperadminSearchesPublic(),
    AUserGrantedNothingMayNotSearchPublic(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep,
    adapter: SystemSessionEnvironAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
