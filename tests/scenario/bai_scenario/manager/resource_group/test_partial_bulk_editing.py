"""리소스 그룹 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.request import (
    PartialBulkUpdateResourceGroupItemInput,
    PartialBulkUpdateResourceGroupsInput,
    UpdateResourceGroupInput,
)
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.resource_group import (
    EveryGroupIsProcessed,
    GroupLook,
    ManyGroupsAndACaller,
    NoGroupIsProcessed,
    Processed,
    TwoGroupsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = "한 번에 고친 설명"

type EditingStep = Scenario[
    TestSeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Processed
]


@dataclass(frozen=True)
class EditingEveryGroup(When[ManyGroupsAndACaller, ResourceGroupAdapter, Processed]):
    """그룹들의 설명을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyGroupsAndACaller) -> str:
        return f"{laid.caller.username}이 그룹 {len(laid.laid)}개의 설명을 한 번에 고침"

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ManyGroupsAndACaller) -> Processed:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateResourceGroupsInput(
                    items=[
                        PartialBulkUpdateResourceGroupItemInput(
                            id=group.id, input=UpdateResourceGroupInput(description=EDITED)
                        )
                        for group in laid.laid
                    ]
                )
            )


@dataclass(frozen=True)
class TheSuperadminEditsSeveralGroups(
    Scenario[TestSeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Processed]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-resource-groups-at-once"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 그룹 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Processed]:
        return EditingEveryGroup()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Processed]:
        return EveryGroupIsProcessed(GroupLook(started=self.started, described=EDITED))


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Processed]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-resource-groups"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 그룹 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone()

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Processed]:
        return EditingEveryGroup()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Processed]:
        return NoGroupIsProcessed(reason="Insufficient permission")


SCENARIOS: list[EditingStep] = [
    TheSuperadminEditsSeveralGroups(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
