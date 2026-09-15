"""설정 조각 쓰기 — 누가 어디에 쓸 수 있고, 허용 목록 항목이 무엇을 막는가.

자기 조각 쓰기와 지정한 스코프에 쓰기가 한 모듈에 있다. 소유자가 있는 쓰기는 그 소유자의
스코프에 부여된 권한을 검사하고, 공개 조각 쓰기는 대응하는 스코프가 없어 전역 역할이 있어야
한다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config import ENFORCEMENT
from bai_scenario.components.app_config_fragment import (
    WRITING,
    ATargetAndACaller,
    AWritingPlace,
    MyWritingPlace,
    SomewhereToTarget,
    Target,
    TheWrittenFragments,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.app_config.allow_list import SCOPE_NAMES

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config import AppConfigScopeID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentUpsertItem,
    AppConfigScopeRef,
    MyUpsertAppConfigFragmentsInput,
    ScopedUpsertAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    UpsertAppConfigFragmentsPayload,
)
from ai.backend.manager.api.adapters.app_config_fragment.adapter import AppConfigFragmentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.app_config import AppConfigFragmentWriteNotAllowed
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission, VirtualEntityNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type Written = UpsertAppConfigFragmentsPayload
type MineStep = Scenario[SeedingSession, AWritingPlace, AppConfigFragmentAdapter, Written]
type ScopedStep = Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, Written]

FIRST: Mapping[str, Any] = MappingProxyType({"theme": "light", "menu": {"home": True}})
SECOND: Mapping[str, Any] = MappingProxyType({"editor": {"wrap": True}})
REPLACED: Mapping[str, Any] = MappingProxyType({"menu": {"docs": True}})


@dataclass(frozen=True)
class WritingMine(When[AWritingPlace, AppConfigFragmentAdapter, Written]):
    """자기 스코프에 쓴다. 이름은 미리 만들어 둔 것에서, 값은 시나리오가 정한 것에서 읽는다."""

    configs: tuple[Mapping[str, Any], ...] = (FIRST,)

    @override
    def operation(self) -> str:
        return "my_upsert_app_config_fragments"

    @override
    def describe(self, laid: AWritingPlace) -> str:
        return f"{laid.caller.username}이 {', '.join(laid.names)}에 자기 조각 쓰기"

    @override
    async def call(self, adapter: AppConfigFragmentAdapter, laid: AWritingPlace) -> Written:
        items = [
            AppConfigFragmentUpsertItem(config_name=name, config=dict(config))
            for name, config in zip(laid.names, self.configs, strict=True)
        ]
        with ActingAs(laid.caller):
            return await adapter.my_upsert_app_config_fragments(
                MyUpsertAppConfigFragmentsInput(items=items)
            )


@dataclass(frozen=True)
class WritingAt(When[ATargetAndACaller, AppConfigFragmentAdapter, Written]):
    """지정한 스코프에 쓴다."""

    config: Mapping[str, Any] = FIRST

    @override
    def operation(self) -> str:
        return "scoped_upsert_app_config_fragments"

    @override
    def describe(self, laid: ATargetAndACaller) -> str:
        return f"{laid.caller.username}이 {SCOPE_NAMES[laid.scope_type]} 스코프를 지정해 {laid.name}에 조각 쓰기"

    @override
    async def call(self, adapter: AppConfigFragmentAdapter, laid: ATargetAndACaller) -> Written:
        scope = AppConfigScopeRef(
            scope_type=laid.scope_type,
            scope_id=AppConfigScopeID(laid.scope_id) if laid.scope_id is not None else None,
        )
        with ActingAs(laid.caller):
            return await adapter.scoped_upsert_app_config_fragments(
                ScopedUpsertAppConfigFragmentsInput(
                    scope=scope,
                    items=[
                        AppConfigFragmentUpsertItem(config_name=laid.name, config=dict(self.config))
                    ],
                )
            )


@dataclass(frozen=True)
class TheGrantedUserWritesTheirFirstFragment(
    Scenario[SeedingSession, AWritingPlace, AppConfigFragmentAdapter, Written]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-write-writes-their-first-own-fragment"

    @override
    def describe(self) -> str:
        return (
            "쓰기 권한을 받은 사용자가 자기 조각을 처음 쓰면, 요청이 지정하지 않은 소유자와 스코프 "
            "종류가 호출자 정보로 채워진 노드가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AWritingPlace]:
        return MyWritingPlace(granted=WRITING)

    @override
    def when(self) -> When[AWritingPlace, AppConfigFragmentAdapter, Written]:
        return WritingMine()

    @override
    def then(self) -> Then[AWritingPlace, Written]:
        return TheWrittenFragments(started=self.started, configs=(FIRST,))


@dataclass(frozen=True)
class WritingAgainReplacesTheValueWhole(
    Scenario[SeedingSession, AWritingPlace, AppConfigFragmentAdapter, Written]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "writing-the-same-name-again-replaces-the-value-whole"

    @override
    def describe(self) -> str:
        return (
            "이미 자기 조각이 있는 이름에 다른 키를 담아 다시 쓰면, id는 그대로인 채 값은 "
            "새 값뿐이다. 이전 키가 남지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AWritingPlace]:
        return MyWritingPlace(granted=WRITING, existing=FIRST)

    @override
    def when(self) -> When[AWritingPlace, AppConfigFragmentAdapter, Written]:
        return WritingMine(configs=(REPLACED,))

    @override
    def then(self) -> Then[AWritingPlace, Written]:
        return TheWrittenFragments(started=self.started, configs=(REPLACED,), replacing=True)


@dataclass(frozen=True)
class SeveralNamesAreWrittenAtOnce(
    Scenario[SeedingSession, AWritingPlace, AppConfigFragmentAdapter, Written]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "several-names-are-written-at-once-in-request-order"

    @override
    def describe(self) -> str:
        return "사용자 스코프에 허용된 이름 둘에 한 번에 쓰면, 둘 다 쓰이고 요청 순서대로 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AWritingPlace]:
        return MyWritingPlace(granted=WRITING, more_opened=1)

    @override
    def when(self) -> When[AWritingPlace, AppConfigFragmentAdapter, Written]:
        return WritingMine(configs=(FIRST, SECOND))

    @override
    def then(self) -> Then[AWritingPlace, Written]:
        return TheWrittenFragments(started=self.started, configs=(FIRST, SECOND))


@dataclass(frozen=True)
class OneNameNotAllowedSinksTheWholeWrite(
    Scenario[SeedingSession, AWritingPlace, AppConfigFragmentAdapter, Written]
):
    @override
    def summary(self) -> str:
        return "one-name-not-opened-to-the-user-kind-refuses-the-whole-write"

    @override
    def describe(self) -> str:
        return (
            "허용된 이름과 허용되지 않은 이름을 함께 쓰면, 쓰기 허용 안 됨으로 거부된다. 쓰기는 "
            "전부 아니면 전무다"
        )

    @override
    def given(self) -> Given[SeedingSession, AWritingPlace]:
        return MyWritingPlace(granted=WRITING, more_unopened=1)

    @override
    def when(self) -> When[AWritingPlace, AppConfigFragmentAdapter, Written]:
        return WritingMine(configs=(FIRST, SECOND))

    @override
    def then(self) -> Then[AWritingPlace, Written]:
        return TheCallIsRefused(AppConfigFragmentWriteNotAllowed)


@dataclass(frozen=True)
class AnUnregisteredNameIsRefused(
    Scenario[SeedingSession, AWritingPlace, AppConfigFragmentAdapter, Written]
):
    @override
    def summary(self) -> str:
        return "a-name-nothing-registers-cannot-be-written"

    @override
    def describe(self) -> str:
        return "등록되지 않은 이름에 쓰기 권한을 받은 사용자가 쓰면, 쓰기 허용 안 됨으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AWritingPlace]:
        return MyWritingPlace(granted=WRITING, defined=False)

    @override
    def when(self) -> When[AWritingPlace, AppConfigFragmentAdapter, Written]:
        return WritingMine()

    @override
    def then(self) -> Then[AWritingPlace, Written]:
        return TheCallIsRefused(AppConfigFragmentWriteNotAllowed)


@dataclass(frozen=True)
class ANameOpenedToAnotherKindIsRefused(
    Scenario[SeedingSession, AWritingPlace, AppConfigFragmentAdapter, Written]
):
    @override
    def summary(self) -> str:
        return "a-name-opened-only-to-the-domain-kind-cannot-be-written-by-a-user"

    @override
    def describe(self) -> str:
        return (
            "도메인 종류에만 허용된 이름에 쓰기 권한을 받은 사용자가 자기 조각을 쓰면, 쓰기 허용 "
            "안 됨으로 거부된다. 등록되지 않은 이름과 같은 검사다"
        )

    @override
    def given(self) -> Given[SeedingSession, AWritingPlace]:
        return MyWritingPlace(granted=WRITING, kinds=(AppConfigScopeType.DOMAIN,))

    @override
    def when(self) -> When[AWritingPlace, AppConfigFragmentAdapter, Written]:
        return WritingMine()

    @override
    def then(self) -> Then[AWritingPlace, Written]:
        return TheCallIsRefused(AppConfigFragmentWriteNotAllowed)


@dataclass(frozen=True)
class CreateAloneIsNotEnough(
    Scenario[SeedingSession, AWritingPlace, AppConfigFragmentAdapter, Written]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-create-alone-may-not-write"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에 생성 권한만 있고 수정 권한이 없는 사용자가 쓰면, 권한 부족으로 "
            "거부된다. 쓰기는 생성과 수정 권한 둘 다를 요구한다"
        )

    @override
    def given(self) -> Given[SeedingSession, AWritingPlace]:
        return MyWritingPlace(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[AWritingPlace, AppConfigFragmentAdapter, Written]:
        return WritingMine()

    @override
    def then(self) -> Then[AWritingPlace, Written]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotWrite(
    Scenario[SeedingSession, AWritingPlace, AppConfigFragmentAdapter, Written]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-write-their-own-fragment"

    @override
    def describe(self) -> str:
        return "사용자 종류에 허용된 이름에 아무 권한도 없는 사용자가 쓰면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AWritingPlace]:
        return MyWritingPlace()

    @override
    def when(self) -> When[AWritingPlace, AppConfigFragmentAdapter, Written]:
        return WritingMine()

    @override
    def then(self) -> Then[AWritingPlace, Written]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneWrite(
    Scenario[SeedingSession, AWritingPlace, AppConfigFragmentAdapter, Written], Configured
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-granted-nothing-write"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 끄면 아무 권한도 없는 사용자도 자기 조각을 쓸 수 있다. "
            "자기 조각 쓰기는 역할이 아니라 권한 그래프로 보호되므로 스위치가 영향을 준다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AWritingPlace]:
        return MyWritingPlace()

    @override
    def when(self) -> When[AWritingPlace, AppConfigFragmentAdapter, Written]:
        return WritingMine()

    @override
    def then(self) -> Then[AWritingPlace, Written]:
        return TheWrittenFragments(started=self.started, configs=(FIRST,))


@dataclass(frozen=True)
class TheGrantedUserWritesADomainFragment(
    Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, Written]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-write-on-the-domain-writes-a-domain-fragment"

    @override
    def describe(self) -> str:
        return "자기 도메인 스코프에 쓰기 권한을 받은 사용자가 도메인을 지정해 쓰면, 스코프 종류는 도메인이고 소유자는 그 도메인이다"

    @override
    def given(self) -> Given[SeedingSession, ATargetAndACaller]:
        return SomewhereToTarget(target=Target.HOME_DOMAIN, granted=WRITING)

    @override
    def when(self) -> When[ATargetAndACaller, AppConfigFragmentAdapter, Written]:
        return WritingAt()

    @override
    def then(self) -> Then[ATargetAndACaller, Written]:
        return TheWrittenFragments(started=self.started, configs=(FIRST,))


@dataclass(frozen=True)
class TheSuperadminWritesAPublicFragment(
    Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, Written]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-writes-a-public-fragment-owned-by-no-one"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 공개 스코프를 지정해 쓰면, 스코프 종류는 공개이고 소유자 필드는 비어 있다. 공개 쓰기는 전역 역할로 보호된다"

    @override
    def given(self) -> Given[SeedingSession, ATargetAndACaller]:
        return SomewhereToTarget(target=Target.PUBLIC, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATargetAndACaller, AppConfigFragmentAdapter, Written]:
        return WritingAt()

    @override
    def then(self) -> Then[ATargetAndACaller, Written]:
        return TheWrittenFragments(started=self.started, configs=(FIRST,))


@dataclass(frozen=True)
class APlainUserMayNotWritePublic(
    Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, Written]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-write-a-public-fragment"

    @override
    def describe(self) -> str:
        return (
            "자기 도메인 스코프에 쓰기 권한을 받았어도 슈퍼관리자가 아닌 사용자가 공개 스코프를 "
            "지정해 쓰면, 역할 부족으로 거부된다. 공개 조각에는 대응하는 스코프가 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, ATargetAndACaller]:
        return SomewhereToTarget(target=Target.PUBLIC, granted=WRITING)

    @override
    def when(self) -> When[ATargetAndACaller, AppConfigFragmentAdapter, Written]:
        return WritingAt()

    @override
    def then(self) -> Then[ATargetAndACaller, Written]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffDoesNotOpenPublic(
    Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, Written], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-does-not-let-a-user-write-a-public-fragment"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 꺼도 슈퍼관리자가 아니면 공개 조각을 쓸 수 없다. "
            "공개 쓰기는 권한 그래프가 아니라 역할로 보호되기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ATargetAndACaller]:
        return SomewhereToTarget(target=Target.PUBLIC)

    @override
    def when(self) -> When[ATargetAndACaller, AppConfigFragmentAdapter, Written]:
        return WritingAt()

    @override
    def then(self) -> Then[ATargetAndACaller, Written]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AnotherUsersScopeIsRefused(
    Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, Written]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-write-on-their-own-scope-may-not-write-at-another-users"

    @override
    def describe(self) -> str:
        return "자기 스코프에만 쓰기 권한을 받은 사용자가 다른 사용자를 지정해 쓰면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ATargetAndACaller]:
        return SomewhereToTarget(target=Target.ANOTHER_USER, granted=WRITING)

    @override
    def when(self) -> When[ATargetAndACaller, AppConfigFragmentAdapter, Written]:
        return WritingAt()

    @override
    def then(self) -> Then[ATargetAndACaller, Written]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnOwnerNothingAnswersToIsRefused(
    Scenario[SeedingSession, ATargetAndACaller, AppConfigFragmentAdapter, Written]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-naming-an-owner-nothing-answers-to-is-refused"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 어느 사용자도 아닌 id를 소유자로 지정해 쓰면, 소유자 없음으로 "
            "거부된다. 소유자가 있는지는 권한 그래프에서 확인한다"
        )

    @override
    def given(self) -> Given[SeedingSession, ATargetAndACaller]:
        return SomewhereToTarget(target=Target.NOBODY, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATargetAndACaller, AppConfigFragmentAdapter, Written]:
        return WritingAt()

    @override
    def then(self) -> Then[ATargetAndACaller, Written]:
        return TheCallIsRefused(VirtualEntityNotFound)


MINE_SCENARIOS: list[MineStep] = [
    TheGrantedUserWritesTheirFirstFragment(started=datetime.now(UTC)),
    WritingAgainReplacesTheValueWhole(started=datetime.now(UTC)),
    SeveralNamesAreWrittenAtOnce(started=datetime.now(UTC)),
    OneNameNotAllowedSinksTheWholeWrite(),
    AnUnregisteredNameIsRefused(),
    ANameOpenedToAnotherKindIsRefused(),
    CreateAloneIsNotEnough(),
    AUserGrantedNothingMayNotWrite(),
    EnforcementOffLetsAnyoneWrite(started=datetime.now(UTC)),
]

SCOPED_SCENARIOS: list[ScopedStep] = [
    TheGrantedUserWritesADomainFragment(started=datetime.now(UTC)),
    TheSuperadminWritesAPublicFragment(started=datetime.now(UTC)),
    APlainUserMayNotWritePublic(),
    EnforcementOffDoesNotOpenPublic(),
    AnotherUsersScopeIsRefused(),
    AnOwnerNothingAnswersToIsRefused(),
]


@pytest.mark.parametrize("scenario", MINE_SCENARIOS, ids=lambda s: s.summary())
async def test_writing_mine(
    scenario: MineStep, adapter: AppConfigFragmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", SCOPED_SCENARIOS, ids=lambda s: s.summary())
async def test_writing_at_a_scope(
    scenario: ScopedStep, adapter: AppConfigFragmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
