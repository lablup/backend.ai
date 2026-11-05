"""세션을 만들기 전에 자원 그룹의 에이전트에 들어가는지 계산."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

import pytest

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.scheduler.request import (
    ComputeScheduleInput,
    ComputeScheduleKernelResourceInput,
)
from ai.backend.common.dto.manager.v2.scheduler.response import ComputeSchedulePayload
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    NoAgentsInResourceGroupError,
)
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.domain import SomeoneOf
from bai_scenario.components.resource_allocation import lay_a_place
from bai_scenario.components.resource_group import SomeoneGrantedOnTheGroup
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.agent.agent import TestSeedAgent
from bai_scenario.seeds.resource_slot.agent_resource import TestSeedReportedSlot

type Schedule = ComputeSchedulePayload

CAPACITY = Decimal(8)
"""The agent reports this much of the slot the kernel asks for."""


@dataclass(frozen=True)
class LaidGroupAndAgent:
    """자원 그룹 하나, 그 그룹의 이미지와 슬롯, 그리고 그룹에 들어갈 수 있는지 계산할 사용자."""

    domain: DomainData
    group: ResourceGroupData
    image: ImageData
    slot_name: str
    caller: UserData


@dataclass(frozen=True)
class AGroupWithAnAgent(Given[Any, LaidGroupAndAgent]):
    """슬롯 하나를 요구하는 커널을 받을 자원 그룹 하나와 사용자 한 명."""

    with_agent: bool = True
    granted: bool = True

    @override
    def describe(self) -> str:
        if self.with_agent:
            slot_state_ko = "용량을 보고한 에이전트 하나"
            slot_state_en = "an agent reporting capacity"
        else:
            slot_state_ko = "에이전트 없음"
            slot_state_en = "no agent"
        if self.granted:
            reach_ko, reach_en = "그 그룹을 읽을 수 있는", "who can read the group"
        else:
            reach_ko, reach_en = "아무 권한도 받지 않은", "holding no permission"
        return Says(
            f"{slot_state_ko}를 가진 자원 그룹 하나와, {reach_ko} 사용자 한 명",
            english=f"one resource group with {slot_state_en} and one user {reach_en}",
        )

    @override
    async def lay(self, seeding: Any) -> LaidGroupAndAgent:
        place = await lay_a_place(seeding, slots=1)
        slot_name = seeding.made(place.slot_types[0]).slot_name
        if self.with_agent:
            agent = await seeding.creating_from(TestSeedAgent(), place.group)
            await seeding.adding(
                TestSeedReportedSlot(
                    agent_id=agent.name,
                    slot_name=slot_name,
                    capacity=CAPACITY,
                    used=Decimal(0),
                ),
                agent,
            )
        caller = await seeding.within(SomeoneOf(place.domain))
        if self.granted:
            await seeding.within(
                SomeoneGrantedOnTheGroup(place.group, caller, Permission.READ)
            )
        return LaidGroupAndAgent(
            domain=seeding.made(place.domain),
            group=seeding.made(place.group),
            image=seeding.made(place.image),
            slot_name=slot_name,
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ComputingTheSchedule(When[LaidGroupAndAgent, SessionAdapter, Schedule]):
    @override
    def operation(self) -> str:
        return "compute_schedule"

    @override
    def describe(self, laid: LaidGroupAndAgent) -> str:
        return Says(
            f"{laid.caller.username}이 그 자원 그룹에서 슬롯 하나를 요구하는 커널이 들어갈 수 "
            "있는지 계산합니다",
            english=(
                f"{laid.caller.username} computes whether a kernel asking for one slot fits the "
                "resource group"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidGroupAndAgent) -> Schedule:
        with ActingAs(laid.caller):
            return await adapter.compute_schedule(
                ComputeScheduleInput(
                    kernels=[
                        ComputeScheduleKernelResourceInput(
                            image_id=ImageID(laid.image.id),
                            resources=[
                                ResourceSlotEntryInput(
                                    resource_type=laid.slot_name, quantity=str(Decimal(1))
                                )
                            ],
                        )
                    ],
                    cluster_mode=ClusterModeEnum.SINGLE_NODE,
                    resource_group_id=ResourceGroupID(laid.group.id),
                )
            )


@dataclass(frozen=True)
class TheKernelFits(Then[LaidGroupAndAgent, Schedule]):
    @override
    def says(self) -> str:
        return Says(
            "요구한 슬롯과 아키텍처가 그대로 돌아오고, 커널 하나가 들어간다고 답합니다",
            english=(
                "the slots and architecture asked for come back, and the one kernel is answered "
                "as fitting"
            ),
        )

    @override
    def look(self, laid: LaidGroupAndAgent, answered: Answered[Schedule]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        if not payload.results:
            return [Same("results count", 0, 1)]
        result = payload.results[0]
        return [
            Same("results count", len(payload.results), 1),
            Held(
                "requested_slots",
                [entry.model_dump() for entry in result.requested_slots],
                SameAs(
                    [{"resource_type": laid.slot_name, "quantity": Decimal(1)}],
                    Says("요구한 슬롯", english="the slots asked for"),
                ),
            ),
            Same("requested_architecture", result.requested_architecture, "x86_64"),
            Same("success", result.success, True),
            Same("reason_hint", result.reason_hint, None),
        ]


@dataclass(frozen=True)
class ComputingASchedule(
    Scenario[TestSeedingSession, LaidGroupAndAgent, SessionAdapter, Schedule]
):
    with_agent: bool = True
    granted: bool = True

    @override
    def summary(self) -> str:
        reach = "granted" if self.granted else "granted-nothing"
        agent = "with-an-agent" if self.with_agent else "without-an-agent"
        return f"computing-whether-a-kernel-fits-{reach}-{agent}"

    @override
    def describe(self) -> str:
        if not self.granted:
            return Says(
                "그 자원 그룹을 읽을 권한이 없는 사용자가 커널이 들어갈 수 있는지 계산하면, 권한 "
                "부족으로 거부됩니다",
                english=(
                    "when a user who may not read the resource group computes whether a kernel "
                    "fits, the call is rejected for lack of permission"
                ),
            )
        if not self.with_agent:
            return Says(
                "그 자원 그룹을 읽을 수 있는 사용자가 에이전트가 하나도 없는 그룹에 커널이 들어갈 "
                "수 있는지 계산하면, 에이전트가 없어서 거부됩니다",
                english=(
                    "when a user who can read the resource group computes a kernel against a "
                    "group with no agent, the call is rejected because no agent is there"
                ),
            )
        return Says(
            "그 자원 그룹을 읽을 수 있는 사용자가 요구한 슬롯을 감당하는 에이전트가 있는 그룹에 "
            "커널이 들어갈 수 있는지 계산하면, 들어간다고 답합니다",
            english=(
                "when a user who can read the resource group computes a kernel against a group "
                "whose agent holds enough of the slot, the kernel is answered as fitting"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidGroupAndAgent]:
        return AGroupWithAnAgent(with_agent=self.with_agent, granted=self.granted)

    @override
    def when(self) -> When[LaidGroupAndAgent, SessionAdapter, Schedule]:
        return ComputingTheSchedule()

    @override
    def then(self) -> Then[LaidGroupAndAgent, Schedule]:
        if not self.granted:
            return TheCallIsRefused(NotEnoughPermission)
        if not self.with_agent:
            return TheCallIsRefused(NoAgentsInResourceGroupError)
        return TheKernelFits()


SCENARIOS: list[Scenario[Any, Any, Any, Any]] = [
    ComputingASchedule(),
    ComputingASchedule(with_agent=False),
    ComputingASchedule(granted=False),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_computing_schedule(
    scenario: Scenario[Any, Any, Any, Any],
    adapter: SessionAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
