"""설정 정의 조회 — 슈퍼관리자만 조회할 수 있다.

설정 정의는 어느 스코프에도 속하지 않아 역할이 미치지 않는다. 슈퍼관리자는 통과하고 그 밖의
사용자는 권한 부족으로 거부되며, 존재하지 않는 id는 슈퍼관리자에게만 대상 없음으로 응답한다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config import ENFORCEMENT
from bai_scenario.components.app_config_definition import (
    ADefinitionAndACaller,
    ADefinitionAndSomeone,
    TheDefinitionNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    AppConfigDefinitionNode,
)
from ai.backend.manager.api.adapters.app_config_definition.adapter import (
    AppConfigDefinitionAdapter,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type ReadingStep = Scenario[
    SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
]


@dataclass(frozen=True)
class ReadingById(When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]):
    """id로 조회한다. id를 지정하지 않으면 미리 만들어 둔 정의의 id를 쓴다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "admin_get"

    @override
    def describe(self, laid: ADefinitionAndACaller) -> str:
        called = "존재하지 않는 id" if self.other is not None else laid.definition.config_name
        return f"{laid.caller.username}이 {called}(으)로 조회"

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ADefinitionAndACaller
    ) -> AppConfigDefinitionNode:
        wanted = AppConfigDefinitionID(self.other) if self.other is not None else laid.definition.id
        with ActingAs(laid.caller):
            return await adapter.admin_get(wanted)


@dataclass(frozen=True)
class TheSuperadminReadsIt(
    Scenario[
        SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-definition-by-id"

    @override
    def describe(self) -> str:
        return "설정 정의 하나가 있고 슈퍼관리자가 id로 조회하면, 그 정의 전체가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ADefinitionAndACaller, AppConfigDefinitionNode]:
        return TheDefinitionNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[
        SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-read-a-definition"

    @override
    def describe(self) -> str:
        return (
            "같은 설정 정의가 있고 슈퍼관리자가 아닌 사용자가 조회하면, 권한 부족으로 거부된다. "
            "설정 정의는 어느 스코프에도 속하지 않아 역할로는 권한을 받을 수 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone()

    @override
    def when(
        self,
    ) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ADefinitionAndACaller, AppConfigDefinitionNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[
        SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
    ]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 존재하지 않는 id로 조회하면, 대상을 찾을 수 없다는 이유로 거부된다. "
            "권한 검사를 통과하는 사용자만 이 응답을 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]:
        return ReadingById(other=uuid4())

    @override
    def then(self) -> Then[ADefinitionAndACaller, AppConfigDefinitionNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneRead(
    Scenario[
        SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
    ],
    Configured,
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-plain-user-read"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 끄면 아무 권한도 없는 사용자도 설정 정의를 조회할 수 있다. "
            "조회는 역할이 아니라 권한 그래프로 보호되므로 스위치가 영향을 준다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone()

    @override
    def when(
        self,
    ) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ADefinitionAndACaller, AppConfigDefinitionNode]:
        return TheDefinitionNode(started=self.started)


SCENARIOS: list[ReadingStep] = [
    TheSuperadminReadsIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    AnUnknownIdIsNotFoundForASuperadmin(),
    EnforcementOffLetsAnyoneRead(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: AppConfigDefinitionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
