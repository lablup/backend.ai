"""카테고리 생성 — 누가 생성할 수 있고, 무엇이 이름을 막는가.

이름 중복은 저장소의 유일 제약이 거부하고 도메인 오류로 옮겨져 있지 않다. 정의의 이름에는
제약이 없으므로 두 엔티티가 반대다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset_category import (
    ACallerAlone,
    ACategoryAndACaller,
    ACategoryAndSomeone,
    CategoryNodeAnswer,
    JustSomeone,
    TheNewCategoryNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    CreateCategoryInput,
)
from ai.backend.manager.api.adapters.prometheus_query_preset_category.adapter import (
    PrometheusQueryPresetCategoryAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)

MADE = "cpu"
FRESH = "새로 만든 카테고리"
ENFORCEMENT = "manager.rbac.enforcement_enabled"

type Adapter = PrometheusQueryPresetCategoryAdapter
type CreatingStep = Scenario[SeedingSession, ACallerAlone, Adapter, CategoryNodeAnswer]
type RepeatingStep = Scenario[SeedingSession, ACategoryAndACaller, Adapter, CategoryNodeAnswer]


@dataclass(frozen=True)
class Creating(When[ACallerAlone, Adapter, CategoryNodeAnswer]):
    """카테고리 하나를 생성한다."""

    named: str = MADE
    described: str | None = None

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ACallerAlone) -> str:
        return f"{laid.caller.username}이 이름 {self.named}(으)로 생성"

    @override
    async def call(self, adapter: Adapter, laid: ACallerAlone) -> CategoryNodeAnswer:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateCategoryInput(name=self.named, description=self.described)
            )
        return payload.item


@dataclass(frozen=True)
class CreatingUnderTheSameName(When[ACategoryAndACaller, Adapter, CategoryNodeAnswer]):
    """미리 만들어 둔 카테고리와 같은 이름으로 하나 더 생성한다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ACategoryAndACaller) -> str:
        return f"{laid.caller.username}이 이미 있는 이름 {laid.category.name}(으)로 다시 생성"

    @override
    async def call(self, adapter: Adapter, laid: ACategoryAndACaller) -> CategoryNodeAnswer:
        with ActingAs(laid.caller):
            payload = await adapter.create(CreateCategoryInput(name=laid.category.name))
        return payload.item


@dataclass(frozen=True)
class TheNameAloneMakesAWholeNode(
    Scenario[SeedingSession, ACallerAlone, Adapter, CategoryNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "creating-a-category-with-a-name-alone-answers-with-the-whole-node"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 이름만 지정해 카테고리를 생성하면, 설명이 비어 있는 노드 전체가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACallerAlone]:
        return JustSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACallerAlone, Adapter, CategoryNodeAnswer]:
        return Creating()

    @override
    def then(self) -> Then[ACallerAlone, CategoryNodeAnswer]:
        return TheNewCategoryNode(started=self.started, named=MADE, described=None)


@dataclass(frozen=True)
class TheDescriptionComesBackAsGiven(
    Scenario[SeedingSession, ACallerAlone, Adapter, CategoryNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "creating-a-category-with-a-description-carries-it-on-the-node"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이름과 설명을 함께 지정해 생성하면, 지정한 값이 그대로 담긴 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACallerAlone]:
        return JustSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACallerAlone, Adapter, CategoryNodeAnswer]:
        return Creating(described=FRESH)

    @override
    def then(self) -> Then[ACallerAlone, CategoryNodeAnswer]:
        return TheNewCategoryNode(started=self.started, named=MADE, described=FRESH)


@dataclass(frozen=True)
class ANameAnotherCategoryHoldsIsRefused(
    Scenario[SeedingSession, ACategoryAndACaller, Adapter, CategoryNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "a-name-another-category-already-holds-is-refused"

    @override
    def describe(self) -> str:
        return (
            "이미 다른 카테고리가 사용 중인 이름으로 슈퍼관리자가 다시 생성하면, 이름 중복으로 "
            "거부된다. 저장소의 유일 제약이 막는 것이고 도메인 오류로 옮겨져 있지 않다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACategoryAndACaller]:
        return ACategoryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACategoryAndACaller, Adapter, CategoryNodeAnswer]:
        return CreatingUnderTheSameName()

    @override
    def then(self) -> Then[ACategoryAndACaller, CategoryNodeAnswer]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class APlainUserMayNotCreate(Scenario[SeedingSession, ACallerAlone, Adapter, CategoryNodeAnswer]):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-category"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 카테고리를 생성하려 하면, 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACallerAlone]:
        return JustSomeone()

    @override
    def when(self) -> When[ACallerAlone, Adapter, CategoryNodeAnswer]:
        return Creating()

    @override
    def then(self) -> Then[ACallerAlone, CategoryNodeAnswer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffChangesNothing(
    Scenario[SeedingSession, ACallerAlone, Adapter, CategoryNodeAnswer], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-does-not-let-a-user-create-a-category"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 꺼도 카테고리 생성은 여전히 거부된다. "
            "생성은 권한 그래프가 아니라 역할로 보호되기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ACallerAlone]:
        return JustSomeone()

    @override
    def when(self) -> When[ACallerAlone, Adapter, CategoryNodeAnswer]:
        return Creating()

    @override
    def then(self) -> Then[ACallerAlone, CategoryNodeAnswer]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheNameAloneMakesAWholeNode(started=datetime.now(UTC)),
    TheDescriptionComesBackAsGiven(started=datetime.now(UTC)),
    APlainUserMayNotCreate(),
    EnforcementOffChangesNothing(),
]

REPEATING_SCENARIOS: list[RepeatingStep] = [ANameAnotherCategoryHoldsIsRefused()]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", REPEATING_SCENARIOS, ids=lambda s: s.summary())
async def test_creating_beside_another(
    scenario: RepeatingStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
