"""What an agent resource scenario table says besides the call.

An agent is created in its resource group, so a caller reads the slot rows it carries
through a role in that group. A table needs the caller, the agent or agents the call
names, and whether the caller holds a read on them.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

from ai.backend.common.data.entity.agent import AgentEntityType, AgentUUID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchAgentResourcesPayload,
    AgentResourceNode,
)
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import Answered, Given, Held, Same, Skipped, Then, Verdict
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.resource_allocation import AmountOf
from bai_scenario.components.system import role_named
from bai_scenario.seeds.agent.agent import TestSeedAgent
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_group.resource_group import TestSeedResourceGroup
from bai_scenario.seeds.resource_slot.agent_resource import TestSeedReportedSlot
from bai_scenario.seeds.resource_slot.slot_type import TestSeedResourceSlotType
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest

CAPACITY_STEP = Decimal(10)
"""슬롯마다 보고하는 용량의 간격. 순위가 앞선 슬롯일수록 작은 용량을 보고한다."""

USED = Decimal(1)
"""보고된 슬롯마다 사용 중인 양. 용량과 구분되도록 용량보다 작은 값을 쓴다."""


@dataclass(frozen=True)
class AnAgent:
    """에이전트 하나. 호출은 이름으로 지정하고, 권한 검사는 uuid로 한다."""

    agent_id: str
    agent_uuid: AgentUUID


@dataclass(frozen=True)
class AnAgentAndACaller:
    """에이전트 하나와, 그것을 호출할 사용자."""

    agent: AnAgent
    caller: UserData


@dataclass(frozen=True)
class TwoAgentsAndACaller:
    """에이전트 둘과, 그중 ``readable``만 읽을 수 있는 사용자."""

    readable: AnAgent
    other: AnAgent
    caller: UserData


@dataclass(frozen=True)
class SomeoneReadingAgentsIn(TestSeedNest[Laid[UserData]]):
    """그 리소스 그룹의 에이전트를 읽을 수 있는 사용자."""

    domain: Laid[DomainData]
    group: Laid[ResourceGroupData]

    @override
    def kind(self) -> str:
        return "리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            TestSeedRole(lambda g: ResourceGroupID(g.id), name_hint="agent-reader"), self.group
        )
        seed.adding(
            TestSeedPermission(entity_type=AgentEntityType(), permission=Permission.READ), role
        )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


@dataclass(frozen=True)
class AnAgentAndSomeone(Given[Any, AnAgentAndACaller]):
    """에이전트 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: bool = False

    @override
    def describe(self) -> str:
        if self.granted:
            return f"에이전트 하나와, 그것을 읽을 수 있는 {role_named(self.role)} 한 명"
        return f"에이전트 하나와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> AnAgentAndACaller:
        group = await seeding.creating(TestSeedResourceGroup())
        agent = await seeding.creating_from(TestSeedAgent(), group)
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        if self.granted:
            caller = await seeding.within(SomeoneReadingAgentsIn(home, group))
        else:
            caller = await seeding.within(SomeoneOf(home, role=self.role))
        return AnAgentAndACaller(
            agent=AnAgent(agent_id=agent.name, agent_uuid=seeding.made(agent)),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TwoAgentsAndSomeoneReadingOne(Given[Any, TwoAgentsAndACaller]):
    """리소스 그룹이 다른 에이전트 둘과, 한쪽 그룹의 에이전트만 읽을 수 있는 사용자 한 명."""

    @override
    def describe(self) -> str:
        return "리소스 그룹이 다른 에이전트 둘과, 한쪽 그룹의 에이전트만 읽을 수 있는 일반 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> TwoAgentsAndACaller:
        mine = await seeding.creating(TestSeedResourceGroup(name_hint="mine"))
        readable = await seeding.creating_from(TestSeedAgent(name_hint="readable"), mine)
        elsewhere = await seeding.creating(TestSeedResourceGroup(name_hint="elsewhere"))
        other = await seeding.creating_from(TestSeedAgent(name_hint="other"), elsewhere)
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneReadingAgentsIn(home, mine))
        return TwoAgentsAndACaller(
            readable=AnAgent(agent_id=readable.name, agent_uuid=seeding.made(readable)),
            other=AnAgent(agent_id=other.name, agent_uuid=seeding.made(other)),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ASlot:
    """미리 만들어 둔 슬롯 종류 하나와, 모든 에이전트가 그 슬롯에 보고한 용량."""

    name: str
    capacity: Decimal


@dataclass(frozen=True)
class ReportedSlotsAndACaller:
    """미리 만들어 둔 에이전트들과 슬롯들, 그리고 호출할 사용자.

    모든 에이전트가 모든 슬롯을 보고한다. 둘 다 만든 순서대로 담고, 슬롯은 그 순서가 순위다.
    """

    agents: tuple[AnAgent, ...]
    slots: tuple[ASlot, ...]
    caller: UserData


@dataclass(frozen=True)
class AgentsReportingSlots(Given[Any, ReportedSlotsAndACaller]):
    """같은 리소스 그룹에서 같은 슬롯들을 보고한 에이전트 여럿과 사용자 한 명."""

    agents: int = 1
    slots: int = 1
    role: UserRole = UserRole.SUPERADMIN
    granted: bool = False

    @override
    def describe(self) -> str:
        caller = f"{role_named(self.role)} 한 명"
        if self.granted:
            caller = f"에이전트를 읽을 수 있는 {caller}"
        if self.agents == 1:
            return f"슬롯 {self.slots}개를 보고한 에이전트 1개와, {caller}"
        return f"슬롯 {self.slots}개씩 보고한 에이전트 {self.agents}개와, {caller}"

    @override
    async def lay(self, seeding: Any) -> ReportedSlotsAndACaller:
        slots: list[ASlot] = []
        for rank in range(self.slots):
            slot_type = await seeding.creating(
                TestSeedResourceSlotType(name_hint="slot", rank=rank)
            )
            slots.append(ASlot(name=slot_type.name, capacity=CAPACITY_STEP * (rank + 1)))
        group = await seeding.creating(TestSeedResourceGroup())
        agents: list[AnAgent] = []
        for _ in range(self.agents):
            agent = await seeding.creating_from(TestSeedAgent(), group)
            for slot in slots:
                await seeding.adding(
                    TestSeedReportedSlot(
                        agent_id=agent.name,
                        slot_name=slot.name,
                        capacity=slot.capacity,
                        used=USED,
                    ),
                    agent,
                )
            agents.append(AnAgent(agent_id=agent.name, agent_uuid=seeding.made(agent)))
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        if self.granted:
            caller = await seeding.within(SomeoneReadingAgentsIn(home, group))
        else:
            caller = await seeding.within(SomeoneOf(home, role=self.role))
        return ReportedSlotsAndACaller(
            agents=tuple(agents), slots=tuple(slots), caller=seeding.made(caller)
        )


@dataclass(frozen=True)
class Reported:
    """미리 만들어 둔 에이전트 하나가 보고한 슬롯 하나. 둘 다 만든 순서로 가리킨다."""

    agent: int
    slot: int


def reported_slot_verdicts(
    at: str, node: AgentResourceNode, agent: AnAgent, slot: ASlot
) -> list[Verdict]:
    """Every place of one agent resource node."""
    return [
        Same(f"{at}id", node.id, f"{agent.agent_id}:{slot.name}"),
        Skipped(f"{at}field_id", "데이터베이스가 만든다"),
        Same(f"{at}agent_id", node.agent_id, agent.agent_id),
        Same(f"{at}slot_name", node.slot_name, slot.name),
        Held(f"{at}capacity", node.capacity, AmountOf(slot.capacity)),
        Held(f"{at}used", node.used, AmountOf(USED)),
    ]


def reported_page_verdicts(
    page: AdminSearchAgentResourcesPayload,
    nodes: list[AgentResourceNode],
    wanted: list[tuple[AnAgent, ASlot]],
    *,
    total_count: int,
    has_next_page: bool,
) -> list[Verdict]:
    """Every place of one page, its nodes matched against ``wanted`` in the given order."""
    seen: list[Verdict] = [Same("len(items)", len(nodes), len(wanted))]
    for i, (node, (agent, slot)) in enumerate(zip(nodes, wanted, strict=False)):
        seen.extend(reported_slot_verdicts(f"items[{i}].", node, agent, slot))
    seen.extend([
        Same("total_count", page.total_count, total_count),
        Same("has_next_page", page.has_next_page, has_next_page),
        Same("has_previous_page", page.has_previous_page, False),
    ])
    return seen


@dataclass(frozen=True)
class TheReportedSlot(Then[ReportedSlotsAndACaller, AgentResourceNode]):
    """에이전트가 보고한 슬롯 하나가 통째로 반환된다."""

    row: Reported

    @override
    def says(self) -> str:
        return "보고된 슬롯 행 전체가 반환된다"

    @override
    def look(
        self, laid: ReportedSlotsAndACaller, answered: Answered[AgentResourceNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return reported_slot_verdicts(
            "", node, laid.agents[self.row.agent], laid.slots[self.row.slot]
        )


@dataclass(frozen=True)
class TheReportedSlots(Then[ReportedSlotsAndACaller, AdminSearchAgentResourcesPayload]):
    """이 슬롯 행들이 통째로 반환된다. ``in_order``가 아니면 반환 순서는 보지 않는다."""

    rows: tuple[Reported, ...]
    in_order: bool = True

    @override
    def says(self) -> str:
        if self.in_order:
            return "보고된 슬롯 행 전체가 이 순서대로 반환된다"
        return "보고된 슬롯 행 전체가 반환된다"

    @override
    def look(
        self,
        laid: ReportedSlotsAndACaller,
        answered: Answered[AdminSearchAgentResourcesPayload],
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        wanted = [(laid.agents[one.agent], laid.slots[one.slot]) for one in self.rows]
        nodes = list(page.items)
        if not self.in_order:
            wanted.sort(key=lambda pair: (pair[0].agent_id, pair[1].name))
            nodes.sort(key=lambda node: (node.agent_id, node.slot_name))
        return reported_page_verdicts(
            page, nodes, wanted, total_count=len(wanted), has_next_page=False
        )


@dataclass(frozen=True)
class TheFirstReportedSlots(Then[ReportedSlotsAndACaller, AdminSearchAgentResourcesPayload]):
    """정렬을 지정하지 않은 첫 페이지. 슬롯 이름 순서로 앞선 행이 ``size``건 반환되고 다음
    페이지가 있다고 응답한다."""

    size: int

    @override
    def says(self) -> str:
        return "슬롯 이름 순서로 앞선 행 전체가 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def look(
        self,
        laid: ReportedSlotsAndACaller,
        answered: Answered[AdminSearchAgentResourcesPayload],
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        every = sorted(
            ((agent, slot) for agent in laid.agents for slot in laid.slots),
            key=lambda pair: (pair[1].name, pair[0].agent_id),
        )
        return reported_page_verdicts(
            page,
            list(page.items),
            every[: self.size],
            total_count=len(every),
            has_next_page=True,
        )
