"""정의 실행하기 — 읽을 수 있어도 실행은 권한 그래프가 지킨다.

실행은 저장된 정의를 읽어 Prometheus에 질의한다. 라벨 검사는 정의가 허용 목록을 둔 때만
돌고, 대역을 부르기 전에 돈다. 대역이 받은 질의를 읽는 줄은 `then`이 대역을 받게 되면 더한다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    TheOneSampleAnswered,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    ExecuteQueryDefinitionOptionsInput,
    MetricLabelEntry,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    QueryDefinitionResultInfo,
)
from ai.backend.common.exception import (
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

type Result = QueryDefinitionResultInfo
type ExecutingStep = Scenario[
    SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result
]


@dataclass(frozen=True)
class Executing(When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]):
    """심은 정의를 창도 구간도 없이 실행한다. 라벨은 준 것만 싣는다."""

    filter_labels: tuple[tuple[str, str], ...] = ()
    group_labels: Sequence[str] = ()
    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "execute_preset"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        target = "아무것도 갖지 않은 id" if self.other is not None else laid.preset.name
        labels = [f"{key}={value}" for key, value in self.filter_labels]
        labels.extend(f"묶음 {one}" for one in self.group_labels)
        how = f" {', '.join(labels)} 라벨로" if labels else " 라벨 없이"
        return f"{laid.caller.username}이 {target}을{how} 실행"

    @override
    async def call(self, adapter: PrometheusQueryPresetAdapter, laid: APresetAndACaller) -> Result:
        wanted = self.other if self.other is not None else laid.preset.id
        options = ExecuteQueryDefinitionOptionsInput(
            filter_labels=[
                MetricLabelEntry(key=key, value=value) for key, value in self.filter_labels
            ],
            group_labels=list(self.group_labels),
        )
        with ActingAs(laid.caller):
            return await adapter.execute_preset(wanted, options, time_window=None, time_range=None)


@dataclass(frozen=True)
class TheSuperadminRunsIt(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-runs-a-preset-and-gets-what-prometheus-answered"

    @override
    def describe(self) -> str:
        return (
            "정의 하나가 있고 대역이 결과 하나를 답하도록 세워 둔 채 슈퍼관리자가 실행하면, "
            "대역이 준 상태와 결과 종류와 값이 그대로 실려 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing()

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheOneSampleAnswered()


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
        return Executing(filter_labels=(("session_id", "abc"),))

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
class AUserGrantedNothingMayNotRun(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Result]
):
    @override
    def summary(self) -> str:
        return "a-user-who-may-read-a-preset-may-not-run-it"

    @override
    def describe(self) -> str:
        return (
            "정의를 읽을 수는 있는 아무 권한도 받지 않은 사용자가 실행하면, 권한 부족으로 "
            "거부된다. 이 엔티티는 어느 스코프에도 없어 권한을 받을 길이 없다"
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
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Result]:
        return Executing()

    @override
    def then(self) -> Then[APresetAndACaller, Result]:
        return TheOneSampleAnswered()


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


@pytest.mark.parametrize(
    "scenario",
    [
        TheSuperadminRunsIt(),
        AFilterLabelOutsideTheListIsRefused(),
        AGroupLabelOutsideTheListIsRefused(),
        AUserGrantedNothingMayNotRun(),
        EnforcementOffLetsAnyoneRun(),
        AnUnknownIdIsRefusedAsPermission(),
        AnUnknownIdIsNotFoundForASuperadmin(),
    ],
    ids=lambda s: s.summary(),
)
async def test_executing(
    scenario: ExecutingStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
