"""정의 실행하기 — 읽을 수 있어도 실행은 권한 그래프가 지킨다.

실행은 저장된 정의를 읽어 Prometheus에 질의한다. 대역이 답하는 샘플의 값이 대역이 받은
질의라, 창과 라벨이 어떻게 들어갔는지를 답에서 본다. 라벨 검사는 정의가 허용 목록을 둔
때만 돌고, 대역을 부르기 전에 돈다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID, uuid4

import pytest
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

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    ExecuteQueryDefinitionOptionsInput,
    MetricLabelEntry,
    QueryTimeRangeInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    QueryDefinitionResultInfo,
)
from ai.backend.common.exception import (
    FailedToGetMetric,
    PrometheusQueryPresetInvalidLabel,
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

ENFORCEMENT = "manager.rbac.enforcement_enabled"
SERVER_WINDOW_PATH = "metric.timewindow"
SERVER_WINDOW = "2m"
PRESET_WINDOW = "1h"
ASKED_WINDOW = "30s"

type Result = QueryDefinitionResultInfo
type ExecutingStep = Scenario[
    SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result
]


@dataclass(frozen=True)
class Executing(When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]):
    """심은 정의를 실행한다. 창, 구간, 라벨은 준 것만 싣는다."""

    filter_labels: tuple[tuple[str, str], ...] = ()
    group_labels: Sequence[str] = ()
    time_window: str | None = None
    over_a_range: bool = False
    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "execute_preset"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        target = "아무것도 갖지 않은 id" if self.other is not None else laid.preset.name
        how = [f"{key}={value} 라벨로" for key, value in self.filter_labels]
        how.extend(f"{one}로 묶어" for one in self.group_labels)
        if self.time_window is not None:
            how.append(f"창 {self.time_window}로")
        if self.over_a_range:
            how.append("구간을 주고")
        return f"{laid.caller.username}이 {target}을 {', '.join(how) or '아무것도 주지 않고'} 실행"

    @override
    async def call(self, adapter: PrometheusQueryPresetAdapter, laid: APresetAndACaller) -> Result:
        wanted = self.other if self.other is not None else laid.preset.id
        options = ExecuteQueryDefinitionOptionsInput(
            filter_labels=[
                MetricLabelEntry(key=key, value=value) for key, value in self.filter_labels
            ],
            group_labels=list(self.group_labels),
        )
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
            "창이 없는 정의를 슈퍼관리자가 창을 주고 구간 없이 실행하면, 순간 질의로 답하고 "
            "대역이 받은 질의에 요청의 창이 들어 있다"
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
        return "슈퍼관리자가 시작·끝·간격을 주고 실행하면, 대역이 범위 질의로 답한다"

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
class ThePresetWindowFillsInForTheRequest(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "a-request-naming-no-window-runs-with-the-window-of-the-preset"

    @override
    def describe(self) -> str:
        return (
            "창이 적힌 정의를 슈퍼관리자가 창 없이 실행하면, 대역이 받은 질의의 창이 정의의 창이다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN, time_window=PRESET_WINDOW)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing()

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheQueryAnswered(query="avg by () (rate(container_cpu_seconds_total{}[1h]))")


@dataclass(frozen=True)
class TheServerWindowFillsInForBoth(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result], Configured
):
    @override
    def summary(self) -> str:
        return "a-preset-and-a-request-naming-no-window-run-with-the-server-default"

    @override
    def describe(self) -> str:
        return (
            "창이 없는 정의를 슈퍼관리자가 창 없이 실행하면, "
            "대역이 받은 질의의 창이 서버 설정의 기본 창이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {SERVER_WINDOW_PATH: SERVER_WINDOW}

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing()

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheQueryAnswered(query="avg by () (rate(container_cpu_seconds_total{}[2m]))")


@dataclass(frozen=True)
class TheRequestWindowWinsOverThePreset(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "the-window-a-request-names-wins-over-the-window-of-the-preset"

    @override
    def describe(self) -> str:
        return (
            "창이 적힌 정의를 슈퍼관리자가 다른 창을 주고 실행하면, "
            "대역이 받은 질의의 창이 요청의 창이다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN, time_window=PRESET_WINDOW)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing(time_window=ASKED_WINDOW)

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheQueryAnswered(query="avg by () (rate(container_cpu_seconds_total{}[30s]))")


@dataclass(frozen=True)
class AnAllowedFilterLabelReachesTheQuery(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "a-filter-label-the-preset-allows-reaches-the-query-as-an-exact-match"

    @override
    def describe(self) -> str:
        return (
            "필터 라벨을 제한해 둔 정의를 슈퍼관리자가 그 목록 안의 라벨로 실행하면, "
            "대역이 받은 질의에 그 라벨이 정확히 일치하는 조건으로 들어 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(
            role=UserRole.SUPERADMIN, time_window=PRESET_WINDOW, filter_labels=("kernel_id",)
        )

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing(filter_labels=(("kernel_id", "k1"),))

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheQueryAnswered(
            query='avg by () (rate(container_cpu_seconds_total{kernel_id="k1"}[1h]))'
        )


@dataclass(frozen=True)
class AnAllowedGroupLabelReachesTheQuery(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "a-group-label-the-preset-allows-reaches-the-query"

    @override
    def describe(self) -> str:
        return (
            "묶음 라벨을 제한해 둔 정의를 슈퍼관리자가 그 목록 안의 라벨로 실행하면, "
            "대역이 받은 질의의 묶음에 그 라벨이 들어 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(
            role=UserRole.SUPERADMIN, time_window=PRESET_WINDOW, group_labels=("agent_id",)
        )

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing(group_labels=("agent_id",))

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheQueryAnswered(query="avg by (agent_id) (rate(container_cpu_seconds_total{}[1h]))")


@dataclass(frozen=True)
class AFilterLabelOutsideTheListIsRefused(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "a-filter-label-the-preset-does-not-allow-is-refused"

    @override
    def describe(self) -> str:
        return (
            "필터 라벨을 제한해 둔 정의를 슈퍼관리자가 그 목록에 없는 라벨로 실행하면, "
            "외부에 질의하기 전에 라벨로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN, filter_labels=("kernel_id",))

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing(filter_labels=(("session_id", "s1"),))

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheCallIsRefused(PrometheusQueryPresetInvalidLabel)


@dataclass(frozen=True)
class AGroupLabelOutsideTheListIsRefused(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "a-group-label-the-preset-does-not-allow-is-refused"

    @override
    def describe(self) -> str:
        return (
            "묶음 라벨을 제한해 둔 정의를 슈퍼관리자가 그 목록에 없는 라벨로 실행하면, "
            "같은 자리에서 라벨로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN, group_labels=("agent_id",))

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing(group_labels=("session_id",))

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheCallIsRefused(PrometheusQueryPresetInvalidLabel)


@dataclass(frozen=True)
class AnUnrestrictedPresetTakesAnyLabel(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "a-preset-restricting-no-label-runs-with-any-label"

    @override
    def describe(self) -> str:
        return (
            "허용 라벨 목록이 빈 정의를 슈퍼관리자가 아무 라벨이나 주고 실행하면, "
            "대역이 받은 질의에 그 라벨이 들어 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN, time_window=PRESET_WINDOW)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing(filter_labels=(("session_id", "s1"),), group_labels=("agent_id",))

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheQueryAnswered(
            query='avg by (agent_id) (rate(container_cpu_seconds_total{session_id="s1"}[1h]))'
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
            "라벨 없이는 빈 질의로 렌더되는 정의를 슈퍼관리자가 라벨 없이 실행하면, "
            "Prometheus가 그 질의를 거부하고 그 거부가 지표를 얻지 못했다는 이유로 그대로 올라온다"
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
        return "a-user-who-may-read-a-preset-may-not-run-it"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자는 정의를 읽을 수 있지만 실행하면 권한 부족으로 "
            "거부된다. 이 엔티티는 어느 스코프에도 없어 역할로는 권한을 받을 길이 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

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
        return (
            "엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 정의를 실행한다. "
            "이 문은 역할이 아니라 권한 그래프가 지키기 때문이다"
        )

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
            "아무 권한도 받지 않은 사용자가 아무것도 갖지 않은 id로 실행하면, 대상이 없다는 "
            "것이 아니라 권한 부족으로 거부된다. 없는 행에는 걸린 권한도 없기 때문이다"
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
            "슈퍼관리자가 아무것도 갖지 않은 id로 실행하면, 대상이 없다는 것으로 거부된다. "
            "실행은 서비스가 정의를 직접 읽어 내므로 고치기와 지우기의 대상 없음과 종류가 다르다"
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
    ThePresetWindowFillsInForTheRequest(),
    TheServerWindowFillsInForBoth(),
    TheRequestWindowWinsOverThePreset(),
    AnAllowedFilterLabelReachesTheQuery(),
    AnAllowedGroupLabelReachesTheQuery(),
    AFilterLabelOutsideTheListIsRefused(),
    AGroupLabelOutsideTheListIsRefused(),
    AnUnrestrictedPresetTakesAnyLabel(),
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
