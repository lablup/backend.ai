"""로그인 클라이언트 종류 생성 — 누가 생성할 수 있고, 생성된 노드에 무엇이 담기는가.

이름이 비어 있거나 길이 제한을 넘는 요청은 여기 없다. 요청 타입이 이미 막기 때문이다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.login_client_type import (
    ATypeAndACaller,
    ATypeAndSomeone,
    TheNewTypeNode,
)
from bai_scenario.components.system import ENFORCEMENT, ACaller, SomeoneAlone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_client_type.request import CreateLoginClientTypeInput
from ai.backend.common.dto.manager.v2.login_client_type.response import LoginClientTypeNode
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege, LoginClientTypeConflict
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

MADE = "webui"
DESCRIBED = "새로 지정한 설명"

type CreatingStep = Scenario[SeedingSession, Any, LoginClientTypeAdapter, LoginClientTypeNode]


@dataclass(frozen=True)
class Creating(When[ACaller, LoginClientTypeAdapter, LoginClientTypeNode]):
    """종류 하나를 생성한다. 응답에 담긴 노드를 꺼내서 준다."""

    named: str = MADE
    described: str | None = None

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: ACaller) -> str:
        return f"{laid.caller.username}이 {self.named} 종류를 생성"

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ACaller) -> LoginClientTypeNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_create(
                CreateLoginClientTypeInput(name=self.named, description=self.described)
            )
        return payload.login_client_type


@dataclass(frozen=True)
class CreatingWithTheLaidName(When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]):
    """미리 만들어 둔 종류와 같은 이름으로 생성한다."""

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: ATypeAndACaller) -> str:
        return f"{laid.caller.username}이 이미 있는 이름 {laid.client_type.name}(으)로 다시 생성"

    @override
    async def call(
        self, adapter: LoginClientTypeAdapter, laid: ATypeAndACaller
    ) -> LoginClientTypeNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_create(
                CreateLoginClientTypeInput(name=laid.client_type.name)
            )
        return payload.login_client_type


@dataclass(frozen=True)
class TheSuperadminMakesOneWithANameAlone(
    Scenario[SeedingSession, ACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-login-client-type-with-a-name-alone"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이름만 지정해 생성하면 설명이 비어 있는 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, LoginClientTypeNode]:
        return TheNewTypeNode(started=self.started, named=MADE, described=None)


@dataclass(frozen=True)
class ADescriptionComesBackAsGiven(
    Scenario[SeedingSession, ACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-login-client-type-made-with-a-description-carries-it-back"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이름과 설명을 함께 지정해 생성하면 지정한 값이 그대로 담긴 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Creating(described=DESCRIBED)

    @override
    def then(self) -> Then[ACaller, LoginClientTypeNode]:
        return TheNewTypeNode(started=self.started, named=MADE, described=DESCRIBED)


@dataclass(frozen=True)
class ANameAlreadyTakenIsRefused(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-login-client-type-name-already-taken-is-refused"

    @override
    def describe(self) -> str:
        return "같은 이름의 종류가 이미 있을 때 그 이름으로 다시 생성하면, 이름 중복으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return CreatingWithTheLaidName()

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheCallIsRefused(LoginClientTypeConflict)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotCreate(
    Scenario[SeedingSession, ACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-login-client-type"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 종류를 생성하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, LoginClientTypeNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheSuperadmin(
    Scenario[SeedingSession, ACaller, LoginClientTypeAdapter, LoginClientTypeNode], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-does-not-let-a-user-create-a-login-client-type"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 꺼도 슈퍼관리자가 아니면 종류를 생성하지 못한다. "
            "생성은 권한 그래프가 아니라 역할로 보호되므로 스위치와 무관하다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, LoginClientTypeNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminMakesOneWithANameAlone(started=datetime.now(UTC)),
    ADescriptionComesBackAsGiven(started=datetime.now(UTC)),
    ANameAlreadyTakenIsRefused(),
    AUserWhoIsNotTheSuperadminMayNotCreate(),
    EnforcementOffStillNeedsTheSuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: LoginClientTypeAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
