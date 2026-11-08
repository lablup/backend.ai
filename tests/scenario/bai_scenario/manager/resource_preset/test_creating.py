"""리소스 프리셋 생성 — 전역 검사만 통과한 호출이 무엇을 만드는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import BinarySizeInfo, ResourceSlotEntryInfo
from ai.backend.common.dto.manager.v2.resource_preset.response import (
    CreateResourcePresetPayload,
    ResourcePresetNode,
)
from ai.backend.common.exception import ResourcePresetConflict
from ai.backend.manager.api.adapters.resource_preset.adapter import ResourcePresetAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.resource_preset import (
    AGroupAndACaller,
    AGroupAndSomeone,
    APresetAndACaller,
    APresetAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.resource_preset.preset import SLOTS

CREATED = "fresh-preset"
SHARED_MEMORY = 1073741824

type Created = ResourcePresetNode

type CreatingStep = (
    Scenario[TestSeedingSession, AGroupAndACaller, ResourcePresetAdapter, Created]
    | Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, Created]
)


@dataclass(frozen=True)
class Creating(When[AGroupAndACaller, ResourcePresetAdapter, Created]):
    """프리셋을 만든다. ``in_group``이면 미리 만들어 둔 자원 그룹에 묶는다."""

    in_group: bool = False

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        where_ko = (
            f"자원 그룹 {laid.group.name}에 묶어"
            if self.in_group
            else "어느 자원 그룹에도 묶지 않고"
        )
        where_en = (
            f"bound to the resource group {laid.group.name}"
            if self.in_group
            else "bound to no resource group"
        )
        return Says(
            f"{laid.caller.username}이 {where_ko} 프리셋 {CREATED}을 만듭니다",
            english=f"{laid.caller.username} creates the preset {CREATED} {where_en}",
        )

    @override
    async def call(self, adapter: ResourcePresetAdapter, laid: AGroupAndACaller) -> Created:
        with ActingAs(laid.caller):
            payload: CreateResourcePresetPayload = await adapter.create(
                name=CREATED,
                resource_slots=SLOTS,
                shared_memory=SHARED_MEMORY,
                resource_group_name=laid.group.name if self.in_group else None,
            )
        return payload.resource_preset


@dataclass(frozen=True)
class CreatingWithATakenName(When[APresetAndACaller, ResourcePresetAdapter, Created]):
    """이미 있는 프리셋의 이름으로, 어느 자원 그룹에도 묶지 않고 프리셋을 만든다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 이미 있는 이름 {laid.preset.name}으로 프리셋을 만듭니다",
            english=(
                f"{laid.caller.username} creates a preset with the name {laid.preset.name} that "
                "another preset already holds"
            ),
        )

    @override
    async def call(self, adapter: ResourcePresetAdapter, laid: APresetAndACaller) -> Created:
        with ActingAs(laid.caller):
            payload: CreateResourcePresetPayload = await adapter.create(
                name=laid.preset.name,
                resource_slots=SLOTS,
                shared_memory=SHARED_MEMORY,
                resource_group_name=None,
            )
        return payload.resource_preset


@dataclass(frozen=True)
class ThePresetJustCreated(Then[AGroupAndACaller, Created]):
    """방금 만든 프리셋 전체가 온다."""

    in_group: bool = False

    @override
    def says(self) -> str:
        return Says(
            "방금 만든 프리셋 전체가 응답으로 옵니다",
            english="the whole preset just created comes back",
        )

    @override
    def look(self, laid: AGroupAndACaller, answered: Answered[Created]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return [
            Skipped("id", "the database generates it"),
            Skipped("entity_id", "the database generates it"),
            Same("name", node.name, CREATED),
            Same(
                "resource_slots",
                sorted(node.resource_slots, key=lambda entry: entry.resource_type),
                sorted(
                    (ResourceSlotEntryInfo(resource_type=k, quantity=v) for k, v in SLOTS.items()),
                    key=lambda entry: entry.resource_type,
                ),
            ),
            Same(
                "shared_memory",
                node.shared_memory,
                BinarySizeInfo(expr=str(SHARED_MEMORY), display="1g"),
            ),
            Same(
                "resource_group_name",
                node.resource_group_name,
                laid.group.name if self.in_group else None,
            ),
        ]


@dataclass(frozen=True)
class ANameAnotherPresetHoldsIsRefused(
    Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, Created]
):
    @override
    def summary(self) -> str:
        return "creating-a-preset-name-another-preset-holds-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 이미 있는 프리셋의 이름으로 프리셋을 만들면 이름이 겹친다는 것으로 "
            "거부됩니다",
            english=(
                "when the superadmin creates a preset with the name another preset already holds, "
                "the call is rejected as a duplicate name"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, ResourcePresetAdapter, Created]:
        return CreatingWithATakenName()

    @override
    def then(self) -> Then[APresetAndACaller, Created]:
        return TheCallIsRefused(ResourcePresetConflict)


@dataclass(frozen=True)
class TheSuperadminCreatesAPresetInAGroup(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourcePresetAdapter, Created]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-creates-a-preset-bound-to-a-resource-group"

    @override
    def describe(self) -> Says:
        return Says(
            "superadmin 이 미리 만들어 둔 자원 그룹에 묶어 프리셋을 만들면, 그 그룹 이름을 가진 "
            "프리셋 전체가 반환됩니다. 이 호출은 superadmin 역할이 막습니다",
            english=(
                "when the superadmin creates a preset bound to a resource group, the whole preset "
                "comes back naming that group. the superadmin role gates this call"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourcePresetAdapter, Created]:
        return Creating(in_group=True)

    @override
    def then(self) -> Then[AGroupAndACaller, Created]:
        return ThePresetJustCreated(in_group=True)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotCreate(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourcePresetAdapter, Created]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-preset"

    @override
    def describe(self) -> Says:
        return Says(
            "superadmin 이 아닌 사용자가 프리셋을 만들려 하면 역할이 없다는 것으로 거부됩니다",
            english=(
                "a user who is not the superadmin creating a preset is rejected for lacking the "
                "role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[AGroupAndACaller, ResourcePresetAdapter, Created]:
        return Creating()

    @override
    def then(self) -> Then[AGroupAndACaller, Created]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminCreatesAPresetInAGroup(),
    ANameAnotherPresetHoldsIsRefused(),
    AUserWhoIsNotTheSuperadminMayNotCreate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: ResourcePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
