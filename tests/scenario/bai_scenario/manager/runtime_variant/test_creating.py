"""런타임 변형 생성 — 누가 생성할 수 있고, 생성된 노드에 무엇이 담기는가.

이름이 비어 있거나 길이 제한을 넘는 요청은 여기 없다. 요청 타입이 이미 막으므로 어댑터가
보장하는 것이 아니다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.runtime_variant import (
    AVariantAndACaller,
    AVariantAndSomeone,
    TheNewVariantNode,
)
from bai_scenario.components.system import ENFORCEMENT, ACaller, SomeoneAlone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.runtime_variant.request import CreateRuntimeVariantInput
from ai.backend.common.dto.manager.v2.runtime_variant.response import RuntimeVariantNode
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.resource import RuntimeVariantConflict
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

MADE = "vllm"
DESCRIBED = "새로 지정한 설명"

type CreatingStep = Scenario[SeedingSession, Any, RuntimeVariantAdapter, RuntimeVariantNode]


@dataclass(frozen=True)
class Creating(When[ACaller, RuntimeVariantAdapter, RuntimeVariantNode]):
    """변형 하나를 생성한다. 응답에 담긴 노드를 꺼내서 준다."""

    named: str = MADE
    described: str | None = None

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ACaller) -> str:
        return f"{laid.caller.username}이 {self.named} 변형을 생성"

    @override
    async def call(self, adapter: RuntimeVariantAdapter, laid: ACaller) -> RuntimeVariantNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateRuntimeVariantInput(name=self.named, description=self.described)
            )
        return payload.runtime_variant


@dataclass(frozen=True)
class CreatingWithTheLaidName(When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]):
    """미리 만들어 둔 변형과 같은 이름으로 생성한다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        return f"{laid.caller.username}이 이미 있는 이름 {laid.variant.name}(으)로 다시 생성"

    @override
    async def call(
        self, adapter: RuntimeVariantAdapter, laid: AVariantAndACaller
    ) -> RuntimeVariantNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(CreateRuntimeVariantInput(name=laid.variant.name))
        return payload.runtime_variant


@dataclass(frozen=True)
class TheSuperadminMakesOneWithANameAlone(
    Scenario[SeedingSession, ACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-variant-with-a-name-alone"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 이름만 지정해 변형을 생성하면, 설명은 비고 폴더 설정 파일은 읽지 않으며 "
            "모델 정의는 코드가 정해 둔 기본값인 노드가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, RuntimeVariantNode]:
        return TheNewVariantNode(started=self.started, named=MADE, described=None)


@dataclass(frozen=True)
class ADescriptionComesBackAsGiven(
    Scenario[SeedingSession, ACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-variant-made-with-a-description-carries-it-back"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이름과 설명을 함께 지정해 생성하면, 지정한 값이 그대로 담긴 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Creating(described=DESCRIBED)

    @override
    def then(self) -> Then[ACaller, RuntimeVariantNode]:
        return TheNewVariantNode(started=self.started, named=MADE, described=DESCRIBED)


@dataclass(frozen=True)
class ANameAlreadyTakenIsRefused(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    @override
    def summary(self) -> str:
        return "a-variant-name-already-taken-is-refused"

    @override
    def describe(self) -> str:
        return "같은 이름의 변형이 이미 있을 때 그 이름으로 다시 생성하면, 이름 중복으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return CreatingWithTheLaidName()

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheCallIsRefused(RuntimeVariantConflict)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotCreate(
    Scenario[SeedingSession, ACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-variant"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 변형을 생성하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, RuntimeVariantNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheSuperadmin(
    Scenario[SeedingSession, ACaller, RuntimeVariantAdapter, RuntimeVariantNode], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-does-not-let-a-user-create-a-variant"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 꺼도 슈퍼관리자가 아니면 변형을 생성하지 못한다. "
            "생성은 권한 그래프가 아니라 역할로 보호되므로 스위치와 무관하다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, RuntimeVariantNode]:
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
    scenario: CreatingStep, adapter: RuntimeVariantAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
