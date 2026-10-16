"""Reservoir 레지스트리 하나 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    UpdateReservoirRegistryInput,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    ReservoirRegistryNode,
)
from ai.backend.manager.api.adapters.reservoir_registry.adapter import (
    ReservoirRegistryAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.reservoir_registry import (
    EDITED_ENDPOINT,
    ARegistryAndACaller,
    ARegistryAndSomeone,
    TheRegistryIsEdited,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Edited = ReservoirRegistryNode
type EditingStep = Scenario[
    TestSeedingSession, ARegistryAndACaller, ReservoirRegistryAdapter, Edited
]


@dataclass(frozen=True)
class Editing(When[ARegistryAndACaller, ReservoirRegistryAdapter, Edited]):
    """미리 만들어 둔 레지스트리의 엔드포인트를 바꾼다. 답에서 노드를 벗겨 준다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.registry.name}의 엔드포인트를 바꿈"

    @override
    async def call(self, adapter: ReservoirRegistryAdapter, laid: ARegistryAndACaller) -> Edited:
        with ActingAs(laid.caller):
            payload = await adapter.update(
                UpdateReservoirRegistryInput(id=laid.registry.id, endpoint=EDITED_ENDPOINT)
            )
        return payload.reservoir


@dataclass(frozen=True)
class AUserGrantedUpdateEdits(
    Scenario[TestSeedingSession, ARegistryAndACaller, ReservoirRegistryAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-edits-a-registry"

    @override
    def describe(self) -> str:
        return "레지스트리 수정 권한을 받은 사용자가 엔드포인트를 바꾸면, 그 레지스트리가 새 엔드포인트로 온다"

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(granted=(Permission.UPDATE,))

    @override
    def when(self) -> When[ARegistryAndACaller, ReservoirRegistryAdapter, Edited]:
        return Editing()

    @override
    def then(self) -> Then[ARegistryAndACaller, Edited]:
        return TheRegistryIsEdited()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[TestSeedingSession, ARegistryAndACaller, ReservoirRegistryAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-registry"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 엔드포인트를 바꾸려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone()

    @override
    def when(self) -> When[ARegistryAndACaller, ReservoirRegistryAdapter, Edited]:
        return Editing()

    @override
    def then(self) -> Then[ARegistryAndACaller, Edited]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[EditingStep] = [
    AUserGrantedUpdateEdits(),
    AUserGrantedNothingMayNotEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: ReservoirRegistryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
