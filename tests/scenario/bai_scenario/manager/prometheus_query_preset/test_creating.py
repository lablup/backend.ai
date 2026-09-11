"""프리셋 생성 — 누가 생성할 수 있고, 무엇이 템플릿과 카테고리를 막는가.

생성은 전역 역할이 있어야 하고 렌더러가 템플릿을 검사한 뒤에야 행을 쓴다. 이름은 유일하지 않고,
존재하지 않는 카테고리는 저장소의 참조 제약이 거부한다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset import (
    ACatalogAndACaller,
    ACategoryAndSomeone,
    APresetAndACaller,
    APresetAndSomeone,
    JustSomeone,
    PresetNodeAnswer,
    TheNewPresetNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.prometheus_query_preset.preset import METRIC, TEMPLATE, UNRENDERABLE

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    CreateQueryDefinitionInput,
    CreateQueryDefinitionOptionsInput,
)
from ai.backend.common.exception import InvalidMetricPresetTemplate
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)

MADE = "cpu-by-kernel"
WINDOW = "5m"
ENFORCEMENT = "manager.rbac.enforcement_enabled"

type CreatingStep = Scenario[
    SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer
]
type RepeatingStep = Scenario[
    SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer
]


def _create_input(
    name: str,
    query_template: str,
    time_window: str | None,
    category_id: UUID | None,
) -> CreateQueryDefinitionInput:
    return CreateQueryDefinitionInput(
        name=name,
        metric_name=METRIC,
        query_template=query_template,
        time_window=time_window,
        category_id=category_id,
        options=CreateQueryDefinitionOptionsInput(filter_labels=[], group_labels=[]),
    )


@dataclass(frozen=True)
class Creating(When[ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]):
    """프리셋 하나를 생성한다. 카테고리는 미리 만들어 둔 것을 가리키거나, 존재하지 않는 id를 지정하거나, 없다."""

    named: str = MADE
    query_template: str = TEMPLATE
    time_window: str | None = None
    under_the_category: bool = False
    under_an_unknown_category: bool = False

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ACatalogAndACaller) -> str:
        where = ""
        if self.under_the_category:
            where = " 미리 만들어 둔 카테고리 아래에"
        elif self.under_an_unknown_category:
            where = " 존재하지 않는 카테고리 id 아래에"
        return f"{laid.caller.username}이{where} 이름 {self.named}(으)로 생성"

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: ACatalogAndACaller
    ) -> PresetNodeAnswer:
        category_id: UUID | None = None
        if self.under_the_category and laid.category is not None:
            category_id = laid.category.id
        elif self.under_an_unknown_category:
            category_id = uuid4()
        with ActingAs(laid.caller):
            payload = await adapter.create(
                _create_input(self.named, self.query_template, self.time_window, category_id)
            )
        return payload.item


@dataclass(frozen=True)
class CreatingUnderTheSameName(
    When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    """미리 만들어 둔 프리셋과 같은 이름으로 하나 더 생성한다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return f"{laid.caller.username}이 이미 있는 이름 {laid.preset.name}(으)로 다시 생성"

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: APresetAndACaller
    ) -> PresetNodeAnswer:
        with ActingAs(laid.caller):
            payload = await adapter.create(_create_input(laid.preset.name, TEMPLATE, None, None))
        return payload.item


@dataclass(frozen=True)
class TheRequiredValuesMakeAWholeNode(
    Scenario[SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "creating-a-preset-with-the-required-values-answers-with-the-whole-node"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 이름, 지표 이름, 템플릿, 허용 라벨 목록만 지정해 생성하면, "
            "순위는 0이고 카테고리·설명·시간 창은 비어 있는 노드 전체가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACatalogAndACaller]:
        return JustSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Creating()

    @override
    def then(self) -> Then[ACatalogAndACaller, PresetNodeAnswer]:
        return TheNewPresetNode(started=self.started, named=MADE)


@dataclass(frozen=True)
class FiledUnderACategory(
    Scenario[SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "creating-a-preset-under-a-category-points-the-node-at-that-category"

    @override
    def describe(self) -> str:
        return "카테고리 하나가 있고 슈퍼관리자가 그 카테고리를 지정해 생성하면, 응답의 카테고리가 그것을 가리킨다"

    @override
    def given(self) -> Given[SeedingSession, ACatalogAndACaller]:
        return ACategoryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Creating(under_the_category=True)

    @override
    def then(self) -> Then[ACatalogAndACaller, PresetNodeAnswer]:
        return TheNewPresetNode(started=self.started, named=MADE, under_the_category=True)


@dataclass(frozen=True)
class WithAWindow(
    Scenario[SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "creating-a-preset-with-a-window-carries-that-window-on-the-node"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 시간 창을 함께 지정해 생성하면, 노드에 그 시간 창이 담긴다"

    @override
    def given(self) -> Given[SeedingSession, ACatalogAndACaller]:
        return JustSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Creating(time_window=WINDOW)

    @override
    def then(self) -> Then[ACatalogAndACaller, PresetNodeAnswer]:
        return TheNewPresetNode(started=self.started, named=MADE, time_window=WINDOW)


@dataclass(frozen=True)
class AnUnrenderableTemplateIsRefused(
    Scenario[SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "a-template-the-renderer-refuses-cannot-be-stored"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 렌더러가 받지 않는 템플릿으로 생성하면, 템플릿 오류로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACatalogAndACaller]:
        return JustSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Creating(query_template=UNRENDERABLE)

    @override
    def then(self) -> Then[ACatalogAndACaller, PresetNodeAnswer]:
        return TheCallIsRefused(InvalidMetricPresetTemplate)


@dataclass(frozen=True)
class AnUnknownCategoryIsRefused(
    Scenario[SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "a-category-id-nothing-answers-to-is-refused"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 존재하지 않는 카테고리 id를 지정해 생성하면, 카테고리가 없다는 이유로 "
            "거부된다. 저장소의 참조 제약이 막는 것이고 도메인 오류로 옮겨져 있지 않다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACatalogAndACaller]:
        return JustSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Creating(under_an_unknown_category=True)

    @override
    def then(self) -> Then[ACatalogAndACaller, PresetNodeAnswer]:
        return TheCallIsRefused(ForeignKeyViolationError)


@dataclass(frozen=True)
class TheSameNameIsAllowedTwice(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-name-another-preset-already-holds-is-allowed"

    @override
    def describe(self) -> str:
        return (
            "이미 다른 프리셋이 사용 중인 이름으로 슈퍼관리자가 다시 생성하면, 생성된다. "
            "프리셋의 이름에는 유일 제약이 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return CreatingUnderTheSameName()

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return TheNewPresetNode(started=self.started, named=None)


@dataclass(frozen=True)
class APlainUserMayNotCreate(
    Scenario[SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-preset"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 프리셋을 생성하려 하면, 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACatalogAndACaller]:
        return JustSomeone()

    @override
    def when(self) -> When[ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Creating()

    @override
    def then(self) -> Then[ACatalogAndACaller, PresetNodeAnswer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AMonitorMayNotCreate(
    Scenario[SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "the-monitor-role-may-not-create-a-preset"

    @override
    def describe(self) -> str:
        return (
            "모니터 역할이 프리셋을 생성하려 하면, 역할 부족으로 거부된다. "
            "전역 역할 검사는 읽기에만 그 역할을 허용한다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACatalogAndACaller]:
        return JustSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Creating()

    @override
    def then(self) -> Then[ACatalogAndACaller, PresetNodeAnswer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffChangesNothing(
    Scenario[SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-does-not-let-a-user-create-a-preset"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 꺼도 프리셋 생성은 여전히 거부된다. "
            "생성은 권한 그래프가 아니라 역할로 보호되기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ACatalogAndACaller]:
        return JustSomeone()

    @override
    def when(self) -> When[ACatalogAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return Creating()

    @override
    def then(self) -> Then[ACatalogAndACaller, PresetNodeAnswer]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheRequiredValuesMakeAWholeNode(started=datetime.now(UTC)),
    FiledUnderACategory(started=datetime.now(UTC)),
    WithAWindow(started=datetime.now(UTC)),
    AnUnrenderableTemplateIsRefused(),
    AnUnknownCategoryIsRefused(),
    APlainUserMayNotCreate(),
    AMonitorMayNotCreate(),
    EnforcementOffChangesNothing(),
]

REPEATING_SCENARIOS: list[RepeatingStep] = [TheSameNameIsAllowedTwice(started=datetime.now(UTC))]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", REPEATING_SCENARIOS, ids=lambda s: s.summary())
async def test_creating_beside_another(
    scenario: RepeatingStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
