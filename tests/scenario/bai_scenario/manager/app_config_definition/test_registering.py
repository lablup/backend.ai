"""정의 등록하기 — 누가 이름을 등록할 수 있고, 무엇이 이름을 막는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config import ENFORCEMENT
from bai_scenario.components.app_config_definition import (
    ADefinitionAndACaller,
    ADefinitionAndSomeone,
    TheNewDefinitionNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    CreateAppConfigDefinitionInput,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    AppConfigDefinitionNode,
)
from ai.backend.manager.api.adapters.app_config_definition.adapter import (
    AppConfigDefinitionAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type RegisteringStep = Scenario[
    SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
]

FRESH = "fresh-config"


@dataclass(frozen=True)
class Registering(When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]):
    """이름을 등록한다. 이름을 대지 않으면 심은 정의의 이름을 그대로 쓴다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: ADefinitionAndACaller) -> str:
        return f"{laid.caller.username}이 {self.named or laid.definition.config_name}을 등록"

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ADefinitionAndACaller
    ) -> AppConfigDefinitionNode:
        wanted = self.named or laid.definition.config_name
        with ActingAs(laid.caller):
            payload = await adapter.admin_create(CreateAppConfigDefinitionInput(config_name=wanted))
        return payload.app_config_definition


@dataclass(frozen=True)
class TheSuperadminRegistersAName(
    Scenario[
        SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-registers-a-name"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 이름만 주고 정의를 등록하면, 이름은 준 그대로이고 id와 시각은 "
            "서버가 채운 노드가 답으로 온다. 이 문은 전역 역할이다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]:
        return Registering(named=FRESH)

    @override
    def then(self) -> Then[ADefinitionAndACaller, AppConfigDefinitionNode]:
        return TheNewDefinitionNode(started=self.started, named=FRESH)


@dataclass(frozen=True)
class ANameAlreadyRegisteredIsRefused(
    Scenario[
        SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-name-already-registered-is-refused-as-a-constraint-violation"

    @override
    def describe(self) -> str:
        return (
            "이미 등록된 이름으로 슈퍼관리자가 다시 등록하면 거부되지만, 답이 이름이 겹친다고 "
            "말하지 않고 데이터베이스의 제약 위반이 그대로 올라온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]:
        return Registering()

    @override
    def then(self) -> Then[ADefinitionAndACaller, AppConfigDefinitionNode]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class APlainUserMayNotRegister(
    Scenario[
        SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-register-a-name"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 정의를 등록하려 하면, 역할로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone()

    @override
    def when(
        self,
    ) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode]:
        return Registering(named=FRESH)

    @override
    def then(self) -> Then[ADefinitionAndACaller, AppConfigDefinitionNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffChangesNothing(
    Scenario[
        SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, AppConfigDefinitionNode
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-does-not-let-a-user-register-a-name"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 꺼도 정의 등록은 여전히 막힌다. "
            "이 문은 권한 그래프가 아니라 역할이 지키기 때문이다"
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
        return Registering(named=FRESH)

    @override
    def then(self) -> Then[ADefinitionAndACaller, AppConfigDefinitionNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[RegisteringStep] = [
    TheSuperadminRegistersAName(started=datetime.now(UTC)),
    ANameAlreadyRegisteredIsRefused(),
    APlainUserMayNotRegister(),
    EnforcementOffChangesNothing(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_registering(
    scenario: RegisteringStep, adapter: AppConfigDefinitionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
