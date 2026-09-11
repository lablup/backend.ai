"""템플릿 미리 보기 — 저장하지 않고 Prometheus에 물어본다.

이 어댑터에서 유일하게 전역 역할이 지키는 읽기라, 모니터 역할이 지나가는 줄이 여기에만
있다. 대역이 받은 질의를 읽는 줄은 `then`이 대역을 받게 되면 더한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset import (
    ACatalogAndACaller,
    JustSomeone,
    TheOneSampleAnswered,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.prometheus_query_preset.preset import TEMPLATE, UNRENDERABLE

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    PreviewQueryDefinitionInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    QueryDefinitionResultInfo,
)
from ai.backend.common.exception import InvalidMetricPresetTemplate
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type Result = QueryDefinitionResultInfo
type PreviewingStep = Scenario[
    SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, Result
]


@dataclass(frozen=True)
class Previewing(When[ACatalogAndACaller, PrometheusQueryPresetAdapter, Result]):
    """템플릿 문자열만 주고 미리 본다."""

    query_template: str = TEMPLATE

    @override
    def operation(self) -> str:
        return "admin_preview"

    @override
    def describe(self, laid: ACatalogAndACaller) -> str:
        what = "렌더러가 받지 않는 템플릿" if self.query_template == UNRENDERABLE else "템플릿"
        return f"{laid.caller.username}이 {what}을 미리 봄"

    @override
    async def call(self, adapter: PrometheusQueryPresetAdapter, laid: ACatalogAndACaller) -> Result:
        with ActingAs(laid.caller):
            return await adapter.admin_preview(
                PreviewQueryDefinitionInput(query_template=self.query_template)
            )


@dataclass(frozen=True)
class TheSuperadminPreviewsATemplate(
    Scenario[SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-previews-a-template-and-gets-what-prometheus-answered"

    @override
    def describe(self) -> str:
        return (
            "대역이 결과를 답하도록 세워 둔 채 슈퍼관리자가 템플릿만 주고 미리 보면, "
            "대역이 답한 결과가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACatalogAndACaller]:
        return JustSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACatalogAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Previewing()

    @override
    def then(self) -> Then[ACatalogAndACaller, Result]:
        return TheOneSampleAnswered()


@dataclass(frozen=True)
class AnUnrenderableTemplateIsRefused(
    Scenario[SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "a-template-the-renderer-refuses-cannot-be-previewed"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 렌더러가 받지 않는 템플릿을 미리 보면, 외부에 묻기 전에 템플릿으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACatalogAndACaller]:
        return JustSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACatalogAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Previewing(query_template=UNRENDERABLE)

    @override
    def then(self) -> Then[ACatalogAndACaller, Result]:
        return TheCallIsRefused(InvalidMetricPresetTemplate)


@dataclass(frozen=True)
class AMonitorPreviewsToo(
    Scenario[SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "the-monitor-role-previews-a-template"

    @override
    def describe(self) -> str:
        return "모니터 역할이 템플릿을 미리 보면, 대역이 답한 결과가 온다. 전역 문은 읽기에 한해 그 역할을 지나게 한다"

    @override
    def given(self) -> Given[SeedingSession, ACatalogAndACaller]:
        return JustSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ACatalogAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Previewing()

    @override
    def then(self) -> Then[ACatalogAndACaller, Result]:
        return TheOneSampleAnswered()


@dataclass(frozen=True)
class APlainUserMayNotPreview(
    Scenario[SeedingSession, ACatalogAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-preview-a-template"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 미리 보려 하면, 역할로 막힌다"

    @override
    def given(self) -> Given[SeedingSession, ACatalogAndACaller]:
        return JustSomeone()

    @override
    def when(self) -> When[ACatalogAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Previewing()

    @override
    def then(self) -> Then[ACatalogAndACaller, Result]:
        return TheCallIsRefused(InsufficientPrivilege)


@pytest.mark.parametrize(
    "scenario",
    [
        TheSuperadminPreviewsATemplate(),
        AnUnrenderableTemplateIsRefused(),
        AMonitorPreviewsToo(),
        APlainUserMayNotPreview(),
    ],
    ids=lambda s: s.summary(),
)
async def test_previewing(
    scenario: PreviewingStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
