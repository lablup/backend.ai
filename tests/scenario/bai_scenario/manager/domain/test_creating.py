"""도메인 만들기 — 누가 만들 수 있고, 무엇이 이름을 막는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.domain import (
    WAS_HERE,
    ADomainAndACaller,
    ADomainAndSomeone,
    TheCallIsRefused,
    TheNewDomainNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.request import CreateDomainInput
from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)

FRESH = "새로 만든 도메인"
ENFORCEMENT = "manager.rbac.enforcement_enabled"

type DomainStep = Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]


@dataclass(frozen=True)
class Creating(When[ADomainAndACaller, DomainAdapter, DomainNode]):
    """도메인을 만든다. 이름을 대지 않으면 심은 도메인의 이름을 그대로 쓴다."""

    named: str | None = None
    described: str | None = None

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return f"{laid.caller.username}이 {self.named or laid.domain.name}으로 만듦"

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> DomainNode:
        with ActingAs(laid.caller) as who:
            payload = await adapter.admin_create(
                CreateDomainInput(name=self.named or laid.domain.name, description=self.described),
                who,
            )
        return payload.domain


@dataclass(frozen=True)
class TheWholeNodeComesBack(Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]):
    started: datetime

    @override
    def summary(self) -> str:
        return "creating-a-domain-answers-with-the-whole-node"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 이름과 설명만 주고 도메인을 만들면, "
            "요청에 없던 값들은 기본값으로 채워진 노드 전체가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return Creating(named="new-domain", described=FRESH)

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheNewDomainNode(started=self.started, named="new-domain", described=FRESH)


@dataclass(frozen=True)
class ANameAnotherDomainHoldsIsRefused(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    @override
    def summary(self) -> str:
        return "a-name-another-domain-already-holds-is-refused"

    @override
    def describe(self) -> str:
        return (
            "이미 어떤 도메인이 쓰고 있는 이름으로 만들려 하면, "
            "권한이 있어도 이름이 겹친다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN, name_hint="taken")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return Creating(described=WAS_HERE)

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class ABlankNameIsRefused(Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]):
    @override
    def summary(self) -> str:
        return "a-blank-name-is-refused"

    @override
    def describe(self) -> str:
        return "이름이 공백뿐이면 도메인을 만들 수 없다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return Creating(named="   ")

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class APlainUserMayNotCreate(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-domain"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 도메인을 만들려 하면, "
            "권한을 얼마나 받았는지와 무관하게 역할로 막힌다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone()

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return Creating(named="by-a-user")

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffChangesNothing(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-does-not-let-a-user-create-a-domain"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 꺼도 도메인 생성은 여전히 막힌다. "
            "이 문은 권한 그래프가 아니라 역할이 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone()

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return Creating(named="by-a-user-again")

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[DomainStep] = [
    TheWholeNodeComesBack(started=datetime.now(UTC)),
    ANameAnotherDomainHoldsIsRefused(),
    ABlankNameIsRefused(),
    APlainUserMayNotCreate(),
    EnforcementOffChangesNothing(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
