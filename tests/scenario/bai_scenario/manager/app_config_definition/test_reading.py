"""정의 읽기 — 누가 어느 정의를 읽을 수 있는가.

정의는 어느 스코프에도 속하지 않으므로 역할이 앉을 자리는 그 정의 자체뿐이다. 없는 id는
슈퍼관리자와 그렇지 않은 사람에게 다른 것으로 거부된다. 권한 검사가 먼저 도는데 없는 행에는
걸린 권한도 없기 때문이다.
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
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type ReadingStep = Scenario[
    SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
]


@dataclass(frozen=True)
class ReadingById(When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]):
    """id로 읽는다. id를 대지 않으면 심은 정의의 id를 쓴다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "admin_get"

    @override
    def describe(self, laid: ADefinitionAndACaller) -> str:
        called = "아무것도 갖지 않은 id" if self.other is not None else laid.definition.config_name
        return f"{laid.caller.username}이 {called}로 조회"

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ADefinitionAndACaller
    ) -> AppConfigDefinitionNode:
        wanted = AppConfigDefinitionID(self.other) if self.other is not None else laid.definition.id
        with ActingAs(laid.caller):
            return await adapter.admin_get(wanted)


@dataclass(frozen=True)
class TheGrantedUserReadsIt(
    Scenario[
        SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-the-definition-reads-it-by-id"

    @override
    def describe(self) -> str:
        return "정의 하나가 있고 그 정의에 읽기 권한을 받은 사용자가 id로 조회하면, 그 정의 전체가 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(granted=(Permission.READ,))

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
        return "a-user-granted-nothing-may-not-read-a-definition"

    @override
    def describe(self) -> str:
        return "같은 정의가 있고 아무 권한도 받지 않은 사용자가 조회하면, 권한 부족으로 거부된다"

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
class AnUnknownIdIsRefusedAsPermission(
    Scenario[
        SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
    ]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user"

    @override
    def describe(self) -> str:
        return (
            "다른 정의에 읽기 권한을 받은 사용자가 아무것도 갖지 않은 id로 조회하면, 대상이 "
            "없다는 것이 아니라 권한 부족으로 거부된다. 없는 행에는 걸린 권한도 없기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(granted=(Permission.READ,))

    @override
    def when(
        self,
    ) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]:
        return ReadingById(other=uuid4())

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
            "슈퍼관리자가 아무것도 갖지 않은 id로 조회하면, 대상이 없다는 것으로 거부된다. "
            "권한 검사를 지나가는 사람만 이 답을 본다"
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
        return "turning-enforcement-off-lets-a-user-granted-nothing-read"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 정의를 읽는다. "
            "이 문은 역할이 아니라 권한 그래프가 지키므로 스위치가 통한다"
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
    TheGrantedUserReadsIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    AnUnknownIdIsRefusedAsPermission(),
    AnUnknownIdIsNotFoundForASuperadmin(),
    EnforcementOffLetsAnyoneRead(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: AppConfigDefinitionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
