"""HuggingFace 레지스트리 하나 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    UpdateHuggingFaceRegistryInput,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    HuggingFaceRegistryNode,
)
from ai.backend.manager.api.adapters.huggingface_registry.adapter import (
    HuggingFaceRegistryAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.huggingface_registry import (
    EDITED_URL,
    ARegistryAndACaller,
    ARegistryAndSomeone,
    TheRegistryIsEdited,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Edited = HuggingFaceRegistryNode
type EditingStep = Scenario[
    TestSeedingSession, ARegistryAndACaller, HuggingFaceRegistryAdapter, Edited
]


@dataclass(frozen=True)
class Editing(When[ARegistryAndACaller, HuggingFaceRegistryAdapter, Edited]):
    """미리 만들어 둔 레지스트리의 주소를 바꾼다. 답에서 노드를 벗겨 준다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.registry.name}의 주소를 바꿈"

    @override
    async def call(self, adapter: HuggingFaceRegistryAdapter, laid: ARegistryAndACaller) -> Edited:
        with ActingAs(laid.caller):
            payload = await adapter.update(
                UpdateHuggingFaceRegistryInput(id=laid.registry.id, url=EDITED_URL)
            )
        return payload.huggingface_registry


@dataclass(frozen=True)
class AUserGrantedUpdateEdits(
    Scenario[TestSeedingSession, ARegistryAndACaller, HuggingFaceRegistryAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-edits-a-registry"

    @override
    def describe(self) -> str:
        return "레지스트리 수정 권한을 받은 사용자가 주소를 바꾸면, 그 레지스트리가 새 주소로 온다"

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(granted=(Permission.UPDATE,))

    @override
    def when(self) -> When[ARegistryAndACaller, HuggingFaceRegistryAdapter, Edited]:
        return Editing()

    @override
    def then(self) -> Then[ARegistryAndACaller, Edited]:
        return TheRegistryIsEdited()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[TestSeedingSession, ARegistryAndACaller, HuggingFaceRegistryAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-registry"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 주소를 바꾸려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone()

    @override
    def when(self) -> When[ARegistryAndACaller, HuggingFaceRegistryAdapter, Edited]:
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
    scenario: EditingStep, adapter: HuggingFaceRegistryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
