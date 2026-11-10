"""공개 설정 조회 — 검사 없는 조회가 무엇을 보는가.

인증도 권한도 확인하지 않는다. 아무 스코프도 지정하지 않으므로 공개 조각만 병합되고, 그것이 이
경로가 안전한 근거다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.dto.manager.v2.app_config.request import PublicGetAppConfigsInput
from ai.backend.common.dto.manager.v2.app_config.response import GetAppConfigsPayload
from ai.backend.manager.api.adapters.app_config.adapter import AppConfigAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.app_config import (
    AConfigLaidAcross,
    AMergeAndACaller,
    SeveralConfigsLaid,
    TheMergedConfigs,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[
    TestSeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload
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
        if self.signed_in:
            who_ko = who_en = laid.caller.username
        else:
            who_ko, who_en = "로그인하지 않은 호출자", "a caller who is not signed in"
        return Says(
            f"{who_ko}가 {', '.join(laid.names)}의 공개 설정을 조회합니다",
            english=f"{who_en} reads the public config for {', '.join(laid.names)}",
        )

    @override
    async def call(self, adapter: AppConfigAdapter, laid: AMergeAndACaller) -> GetAppConfigsPayload:
        asked = PublicGetAppConfigsInput(config_names=list(laid.names))
        if not self.signed_in:
            return await adapter.public_app_configs(asked)
        with ActingAs(laid.caller):
            return await adapter.public_app_configs(asked)


@dataclass(frozen=True)
class AnonymousReadsThePublicValueOnly(
    Scenario[TestSeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-caller-not-signed-in-reads-the-public-value-only"

    @override
    def describe(self) -> str:
        return Says(
            "공개, 도메인, 사용자 조각이 모두 있는 이름을 로그인 없이 조회하면, 공개 조각의 "
            "값만 반환됩니다. 도메인과 사용자 조각은 섞이지 않습니다",
            english=(
                "when a name with public, domain, and user fragments is read without signing "
                "in, only the value of the public fragment comes back. The domain and user "
                "fragments do not merge in"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(public=PUBLIC, domain=DOMAIN, user=MINE, granted=False)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingPublic()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=(PUBLIC,))


@dataclass(frozen=True)
class ANameWithNoPublicFragmentAnswersEmpty(
    Scenario[TestSeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-name-holding-no-public-fragment-answers-an-empty-config"

    @override
    def describe(self) -> str:
        return Says(
            "사용자 조각만 있는 이름을 로그인 없이 조회하면, 빈 설정이 반환됩니다",
            english=(
                "when a name that has only a user fragment is read without signing in, "
                "an empty config comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(user=MINE, granted=False)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingPublic()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=({},))


@dataclass(frozen=True)
class AnUnregisteredNameAnswersEmptyToo(
    Scenario[TestSeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-name-nothing-registers-answers-an-empty-config-too"

    @override
    def describe(self) -> str:
        return Says(
            "정의조차 없는 이름을 로그인 없이 조회하면, 공개 조각이 없는 이름과 같은 빈 설정이 "
            "반환됩니다. 이 조회로는 어떤 이름이 등록되었는지 알 수 없습니다",
            english=(
                "when a name that has no definition at all is read without signing in, the "
                "same empty config comes back as for a name with no public fragment. This "
                "read cannot tell which names are registered"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(defined=False, granted=False)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingPublic()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=({},))


@dataclass(frozen=True)
class ASignedInUserGetsTheSameAnswer(
    Scenario[TestSeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-signed-in-user-granted-nothing-gets-the-same-public-answer"

    @override
    def describe(self) -> str:
        return Says(
            "같은 조각 셋을 아무 권한도 없는 사용자가 로그인한 채 공개 조회로 조회해도, 공개 "
            "조각의 값만 반환됩니다. 이 조회는 호출자를 아예 보지 않습니다",
            english=(
                "even when a user granted nothing reads the same three fragments through the "
                "public read while signed in, only the value of the public fragment comes "
                "back. This read does not look at the caller at all"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(public=PUBLIC, domain=DOMAIN, user=MINE, granted=False)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingPublic(signed_in=True)

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=(PUBLIC,))


@dataclass(frozen=True)
class SeveralNamesAnswerInRequestOrder(
    Scenario[TestSeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    publics: tuple[Mapping[str, Any], ...] = ({"n": 1}, {"n": 2}, {"n": 3})

    @override
    def summary(self) -> str:
        return "several-names-answer-one-each-in-request-order"

    @override
    def describe(self) -> str:
        return Says(
            "이름 셋을 한 번에 로그인 없이 조회하면, 각각의 공개 값이 요청한 순서대로 반환됩니다",
            english=(
                "when three names are read in one call without signing in, each public value "
                "comes back in the order requested"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AMergeAndACaller]:
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
