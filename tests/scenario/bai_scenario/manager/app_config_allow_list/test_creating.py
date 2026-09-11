"""허용 항목 만들기 — 누가 열 수 있고, 순위를 생략하면 무엇이 되는가.

순위 생략을 세 줄로 두는 이유는, 생략했을 때의 값이 스코프 종류마다 다르고 그 값이 병합의
기본 순서이기 때문이다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config import ENFORCEMENT
from bai_scenario.components.app_config_allow_list import (
    AnEntryAndACaller,
    AnEntryAndSomeone,
    TheNewEntryNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.app_config.allow_list import SCOPE_NAMES

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    CreateAppConfigAllowListInput,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    AppConfigAllowListNode,
)
from ai.backend.manager.api.adapters.app_config_allow_list.adapter import (
    AppConfigAllowListAdapter,
)
from ai.backend.manager.errors.app_config import AppConfigDefinitionNotFound
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type CreatingStep = Scenario[
    SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode
]


@dataclass(frozen=True)
class Opening(When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]):
    """심은 이름을 한 스코프 종류에 연다. 순위를 대지 않으면 생략한다."""

    scope_type: AppConfigScopeType
    rank: int | None = None

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: AnEntryAndACaller) -> str:
        how = f"순위 {self.rank}로" if self.rank is not None else "순위 없이"
        return (
            f"{laid.caller.username}이 {laid.name}을 {SCOPE_NAMES[self.scope_type]} 종류에 {how} 엶"
        )

    @override
    async def call(
        self, adapter: AppConfigAllowListAdapter, laid: AnEntryAndACaller
    ) -> AppConfigAllowListNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_create(
                CreateAppConfigAllowListInput(
                    config_name=laid.name, scope_type=self.scope_type, rank=self.rank
                )
            )
        return payload.app_config_allow_list


@dataclass(frozen=True)
class LeavingTheRankOutTakesTheDefault(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]
):
    started: datetime
    scope_type: AppConfigScopeType

    @override
    def summary(self) -> str:
        return f"leaving-the-rank-out-opens-the-{self.scope_type.value}-kind-at-its-default-rank"

    @override
    def describe(self) -> str:
        return (
            f"슈퍼관리자가 순위를 생략하고 {SCOPE_NAMES[self.scope_type]} 종류의 허용 항목을 "
            f"만들면, 순위 {self.scope_type.default_rank()}이 매겨진다. 이 문은 전역 역할이다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=None, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return Opening(scope_type=self.scope_type)

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheNewEntryNode(
            started=self.started, scope_type=self.scope_type, rank=self.scope_type.default_rank()
        )


@dataclass(frozen=True)
class AGivenRankIsKept(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-rank-given-in-the-request-is-kept-as-is"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 기본값 사이의 순위를 주고 허용 항목을 만들면, 그 값이 그대로 저장된다"

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=None, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return Opening(scope_type=AppConfigScopeType.DOMAIN, rank=250)

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheNewEntryNode(started=self.started, scope_type=AppConfigScopeType.DOMAIN, rank=250)


@dataclass(frozen=True)
class AnUnregisteredNameIsRefused(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]
):
    @override
    def summary(self) -> str:
        return "a-name-nothing-registers-cannot-be-opened"

    @override
    def describe(self) -> str:
        return "같은 이름의 정의가 없을 때 슈퍼관리자가 허용 항목을 만들려 하면, 정의 없음으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(defined=False, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return Opening(scope_type=AppConfigScopeType.PUBLIC)

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheCallIsRefused(AppConfigDefinitionNotFound)


@dataclass(frozen=True)
class OpeningTheSameKindTwiceIsRefused(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]
):
    @override
    def summary(self) -> str:
        return "opening-the-same-name-to-the-same-kind-twice-is-refused-as-a-constraint-violation"

    @override
    def describe(self) -> str:
        return (
            "이미 그 종류에 열린 이름을 슈퍼관리자가 같은 종류에 다시 열면 거부되지만, 답이 "
            "겹친다고 말하지 않고 데이터베이스의 제약 위반이 그대로 올라온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.PUBLIC, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return Opening(scope_type=AppConfigScopeType.PUBLIC)

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class APlainUserMayNotOpen(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-open-a-name"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 허용 항목을 만들려 하면, 역할로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=None)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return Opening(scope_type=AppConfigScopeType.PUBLIC)

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffChangesNothing(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-does-not-let-a-user-open-a-name"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 꺼도 허용 항목 만들기는 여전히 막힌다. "
            "이 문은 권한 그래프가 아니라 역할이 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=None)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return Opening(scope_type=AppConfigScopeType.PUBLIC)

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    LeavingTheRankOutTakesTheDefault(
        started=datetime.now(UTC), scope_type=AppConfigScopeType.PUBLIC
    ),
    LeavingTheRankOutTakesTheDefault(
        started=datetime.now(UTC), scope_type=AppConfigScopeType.DOMAIN
    ),
    LeavingTheRankOutTakesTheDefault(started=datetime.now(UTC), scope_type=AppConfigScopeType.USER),
    AGivenRankIsKept(started=datetime.now(UTC)),
    AnUnregisteredNameIsRefused(),
    OpeningTheSameKindTwiceIsRefused(),
    APlainUserMayNotOpen(),
    EnforcementOffChangesNothing(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
