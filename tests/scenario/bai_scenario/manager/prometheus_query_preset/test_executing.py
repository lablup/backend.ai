"""프리셋 실행 — 조회할 수 있어도 실행은 권한 그래프로 보호된다.

실행은 저장된 프리셋을 읽어 Prometheus에 질의한다. 모의 서버가 응답하는 샘플의 값이 모의
서버가 받은 질의라, 시간 창이 어떻게 들어갔는지를 응답에서 확인한다. 시간 창의 우선순위와
라벨 허용 목록은 서비스의 단위 테스트가 검사하므로 여기에는 없다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    ExecuteQueryDefinitionOptionsInput,
    QueryTimeRangeInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    QueryDefinitionResultInfo,
)
from ai.backend.common.exception import (
    FailedToGetMetric,
    PrometheusQueryPresetNotFound,
)
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    TheQueryAnswered,
)
from bai_scenario.fakes.prometheus import RANGE
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.prometheus_query_preset.preset import EMPTY_WITHOUT_LABELS

ENFORCEMENT = "manager.rbac.enforcement_enabled"
PRESET_WINDOW = "1h"
ASKED_WINDOW = "30s"

type Result = QueryDefinitionResultInfo
type ExecutingStep = Scenario[
    SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result
]


@dataclass(frozen=True)
class Executing(When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]):
    """미리 만들어 둔 프리셋을 실행한다. 시간 창과 조회 구간은 지정한 것만 담는다."""

    time_window: str | None = None
    over_a_range: bool = False
    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "execute_preset"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        target = "존재하지 않는 id" if self.other is not None else laid.preset.name
        how: list[str] = []
        if self.time_window is not None:
            how.append(f"시간 창 {self.time_window}")
        if self.over_a_range:
            how.append("조회 구간 지정")
        return (
            f"{laid.caller.username}이 {target} 실행 ({', '.join(how) or '아무것도 지정하지 않음'})"
        )

    @override
    async def call(self, adapter: PrometheusQueryPresetAdapter, laid: APresetAndACaller) -> Result:
        wanted = self.other if self.other is not None else laid.preset.id
        options = ExecuteQueryDefinitionOptionsInput(filter_labels=[], group_labels=[])
        time_range = (
            QueryTimeRangeInputDTO(
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 1, 2, tzinfo=UTC),
                step="60s",
            )
            if self.over_a_range
            else None
        )
        with ActingAs(laid.caller):
            return await adapter.execute_preset(
                wanted, options, time_window=self.time_window, time_range=time_range
            )


@dataclass(frozen=True)
class TheSuperadminRunsItWithoutARange(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "running-a-preset-without-a-range-is-an-instant-query-carrying-the-asked-window"

    @override
    def describe(self) -> str:
        return (
            "시간 창이 없는 프리셋을 슈퍼관리자가 시간 창을 지정하고 조회 구간 없이 실행하면, 순간 질의로 "
            "응답하고 모의 서버가 받은 질의에 요청의 시간 창이 들어 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing(time_window=ASKED_WINDOW)

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheQueryAnswered(query="avg by () (rate(container_cpu_seconds_total{}[30s]))")


@dataclass(frozen=True)
class RunningOverARangeIsARangeQuery(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "running-a-preset-over-a-range-is-a-range-query"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 시작·끝·간격을 지정해 실행하면, 모의 서버가 범위 질의로 응답한다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN, time_window=PRESET_WINDOW)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing(over_a_range=True)

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheQueryAnswered(
            query="avg by () (rate(container_cpu_seconds_total{}[1h]))", result_type=RANGE
        )


@dataclass(frozen=True)
class PrometheusRefusingTheQueryIsPassedOn(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "a-query-prometheus-refuses-is-refused-as-a-failed-metric-read"

    @override
    def describe(self) -> str:
        return (
            "라벨 없이는 빈 질의로 렌더되는 프리셋을 슈퍼관리자가 라벨 없이 실행하면, "
            "Prometheus가 그 질의를 거부하고 그 거부가 지표를 얻지 못했다는 이유로 그대로 전파된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN, query_template=EMPTY_WITHOUT_LABELS)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing()

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheCallIsRefused(FailedToGetMetric)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRun(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-run-a-preset"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 프리셋을 실행하면 권한 부족으로 거부된다. 실행은 조회와 "
            "같은 권한을 묻는다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(reading_in_public=False)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing()

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneRun(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-run-a-preset"

    @override
    def describe(self) -> str:
        return "권한 검사를 끄면 아무 권한도 없는 사용자도 프리셋을 실행할 수 있다"

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(time_window=PRESET_WINDOW)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing()

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheQueryAnswered(query="avg by () (rate(container_cpu_seconds_total{}[1h]))")


@dataclass(frozen=True)
class AnUnknownIdIsRefusedAsPermission(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "running-an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 존재하지 않는 id로 실행하면, 대상 없음이 아니라 "
            "권한 부족으로 거부된다. 없는 행에는 부여된 권한도 없기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing(other=uuid4())

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "running-an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 존재하지 않는 id로 실행하면, 대상을 찾을 수 없다는 이유로 거부된다. "
            "실행은 서비스가 프리셋을 직접 읽어서 내는 오류라 수정과 삭제의 대상 없음과 종류가 다르다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing(other=uuid4())

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheCallIsRefused(PrometheusQueryPresetNotFound)


SCENARIOS: list[ExecutingStep] = [
    TheSuperadminRunsItWithoutARange(),
    RunningOverARangeIsARangeQuery(),
    PrometheusRefusingTheQueryIsPassedOn(),
    AUserGrantedNothingMayNotRun(),
    EnforcementOffLetsAnyoneRun(),
    AnUnknownIdIsRefusedAsPermission(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_executing(
    scenario: ExecutingStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
