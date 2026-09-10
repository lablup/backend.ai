"""도메인 수정 — 무엇이 바뀌고 무엇이 그대로 남는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest
from bai_scenario.components.domain import (
    ADomainAndACaller,
    ADomainAndSomeone,
    TheCallIsRefused,
    TheDomainNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.request import UpdateDomainInput
from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

EDITED = "고쳐 쓴 설명"

type DomainStep = Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]


@dataclass(frozen=True)
class Editing(When[ADomainAndACaller, DomainAdapter, DomainNode]):
    """심은 도메인을 고친다. 답이 실은 노드를 벗겨서 준다."""

    asked: UpdateDomainInput
    named: str | None = None
    changing: str = "설명"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        target = self.named or laid.domain.name
        return f"{laid.caller.username}이 {target}의 {self.changing}을 고침"

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> DomainNode:
        with ActingAs(laid.caller) as who:
            payload = await adapter.admin_update(self.named or laid.domain.name, self.asked, who)
        return payload.domain


@dataclass(frozen=True)
class TheDescriptionChangesAndTheNameStays(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "editing-a-description-leaves-the-name-alone"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 도메인의 설명만 바꾸면, 설명은 새 값이 되고 이름은 그대로 남는다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN, name_hint="editable")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return Editing(UpdateDomainInput(description=EDITED))

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheDomainNode(started=self.started, described=EDITED)


@dataclass(frozen=True)
class ClearingTheActiveFlagRetires(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "clearing-the-active-flag-is-how-a-domain-retires"

    @override
    def describe(self) -> str:
        return "활성 플래그를 내리는 수정으로 도메인을 물릴 수 있고, 답이 그 상태를 실어 온다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN, name_hint="to-retire")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return Editing(UpdateDomainInput(is_active=False), changing="활성 플래그")

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheDomainNode(started=self.started, active=False)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-domain"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 도메인을 수정하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone()

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return Editing(UpdateDomainInput(description=EDITED))

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    @override
    def summary(self) -> str:
        return "editing-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "아무 도메인도 갖지 않은 이름을 수정하려 하면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return Editing(UpdateDomainInput(description=EDITED), named="no-such-domain")

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[DomainStep] = [
    TheDescriptionChangesAndTheNameStays(started=datetime.now(UTC)),
    ClearingTheActiveFlagRetires(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotEdit(),
    ANameNothingAnswersToIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
