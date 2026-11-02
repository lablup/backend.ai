"""리소스 그룹 여럿 완전 삭제."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.request import (
    PartialBulkPurgeResourceGroupsInput,
)
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
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

type PurgingStep = Scenario[
    TestSeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Processed
]


@dataclass(frozen=True)
class PurgingEveryGroup(When[ManyGroupsAndACaller, ResourceGroupAdapter, Processed]):
    """그룹들을 한 번에 완전 삭제한다. ``missing``이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyGroupsAndACaller) -> str:
        if self.missing is not None:
            besides_ko = " 와 없는 id 하나"
            besides_en = " and one unknown id"
        else:
            besides_ko = ""
            besides_en = ""
        return Says(
            f"{laid.caller.username}이 자원 그룹 {len(laid.laid)}개{besides_ko}를 한 번에 "
            "완전 삭제합니다",
            english=(
                f"{laid.caller.username} purges {len(laid.laid)} resource groups{besides_en} "
                "at once"
            ),
        )

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ManyGroupsAndACaller) -> Processed:
        ids: list[UUID] = [group.id for group in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(PartialBulkPurgeResourceGroupsInput(ids=ids))


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Processed]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-resource-groups-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 자원 그룹 둘과 없는 id 하나를 한 번에 완전 삭제하면, 둘은 삭제한 그대로 "
            "오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when the superadmin purges two resource groups and one unknown id at once, the "
                "two come back as deleted and the unknown id comes back in the failed list "
                "because no target answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Processed]:
        return PurgingEveryGroup(missing=self.missing)

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Processed]:
        return EveryGroupIsProcessed(GroupLook(started=self.started), missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Processed]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-resource-groups"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자원 그룹 여럿을 한 번에 완전 삭제하려 하면, 지워진 "
            "것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "a user granted nothing trying to purge several resource groups at once gets "
                "none purged and every one in the failed list for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone()

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Processed]:
        return PurgingEveryGroup()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Processed]:
        return NoGroupIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    PurgingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
