"""공개 설정 조회 — 검사 없는 조회가 무엇을 보는가.

인증도 권한도 확인하지 않는다. 아무 스코프도 지정하지 않으므로 공개 조각만 병합되고, 그것이 이
경로가 안전한 근거다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.app_config import (
    AConfigLaidAcross,
    AMergeAndACaller,
    SeveralConfigsLaid,
    TheMergedConfigs,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.app_config.request import PublicGetAppConfigsInput
from ai.backend.common.dto.manager.v2.app_config.response import GetAppConfigsPayload
from ai.backend.manager.api.adapters.app_config.adapter import AppConfigAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type ReadingStep = Scenario[
    SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload
]

PUBLIC = {"theme": "light", "menu": {"home": True}}
DOMAIN = {"theme": "dark"}
MINE = {"theme": "solar"}


@dataclass(frozen=True)
class ReadingPublic(When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]):
    """아무 스코프도 지정하지 않고 조회한다. 로그인한 채 호출할 수도 있지만 그 사실은 쓰이지 않는다."""

    signed_in: bool = False

    @override
    def operation(self) -> str:
        return "public_app_configs"

    @override
    def describe(self, laid: AMergeAndACaller) -> str:
        who = laid.caller.username if self.signed_in else "로그인하지 않은 호출자"
        return f"{who}가 {', '.join(laid.names)}의 공개 설정을 조회"

    @override
    async def call(self, adapter: AppConfigAdapter, laid: AMergeAndACaller) -> GetAppConfigsPayload:
        asked = PublicGetAppConfigsInput(config_names=list(laid.names))
        if not self.signed_in:
            return await adapter.public_app_configs(asked)
        with ActingAs(laid.caller):
            return await adapter.public_app_configs(asked)


@dataclass(frozen=True)
class AnonymousReadsThePublicValueOnly(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-caller-not-signed-in-reads-the-public-value-only"

    @override
    def describe(self) -> str:
        return (
            "공개·도메인·사용자 조각이 모두 있는 이름을 로그인 없이 조회하면, 공개 조각의 값만 "
            "반환된다. 도메인과 사용자 조각은 섞이지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(public=PUBLIC, domain=DOMAIN, user=MINE, granted=False)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingPublic()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=(PUBLIC,))


@dataclass(frozen=True)
class ANameWithNoPublicFragmentAnswersEmpty(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-name-holding-no-public-fragment-answers-an-empty-config"

    @override
    def describe(self) -> str:
        return "사용자 조각만 있는 이름을 로그인 없이 조회하면, 빈 설정이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(user=MINE, granted=False)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingPublic()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=({},))


@dataclass(frozen=True)
class AnUnregisteredNameAnswersEmptyToo(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-name-nothing-registers-answers-an-empty-config-too"

    @override
    def describe(self) -> str:
        return (
            "정의조차 없는 이름을 로그인 없이 조회하면, 공개 조각이 없는 이름과 같은 빈 설정이 "
            "반환된다. 이 조회로는 어떤 이름이 등록돼 있는지 알 수 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(defined=False, granted=False)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingPublic()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=({},))


@dataclass(frozen=True)
class ASignedInUserGetsTheSameAnswer(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-signed-in-user-granted-nothing-gets-the-same-public-answer"

    @override
    def describe(self) -> str:
        return (
            "같은 조각 셋을 아무 권한도 없는 사용자가 로그인한 채 공개 조회로 조회해도, 공개 "
            "조각의 값만 반환된다. 이 조회는 호출자를 아예 보지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(public=PUBLIC, domain=DOMAIN, user=MINE, granted=False)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingPublic(signed_in=True)

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=(PUBLIC,))


@dataclass(frozen=True)
class SeveralNamesAnswerInRequestOrder(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    publics: tuple[Mapping[str, Any], ...] = ({"n": 1}, {"n": 2}, {"n": 3})

    @override
    def summary(self) -> str:
        return "several-names-answer-one-each-in-request-order"

    @override
    def describe(self) -> str:
        return "이름 셋을 한 번에 로그인 없이 조회하면, 각각의 공개 값이 요청한 순서대로 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return SeveralConfigsLaid(publics=self.publics, granted=False)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingPublic()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=self.publics)


SCENARIOS: list[ReadingStep] = [
    AnonymousReadsThePublicValueOnly(),
    ANameWithNoPublicFragmentAnswersEmpty(),
    AnUnregisteredNameAnswersEmptyToo(),
    ASignedInUserGetsTheSameAnswer(),
    SeveralNamesAnswerInRequestOrder(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_public(
    scenario: ReadingStep, adapter: AppConfigAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
