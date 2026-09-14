"""허용 목록 항목 수정 — 순위와 개별 엔티티 권한을 확인한다.

설정 이름과 스코프 유형은 항목의 정체성이므로 요청 타입이 받지 않는다. 순위를 바꾼 뒤 병합의 우선순위가
뒤바뀌는 것은 병합 조회 시나리오가 순위를 처음부터 뒤집어 만들어 두고 확인한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_allow_list import (
    AnEntryAndACaller,
    AnEntryAndSomeone,
    TheEntryNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    UpdateAppConfigAllowListInput,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    AppConfigAllowListNode,
)
from ai.backend.manager.api.adapters.app_config_allow_list.adapter import (
    AppConfigAllowListAdapter,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type EditingStep = Scenario[
    SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode
]


@dataclass(frozen=True)
class ChangingTheRank(When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]):
    """순위를 수정한다. ID를 지정하지 않으면 준비한 항목을 수정한다."""

    rank: int | None = None
    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "admin_update"

    @override
    def describe(self, laid: AnEntryAndACaller) -> str:
        called = "존재하지 않는 ID" if self.other is not None else f"{laid.name}의 항목"
        how = f"순위 {self.rank}(으)로 변경" if self.rank is not None else "빈 요청"
        return f"{laid.caller.username}이 {called} 수정 ({how})"

    @override
    async def call(
        self, adapter: AppConfigAllowListAdapter, laid: AnEntryAndACaller
    ) -> AppConfigAllowListNode:
        if self.other is not None:
            wanted = self.other
        elif laid.entry is not None:
            wanted = laid.entry.id
        else:
            raise LookupError("this row lays no entry to edit")
        with ActingAs(laid.caller):
            payload = await adapter.admin_update(
                UpdateAppConfigAllowListInput(id=wanted, rank=self.rank)
            )
        return payload.app_config_allow_list


@dataclass(frozen=True)
class TheSuperadminChangesTheRank(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-changes-an-entrys-rank"

    @override
    def describe(self) -> str:
        return "항목 하나가 있고 슈퍼관리자가 순위를 바꾸면, 순위만 변경되고 설정 이름과 스코프 유형은 그대로다"

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return ChangingTheRank(rank=150)

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheEntryNode(started=self.started, rank=150)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-edit-carrying-no-value-changes-nothing"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아무 값도 지정하지 않고 수정하면, 아무것도 바뀌지 않은 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return ChangingTheRank()

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheEntryNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-change-a-rank"

    @override
    def describe(self) -> str:
        return "같은 항목을 권한이 없는 일반 사용자가 수정하면, 엔티티 수정 권한이 없어 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return ChangingTheRank(rank=150)

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 존재하지 않는 ID의 순위를 수정하면, 대상을 찾을 수 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return ChangingTheRank(rank=150, other=uuid4())

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[EditingStep] = [
    TheSuperadminChangesTheRank(started=datetime.now(UTC)),
    AnEmptyEditChangesNothing(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotEdit(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
