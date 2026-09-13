"""이름으로 설정 조각 조회 — 한 스코프의 조각을 이름 항목마다 응답한다.

자기 조각 조회는 사용자 스코프 하나만 본다. 지정한 스코프 조회는 그 스코프의 권한을
검사하되, 공개 스코프에는 보호할 스코프가 없어 인증만으로 응답한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_fragment import (
    AReadingPlace,
    ATargetAndACaller,
    EachNameAnsweredWithMine,
    MyFragmentsLaid,
    SomewhereToTarget,
    Target,
    TheTargetsFragmentByName,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.app_config.allow_list import SCOPE_NAMES

from ai.backend.common.data.entity.app_config import AppConfigScopeID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigScopeRef,
    MyAppConfigFragmentsByNamesInput,
    ScopedAppConfigFragmentsByNamesInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import AppConfigFragmentNode
from ai.backend.manager.api.adapters.app_config_fragment.adapter import AppConfigFragmentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type ByNames = list[AppConfigFragmentNode | None]
type MineStep = Scenario[SeedingSession, AReadingPlace, AppConfigFragmentAdapter, ByNames]
type ScopedStep = Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, ByNames]


@dataclass(frozen=True)
class ReadingMineByNames(When[AReadingPlace, AppConfigFragmentAdapter, ByNames]):
    """자기 스코프의 조각을 미리 만들어 둔 이름들로 조회한다."""

    @override
    def operation(self) -> str:
        return "my_app_config_fragments_by_names"

    @override
    def describe(self, laid: AReadingPlace) -> str:
        return f"{laid.caller.username}이 {', '.join(laid.names)}의 자기 조각을 조회"

    @override
    async def call(self, adapter: AppConfigFragmentAdapter, laid: AReadingPlace) -> ByNames:
        with ActingAs(laid.caller):
            return await adapter.my_app_config_fragments_by_names(
                MyAppConfigFragmentsByNamesInput(config_names=list(laid.names))
            )


@dataclass(frozen=True)
class ReadingAtByName(When[ATargetAndACaller, AppConfigFragmentAdapter, ByNames]):
    """지정한 스코프의 조각을 이름으로 조회한다."""

    @override
    def operation(self) -> str:
        return "scoped_app_config_fragments_by_names"

    @override
    def describe(self, laid: ATargetAndACaller) -> str:
        return f"{laid.caller.username}이 {SCOPE_NAMES[laid.scope_type]} 스코프를 지정해 {laid.name}의 조각을 조회"

    @override
    async def call(self, adapter: AppConfigFragmentAdapter, laid: ATargetAndACaller) -> ByNames:
        scope = AppConfigScopeRef(
            scope_type=laid.scope_type,
            scope_id=AppConfigScopeID(laid.scope_id) if laid.scope_id is not None else None,
        )
        with ActingAs(laid.caller):
            return await adapter.scoped_app_config_fragments_by_names(
                ScopedAppConfigFragmentsByNamesInput(scope=scope, config_names=[laid.name])
            )


@dataclass(frozen=True)
class ReadingElsewhereByName(When[ATargetAndACaller, AppConfigFragmentAdapter, ByNames]):
    """지정한 종류의, 존재하지 않는 id를 지정해 조회한다."""

    @override
    def operation(self) -> str:
        return "scoped_app_config_fragments_by_names"

    @override
    def describe(self, laid: ATargetAndACaller) -> str:
        return f"{laid.caller.username}이 어느 {SCOPE_NAMES[laid.scope_type]}도 아닌 id를 지정해 {laid.name}의 조각을 조회"

    @override
    async def call(self, adapter: AppConfigFragmentAdapter, laid: ATargetAndACaller) -> ByNames:
        scope = AppConfigScopeRef(scope_type=laid.scope_type, scope_id=AppConfigScopeID(uuid4()))
        with ActingAs(laid.caller):
            return await adapter.scoped_app_config_fragments_by_names(
                ScopedAppConfigFragmentsByNamesInput(scope=scope, config_names=[laid.name])
            )


@dataclass(frozen=True)
class EachNameIsAnsweredInOrder(
    Scenario[SeedingSession, AReadingPlace, AppConfigFragmentAdapter, ByNames]
):
    @override
    def summary(self) -> str:
        return "three-names-answer-a-fragment-or-an-empty-slot-each-in-request-order"

    @override
    def describe(self) -> str:
        return (
            "사용자 스코프에 허용된 이름 셋 중 둘에 자기 조각이 있고 읽기 권한을 받은 사용자가 "
            "셋을 조회하면, 세 항목이 요청 순서대로 반환되고 조각이 없는 항목은 비어 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, AReadingPlace]:
        return MyFragmentsLaid(names=3, mine_on=(0, 2), granted=(Permission.READ,))

    @override
    def when(self) -> When[AReadingPlace, AppConfigFragmentAdapter, ByNames]:
        return ReadingMineByNames()

    @override
    def then(self) -> Then[AReadingPlace, ByNames]:
        return EachNameAnsweredWithMine()


@dataclass(frozen=True)
class AnotherUsersFragmentStaysOut(
    Scenario[SeedingSession, AReadingPlace, AppConfigFragmentAdapter, ByNames]
):
    @override
    def summary(self) -> str:
        return "another-users-fragment-under-the-same-name-is-not-answered"

    @override
    def describe(self) -> str:
        return "같은 이름에 다른 사용자의 조각이 있어도, 자기 조각을 조회하면 자기 것만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AReadingPlace]:
        return MyFragmentsLaid(anothers={"theirs": True}, granted=(Permission.READ,))

    @override
    def when(self) -> When[AReadingPlace, AppConfigFragmentAdapter, ByNames]:
        return ReadingMineByNames()

    @override
    def then(self) -> Then[AReadingPlace, ByNames]:
        return EachNameAnsweredWithMine()


@dataclass(frozen=True)
class TheDomainsFragmentStaysOut(
    Scenario[SeedingSession, AReadingPlace, AppConfigFragmentAdapter, ByNames]
):
    @override
    def summary(self) -> str:
        return "the-domains-fragment-under-the-same-name-is-not-answered"

    @override
    def describe(self) -> str:
        return (
            "같은 이름에 자기 도메인의 조각이 있어도, 자기 조각을 조회하면 자기 것만 반환된다. "
            "이 조회는 사용자 스코프 하나만 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, AReadingPlace]:
        return MyFragmentsLaid(domains={"domains": True}, granted=(Permission.READ,))

    @override
    def when(self) -> When[AReadingPlace, AppConfigFragmentAdapter, ByNames]:
        return ReadingMineByNames()

    @override
    def then(self) -> Then[AReadingPlace, ByNames]:
        return EachNameAnsweredWithMine()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadMine(
    Scenario[SeedingSession, AReadingPlace, AppConfigFragmentAdapter, ByNames]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-their-own-fragments"

    @override
    def describe(self) -> str:
        return (
            "자기 조각이 있어도 아무 권한도 없는 사용자가 이름으로 조회하면, 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AReadingPlace]:
        return MyFragmentsLaid()

    @override
    def when(self) -> When[AReadingPlace, AppConfigFragmentAdapter, ByNames]:
        return ReadingMineByNames()

    @override
    def then(self) -> Then[AReadingPlace, ByNames]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheGrantedUserReadsTheDomains(
    Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, ByNames]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-the-domain-reads-its-fragment-by-name"

    @override
    def describe(self) -> str:
        return "도메인 조각이 있고 그 도메인 스코프에 읽기 권한을 받은 사용자가 도메인을 지정해 조회하면, 그 조각이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ATargetAndACaller]:
        return SomewhereToTarget(
            target=Target.HOME_DOMAIN, laid={"theme": "domain"}, granted=(Permission.READ,)
        )

    @override
    def when(self) -> When[ATargetAndACaller, AppConfigFragmentAdapter, ByNames]:
        return ReadingAtByName()

    @override
    def then(self) -> Then[ATargetAndACaller, ByNames]:
        return TheTargetsFragmentByName()


@dataclass(frozen=True)
class AnyoneSignedInReadsThePublic(
    Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, ByNames]
):
    @override
    def summary(self) -> str:
        return "anyone-signed-in-reads-a-public-fragment-by-name"

    @override
    def describe(self) -> str:
        return (
            "공개 조각이 있고 아무 권한도 없는 사용자가 공개 스코프를 지정해 조회하면, 그 조각이 "
            "반환된다. 공개 조각에는 보호할 스코프가 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, ATargetAndACaller]:
        return SomewhereToTarget(target=Target.PUBLIC, laid={"theme": "public"})

    @override
    def when(self) -> When[ATargetAndACaller, AppConfigFragmentAdapter, ByNames]:
        return ReadingAtByName()

    @override
    def then(self) -> Then[ATargetAndACaller, ByNames]:
        return TheTargetsFragmentByName()


@dataclass(frozen=True)
class AnotherUsersScopeIsRefused(
    Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, ByNames]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-their-own-scope-may-not-read-another-users"

    @override
    def describe(self) -> str:
        return "자기 스코프에만 읽기 권한을 받은 사용자가 다른 사용자를 지정해 조회하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ATargetAndACaller]:
        return SomewhereToTarget(
            target=Target.ANOTHER_USER, laid={"theme": "theirs"}, granted=(Permission.READ,)
        )

    @override
    def when(self) -> When[ATargetAndACaller, AppConfigFragmentAdapter, ByNames]:
        return ReadingAtByName()

    @override
    def then(self) -> Then[ATargetAndACaller, ByNames]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AMissingDomainIsNotFoundForASuperadmin(
    Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, ByNames]
):
    @override
    def summary(self) -> str:
        return "a-domain-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 어느 도메인도 아닌 id를 지정해 조회하면, 대상을 찾을 수 없다는 이유로 거부된다. "
            "권한 검사를 통과하는 사용자만 이 응답을 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, ATargetAndACaller]:
        return SomewhereToTarget(target=Target.HOME_DOMAIN, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATargetAndACaller, AppConfigFragmentAdapter, ByNames]:
        return ReadingElsewhereByName()

    @override
    def then(self) -> Then[ATargetAndACaller, ByNames]:
        return TheCallIsRefused(DomainNotFound)


@dataclass(frozen=True)
class AMissingDomainIsRefusedAsPermission(
    Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, ByNames]
):
    @override
    def summary(self) -> str:
        return "a-domain-nothing-answers-to-is-refused-as-permission-for-a-plain-user"

    @override
    def describe(self) -> str:
        return (
            "자기 도메인에 읽기 권한을 받은 사용자가 어느 도메인도 아닌 id를 지정해 조회하면, "
            "대상 없음이 아니라 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ATargetAndACaller]:
        return SomewhereToTarget(target=Target.HOME_DOMAIN, granted=(Permission.READ,))

    @override
    def when(self) -> When[ATargetAndACaller, AppConfigFragmentAdapter, ByNames]:
        return ReadingElsewhereByName()

    @override
    def then(self) -> Then[ATargetAndACaller, ByNames]:
        return TheCallIsRefused(NotEnoughPermission)


MINE_SCENARIOS: list[MineStep] = [
    EachNameIsAnsweredInOrder(),
    AnotherUsersFragmentStaysOut(),
    TheDomainsFragmentStaysOut(),
    AUserGrantedNothingMayNotReadMine(),
]

SCOPED_SCENARIOS: list[ScopedStep] = [
    TheGrantedUserReadsTheDomains(),
    AnyoneSignedInReadsThePublic(),
    AnotherUsersScopeIsRefused(),
    AMissingDomainIsNotFoundForASuperadmin(),
    AMissingDomainIsRefusedAsPermission(),
]


@pytest.mark.parametrize("scenario", MINE_SCENARIOS, ids=lambda s: s.summary())
async def test_reading_mine_by_names(
    scenario: MineStep, adapter: AppConfigFragmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", SCOPED_SCENARIOS, ids=lambda s: s.summary())
async def test_reading_at_a_scope_by_names(
    scenario: ScopedStep, adapter: AppConfigFragmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
