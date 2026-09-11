"""자기 설정 조회 — 세 스코프의 설정 조각이 어떻게 하나로 병합되는가.

설정은 자체 행이 없다. 세 테이블에 조각을 미리 만들어 두고 조회하면 병합 결과가 무엇인지가 이
모듈의 전부이고, 병합 순서는 허용 목록 항목의 순위가 결정한다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config import (
    ENFORCEMENT,
    AConfigLaidAcross,
    AMergeAndACaller,
    SeveralConfigsLaid,
    TheMergedConfigs,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config.request import MyGetAppConfigsInput
from ai.backend.common.dto.manager.v2.app_config.response import GetAppConfigsPayload
from ai.backend.manager.api.adapters.app_config.adapter import AppConfigAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type ReadingStep = Scenario[
    SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload
]

PUBLIC = {"theme": "light", "menu": {"home": True, "docs": True}}
DOMAIN = {"theme": "dark", "menu": {"docs": False, "billing": True}}
MINE = {"theme": "solar", "menu": {"home": False}}


@dataclass(frozen=True)
class ReadingMine(When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]):
    """세션의 사용자와 도메인으로 조회한다. 이름은 미리 만들어 둔 것에서 읽는다."""

    @override
    def operation(self) -> str:
        return "my_app_configs"

    @override
    def describe(self, laid: AMergeAndACaller) -> str:
        return f"{laid.caller.username}이 {', '.join(laid.names)}의 자기 설정을 조회"

    @override
    async def call(self, adapter: AppConfigAdapter, laid: AMergeAndACaller) -> GetAppConfigsPayload:
        with ActingAs(laid.caller):
            return await adapter.my_app_configs(MyGetAppConfigsInput(config_names=list(laid.names)))


@dataclass(frozen=True)
class ANameWithNoFragmentAnswersEmpty(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-name-holding-no-fragment-answers-an-empty-config"

    @override
    def describe(self) -> str:
        return (
            "정의만 있고 허용 목록 항목도 조각도 없는 이름을 읽기 권한을 받은 사용자가 조회하면, "
            "그 이름이 응답에서 빠지지 않고 빈 설정으로 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross()

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=({},))


@dataclass(frozen=True)
class AnUnregisteredNameAnswersEmpty(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-name-nothing-registers-answers-an-empty-config"

    @override
    def describe(self) -> str:
        return (
            "정의조차 없는 이름을 읽기 권한을 받은 사용자가 조회하면, 정의가 없다고 거부되지 "
            "않고 빈 설정으로 반환된다. 이 조회는 정의를 확인하지 않고 조각만 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(defined=False)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=({},))


@dataclass(frozen=True)
class OnlyAPublicFragmentAnswersItself(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-public-fragment-alone-answers-its-own-value"

    @override
    def describe(self) -> str:
        return "공개 스코프에만 조각이 있는 이름을 조회하면, 그 조각의 값이 그대로 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(public=PUBLIC)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=(PUBLIC,))


@dataclass(frozen=True)
class MyFragmentOverridesTheDomains(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "my-own-fragment-overrides-the-domains"

    @override
    def describe(self) -> str:
        return (
            "같은 이름에 도메인 조각과 자기 조각이 모두 있고 허용 목록 항목이 기본 순위이면, "
            "겹치는 키는 자기 값이 남고 겹치지 않는 키는 양쪽 모두 남는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(domain=DOMAIN, user=MINE)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(
            wanted=({"theme": "solar", "menu": {"docs": False, "billing": True, "home": False}},)
        )


@dataclass(frozen=True)
class TheDomainsFragmentOverridesThePublic(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "the-domains-fragment-overrides-the-public-one"

    @override
    def describe(self) -> str:
        return (
            "같은 이름에 공개 조각과 도메인 조각이 모두 있고 허용 목록 항목이 기본 순위이면, "
            "겹치는 키는 도메인 값이 남는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(public=PUBLIC, domain=DOMAIN)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(
            wanted=({"theme": "dark", "menu": {"home": True, "docs": False, "billing": True}},)
        )


@dataclass(frozen=True)
class AFlippedRankLetsTheDomainWin(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-rank-the-admin-flipped-lets-the-domains-fragment-override-mine"

    @override
    def describe(self) -> str:
        return (
            "도메인 허용 목록 항목의 순위를 사용자 항목보다 크게 두면, 같은 조각들에서 겹치는 키의 "
            "우선순위가 도메인으로 뒤바뀐다. 순위는 허용 목록 항목에 있고 값의 소유자는 바꿀 수 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(domain=DOMAIN, user=MINE, ranks={AppConfigScopeType.DOMAIN: 400})

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(
            wanted=({"theme": "dark", "menu": {"home": False, "docs": False, "billing": True}},)
        )


@dataclass(frozen=True)
class NestedKeysMergeInside(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "nested-dicts-merge-key-by-key-inside"

    @override
    def describe(self) -> str:
        return (
            "같은 키 아래 중첩 사전을 담은 두 조각을 조회하면, 겹치지 않는 안쪽 키는 양쪽 모두 "
            "남고 겹치는 안쪽 키만 뒤의 것이 남는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(
            domain={"editor": {"font": {"size": 12, "family": "mono"}, "wrap": True}},
            user={"editor": {"font": {"size": 14}, "theme": "night"}},
        )

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(
            wanted=(
                {
                    "editor": {
                        "font": {"size": 14, "family": "mono"},
                        "wrap": True,
                        "theme": "night",
                    }
                },
            )
        )


@dataclass(frozen=True)
class ListsAreReplacedWhole(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-list-is-replaced-whole-rather-than-appended"

    @override
    def describe(self) -> str:
        return "같은 키에 목록을 담은 두 조각을 조회하면, 뒤의 것의 목록만 남고 이어 붙지 않는다"

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(domain={"plugins": ["git", "lint"]}, user={"plugins": ["spell"]})

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=({"plugins": ["spell"]},))


@dataclass(frozen=True)
class AnExplicitNullOverrides(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-value-written-as-null-overrides-rather-than-being-skipped"

    @override
    def describe(self) -> str:
        return (
            "앞 조각의 키에 값이 있고 뒤 조각이 같은 키를 비워 두면, 그 키는 비어 있는 채로 "
            "반환된다. 빈 값도 덮어쓴다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(domain={"banner": "welcome"}, user={"banner": None})

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=({"banner": None},))


@dataclass(frozen=True)
class AnotherUsersFragmentStaysOut(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "another-users-fragment-does-not-merge-into-mine"

    @override
    def describe(self) -> str:
        return (
            "같은 도메인의 다른 사용자가 같은 이름에 조각을 두었어도, 자기 설정을 조회하면 "
            "자기 조각의 값만 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(user=MINE, another_user={"theme": "theirs", "secret": 1})

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=(MINE,))


@dataclass(frozen=True)
class AnotherDomainsFragmentStaysOut(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "another-domains-fragment-does-not-merge-into-mine"

    @override
    def describe(self) -> str:
        return "다른 도메인이 같은 이름에 조각을 두었어도, 자기 설정을 조회하면 자기 도메인 조각의 값만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(domain=DOMAIN, another_domain={"theme": "elsewhere"})

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=(DOMAIN,))


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
        return "이름 셋을 한 번에 조회하면, 각각의 병합 결과가 요청한 순서대로 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return SeveralConfigsLaid(publics=self.publics)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=self.publics)


@dataclass(frozen=True)
class ANameAskedTwiceAnswersTwice(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-name-asked-twice-is-answered-twice"

    @override
    def describe(self) -> str:
        return "같은 이름을 두 번 지정해 조회하면, 같은 값이 두 번 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(public=PUBLIC, asked=2)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=(PUBLIC, PUBLIC))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-their-own-config"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 자기 설정을 조회하면, 스코프 권한 검사에서 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(public=PUBLIC, granted=False)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneRead(
    Scenario[SeedingSession, AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-granted-nothing-read"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 끄면 아무 권한도 없는 사용자도 자기 설정을 조회할 수 있다. "
            "이 조회는 역할이 아니라 권한 그래프로 보호되므로 스위치가 영향을 준다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AMergeAndACaller]:
        return AConfigLaidAcross(public=PUBLIC, granted=False)

    @override
    def when(self) -> When[AMergeAndACaller, AppConfigAdapter, GetAppConfigsPayload]:
        return ReadingMine()

    @override
    def then(self) -> Then[AMergeAndACaller, GetAppConfigsPayload]:
        return TheMergedConfigs(wanted=(PUBLIC,))


SCENARIOS: list[ReadingStep] = [
    ANameWithNoFragmentAnswersEmpty(),
    AnUnregisteredNameAnswersEmpty(),
    OnlyAPublicFragmentAnswersItself(),
    MyFragmentOverridesTheDomains(),
    TheDomainsFragmentOverridesThePublic(),
    AFlippedRankLetsTheDomainWin(),
    NestedKeysMergeInside(),
    ListsAreReplacedWhole(),
    AnExplicitNullOverrides(),
    AnotherUsersFragmentStaysOut(),
    AnotherDomainsFragmentStaysOut(),
    SeveralNamesAnswerInRequestOrder(),
    ANameAskedTwiceAnswersTwice(),
    AUserGrantedNothingMayNotRead(),
    EnforcementOffLetsAnyoneRead(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_mine(
    scenario: ReadingStep, adapter: AppConfigAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
