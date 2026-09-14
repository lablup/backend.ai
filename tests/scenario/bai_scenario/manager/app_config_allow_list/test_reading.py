"""허용 목록 항목 조회 — 개별 엔티티 권한 검사를 확인한다.

허용 목록 항목은 도메인·프로젝트·사용자 스코프에 자동 귀속되지 않는다. 따라서 현재 기본
역할로는 도달할 수 없으며, 슈퍼관리자만 조회할 수 있다.
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
from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.data.user.types import UserRole
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

type ReadingStep = Scenario[
    SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode
]


@dataclass(frozen=True)
class ReadingById(When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]):
    """ID로 조회한다. ID를 지정하지 않으면 준비한 항목의 ID를 쓴다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "admin_get"

    @override
    def describe(self, laid: AnEntryAndACaller) -> str:
        called = "존재하지 않는 ID" if self.other is not None else f"{laid.name}의 항목"
        return f"{laid.caller.username}이 {called} 조회"

    @override
    async def call(
        self, adapter: AppConfigAllowListAdapter, laid: AnEntryAndACaller
    ) -> AppConfigAllowListNode:
        if self.other is not None:
            wanted = AppConfigAllowListID(self.other)
        elif laid.entry is not None:
            wanted = laid.entry.id
        else:
            raise LookupError("this row lays no entry to read")
        with ActingAs(laid.caller):
            return await adapter.admin_get(wanted)


@dataclass(frozen=True)
class TheSuperadminReadsIt(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-an-entry-by-id"

    @override
    def describe(self) -> str:
        return "항목 하나가 있고 슈퍼관리자가 ID로 조회하면, 그 항목의 모든 필드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheEntryNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-read-an-entry"

    @override
    def describe(self) -> str:
        return "같은 항목을 권한이 없는 일반 사용자가 조회하면, 엔티티 읽기 권한이 없어 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return ReadingById()

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
            "슈퍼관리자가 존재하지 않는 ID로 조회하면, 대상을 찾을 수 없다는 이유로 거부된다. "
            "권한 검사를 통과하는 사용자만 이 응답을 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return ReadingById(other=uuid4())

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[ReadingStep] = [
    TheSuperadminReadsIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
