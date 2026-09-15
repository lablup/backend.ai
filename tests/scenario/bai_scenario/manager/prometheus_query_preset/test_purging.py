"""프리셋 삭제 — 누가 삭제할 수 있는가.

이 어댑터에는 soft delete가 없다. 삭제하면 행이 사라지고 되살리는 호출도 없다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    TheRemovedOneIsNamed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    DeleteQueryDefinitionInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    DeleteQueryDefinitionPayload,
)
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
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

type Removed = DeleteQueryDefinitionPayload
type PurgingStep = Scenario[
    SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Removed
]


@dataclass(frozen=True)
class Removing(When[APresetAndACaller, PrometheusQueryPresetAdapter, Removed]):
    """프리셋 하나를 삭제한다. id를 지정하지 않으면 미리 만들어 둔 프리셋을 삭제한다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        called = "존재하지 않는 id" if self.other is not None else laid.preset.name
        return f"{laid.caller.username}이 {called} 삭제"

    @override
    async def call(self, adapter: PrometheusQueryPresetAdapter, laid: APresetAndACaller) -> Removed:
        wanted = self.other if self.other is not None else laid.preset.id
        with ActingAs(laid.caller):
            return await adapter.delete(DeleteQueryDefinitionInput(id=wanted))


@dataclass(frozen=True)
class TheSuperadminRemovesIt(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Removed]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-removes-a-preset"

    @override
    def describe(self) -> str:
        return "프리셋 하나가 있고 슈퍼관리자가 삭제하면, 삭제한 id를 담은 응답이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Removed]:
        return Removing()

    @override
    def then(self) -> Then[APresetAndACaller, Removed]:
        return TheRemovedOneIsNamed()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRemove(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Removed]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-remove-a-preset"

    @override
    def describe(self) -> str:
        return "같은 프리셋이 있고 아무 권한도 없는 사용자가 삭제하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Removed]:
        return Removing()

    @override
    def then(self) -> Then[APresetAndACaller, Removed]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneRemove(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Removed],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-remove-a-preset"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 끄면 아무 권한도 없는 사용자도 프리셋을 삭제할 수 있다. "
            "삭제는 역할이 아니라 권한 그래프로 보호되기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Removed]:
        return Removing()

    @override
    def then(self) -> Then[APresetAndACaller, Removed]:
        return TheRemovedOneIsNamed()


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, Removed]
):
    @override
    def summary(self) -> str:
        return "removing-an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 삭제하면, 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, Removed]:
        return Removing(other=uuid4())

    @override
    def then(self) -> Then[APresetAndACaller, Removed]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[PurgingStep] = [
    TheSuperadminRemovesIt(),
    AUserGrantedNothingMayNotRemove(),
    EnforcementOffLetsAnyoneRemove(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
