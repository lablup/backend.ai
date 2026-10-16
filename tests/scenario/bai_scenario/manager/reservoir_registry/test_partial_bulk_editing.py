"""Reservoir 레지스트리 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    PartialBulkUpdateReservoirRegistriesInput,
    PartialBulkUpdateReservoirRegistryItemInput,
    UpdateReservoirRegistryBody,
)
from ai.backend.manager.api.adapters.reservoir_registry.adapter import (
    ReservoirRegistryAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.reservoir_registry import (
    EDITED_ENDPOINT,
    Edited,
    EveryTargetIsEdited,
    ManyRegistriesAndACaller,
    ManyRegistriesAndSomeone,
    NothingIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type EditingStep = Scenario[
    TestSeedingSession, ManyRegistriesAndACaller, ReservoirRegistryAdapter, Edited
]


@dataclass(frozen=True)
class EditingEveryTarget(When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, Edited]):
    """대상 레지스트리들의 엔드포인트를 한 번에 바꾼다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        return f"{laid.caller.username}이 레지스트리 {len(laid.laid)}개의 엔드포인트를 한 번에 바꿈"

    @override
    async def call(
        self, adapter: ReservoirRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateReservoirRegistriesInput(
                    items=[
                        PartialBulkUpdateReservoirRegistryItemInput(
                            id=registry.id,
                            input=UpdateReservoirRegistryBody(endpoint=EDITED_ENDPOINT),
                        )
                        for registry in laid.laid
                    ]
                )
            )


@dataclass(frozen=True)
class AUserGrantedUpdateEditsSeveral(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ReservoirRegistryAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-edits-several-registries"

    @override
    def describe(self) -> str:
        return (
            "레지스트리 수정 권한을 받은 사용자가 여럿의 엔드포인트를 한 번에 바꾸면, 모두 새 엔드포인트로 오고 "
            "실패한 것은 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(granted=(Permission.UPDATE,))

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Edited]:
        return EveryTargetIsEdited()


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ReservoirRegistryAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-registries"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 레지스트리 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Edited]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[EditingStep] = [
    AUserGrantedUpdateEditsSeveral(),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: ReservoirRegistryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
