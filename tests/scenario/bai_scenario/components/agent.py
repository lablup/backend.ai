"""What an agent scenario table says besides the call.

An agent lives in its resource group, so a caller reaches it through a role in that
group. A table needs the agents, the slots they report, and the caller who holds the
read. A search and a total are answered for the whole cluster, so those rows run as the
superadmin.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, override

from ai.backend.common.data.entity.agent import AgentEntityType, AgentUUID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.agent.response import (
    AdminSearchAgentsPayload,
    AgentNode,
    UpdateAgentResourceGroupPayload,
)
from ai.backend.common.resource.types import TotalResourceData
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Language,
    Refused,
    Same,
    SameAs,
    Says,
    Then,
    Verdict,
    in_language,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.resource_allocation import lay_a_place
from bai_scenario.components.system import role_named
from bai_scenario.seeds.agent.agent import TestSeedAgent
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_group.resource_group import TestSeedResourceGroup
from bai_scenario.seeds.resource_slot.agent_resource import TestSeedReportedSlot
from bai_scenario.seeds.resource_slot.slot_type import TestSeedResourceSlotType
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.session.session import TestSeedDesignatedAgentOf, TestSeedSession

REGION = "local"
"""시드가 에이전트를 등록할 때 적는 지역."""
VERSION = "0.0.0"
"""시드가 에이전트를 등록할 때 적는 버전."""
ARCHITECTURE = "x86_64"
"""시드가 에이전트를 등록할 때 적는 아키텍처."""
ADDR_TEMPLATE = "tcp://{agent_id}:6001"
"""시드가 에이전트의 주소로 적는 값."""
UNKNOWN_AGENT = "no-such-agent"
"""어떤 에이전트도 갖지 않은 이름."""

READ_ATTRIBUTE = "read_attribute"
"""RBAC READ 가 에이전트 권한으로 옮겨진 이름."""
SUPERADMIN_PERMISSIONS = (
    "read_attribute",
    "update_attribute",
    "create_compute_session",
    "create_service",
)
"""에이전트에 붙는 권한 전부. superadmin 은 모든 비트를 쥐어 이 넷이 된다."""


@dataclass(frozen=True)
class AnAgent:
    """에이전트 하나. 호출은 이름으로 지정하고, 권한 검사는 uuid 로 한다."""

    agent_id: str
    uuid: AgentUUID
    group: ResourceGroupData


@dataclass(frozen=True)
class ASlot:
    """에이전트가 보고한 슬롯 하나."""

    name: str
    capacity: Decimal
    used: Decimal


@dataclass(frozen=True)
class AgentsAndACaller:
    """호출자가 읽을 수 있는 에이전트들, 읽을 수 없는 에이전트들, 그들이 보고한 슬롯과 호출자."""

    agents: tuple[AnAgent, ...]
    unreadable: tuple[AnAgent, ...]
    slots: tuple[ASlot, ...]
    caller: UserData


@dataclass(frozen=True)
class SomeoneReadingAgentsIn(TestSeedNest[Laid[UserData]]):
    """그 리소스 그룹의 에이전트를 읽을 수 있는 사용자."""

    domain: Laid[DomainData]
    group: Laid[ResourceGroupData]

    @override
    def kind(self) -> str:
        return Says(
            "리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비",
            english="Prepare a user granted permission to read agents in the resource group",
        )

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
class AgentsAndSomeone(Given[Any, AgentsAndACaller]):
    """호출자가 읽을 수 있는 에이전트 여럿, 다른 그룹의 에이전트 여럿, 사용자 한 명.

    ``readable``개는 그룹 하나에 있고 ``granted`` 면 호출자가 그 그룹의 에이전트를 읽는다.
    ``elsewhere``개는 다른 그룹에 있다. ``slots``는 에이전트마다 보고할 슬롯의 (용량, 사용량)이다.
    """

    readable: int = 1
    elsewhere: int = 0
    slots: tuple[tuple[Decimal, Decimal], ...] = ()
    role: UserRole = UserRole.USER
    granted: bool = False

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        who_ko = str(who)
        who_en = in_language(who, Language.ENGLISH)
        if self.granted:
            who_ko = f"그 그룹의 에이전트를 읽을 수 있는 {who_ko}"
            who_en = f"the {who_en} granted permission to read the agents of the group"
        parts_ko = [f"에이전트 {self.readable}개"]
        parts_en = [f"{self.readable} agents"]
        if self.slots:
            parts_ko.append(f"에이전트마다 슬롯 {len(self.slots)}개를 보고하고")
            parts_en.append(f"each reporting {len(self.slots)} slots")
        if self.elsewhere:
            parts_ko.append(f"다른 그룹의 에이전트 {self.elsewhere}개")
            parts_en.append(f"{self.elsewhere} agents in another group")
        return Says(
            f"{', '.join(parts_ko)}와, {who_ko} 한 명",
            english=f"{', '.join(parts_en)} and one {who_en}",
        )

    @override
    async def lay(self, seeding: Any) -> AgentsAndACaller:
        group = await seeding.creating(TestSeedResourceGroup(name_hint="mine"))
        slot_types = [
            await seeding.creating(TestSeedResourceSlotType(name_hint="slot", rank=rank))
            for rank in range(len(self.slots))
        ]
        slots = tuple(
            ASlot(name=slot_type.name, capacity=capacity, used=used)
            for slot_type, (capacity, used) in zip(slot_types, self.slots, strict=True)
        )
        agents: list[AnAgent] = []
        for _ in range(self.readable):
            agent = await seeding.creating_from(TestSeedAgent(), group)
            for slot in slots:
                await seeding.adding(
                    TestSeedReportedSlot(
                        agent_id=agent.name, slot_name=slot.name,
                        capacity=slot.capacity, used=slot.used,
                    ),
                    agent,
                )
            agents.append(
                AnAgent(agent_id=agent.name, uuid=seeding.made(agent), group=seeding.made(group))
            )
        elsewhere: list[AnAgent] = []
        if self.elsewhere:
            other = await seeding.creating(TestSeedResourceGroup(name_hint="elsewhere"))
            for _ in range(self.elsewhere):
                agent = await seeding.creating_from(TestSeedAgent(), other)
                elsewhere.append(
                    AnAgent(
                        agent_id=agent.name, uuid=seeding.made(agent), group=seeding.made(other)
                    )
                )
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = (
            await seeding.within(SomeoneReadingAgentsIn(home, group))
            if self.granted
            else await seeding.within(SomeoneOf(home, role=self.role))
        )
        return AgentsAndACaller(
            agents=tuple(agents),
            unreadable=tuple(elsewhere),
            slots=slots,
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AnAgentToMoveAndACaller:
    """옮길 에이전트 하나, 옮길 곳, 그 에이전트를 지정한 다른 그룹의 세션과 호출자."""

    agent: AnAgent
    target: ResourceGroupData
    conflicting: SessionEntityData | None
    caller: UserData


@dataclass(frozen=True)
class AnAgentToMoveAndSomeone(Given[Any, AnAgentToMoveAndACaller]):
    """옮길 에이전트 하나와 옮길 곳, 사용자 한 명.

    ``conflicting`` 이면 그 에이전트를 지정한, 다른 리소스 그룹의 세션이 하나 있다.
    """

    role: UserRole = UserRole.SUPERADMIN
    conflicting: bool = False

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        who_en = in_language(who, Language.ENGLISH)
        if self.conflicting:
            return Says(
                f"다른 그룹의 세션이 지정한 에이전트 하나와 옮길 그룹, 그리고 {who} 한 명",
                english=(
                    "one agent designated by a session of another group, a group to move it "
                    f"to, and one {who_en}"
                ),
            )
        return Says(
            f"에이전트 하나와 옮길 그룹, 그리고 {who} 한 명",
            english=f"one agent, a group to move it to, and one {who_en}",
        )

    @override
    async def lay(self, seeding: Any) -> AnAgentToMoveAndACaller:
        group = await seeding.creating(TestSeedResourceGroup(name_hint="before"))
        agent = await seeding.creating_from(TestSeedAgent(), group)
        target = await seeding.creating(TestSeedResourceGroup(name_hint="after"))
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        conflicting: SessionEntityData | None = None
        if self.conflicting:
            place = await lay_a_place(seeding, slots=0)
            session = await seeding.creating_from_three(
                TestSeedSession(access_key=place.access_key),
                place.project,
                place.owner,
                group,
            )
            await seeding.adding(
                TestSeedDesignatedAgentOf(agent_uuid=seeding.made(agent)), session
            )
            conflicting = seeding.made(session)
        return AnAgentToMoveAndACaller(
            agent=AnAgent(agent_id=agent.name, uuid=seeding.made(agent), group=seeding.made(group)),
            target=seeding.made(target),
            conflicting=conflicting,
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AgentLook:
    """에이전트 노드가 어떤 값으로 와야 하는지. 값은 미리 등록한 에이전트에서 읽는다."""

    started: datetime
    permissions: tuple[str, ...]

    def verdicts(self, prefix: str, node: AgentNode, agent: AnAgent, slots: tuple[ASlot, ...]) -> list[Verdict]:
        written = WrittenByThisRun(self.started)
        capacity = {slot.name: str(slot.capacity) for slot in slots}
        used = {slot.name: str(slot.used) for slot in slots}
        free = {slot.name: str(slot.capacity - slot.used) for slot in slots}
        return [
            Same(f"{prefix}id", node.id, agent.agent_id),
            Held(
                f"{prefix}entity_id",
                node.entity_id,
                SameAs(
                    agent.uuid,
                    Says("미리 등록한 에이전트의 id", english="the id of the agent laid in advance"),
                ),
            ),
            Held(
                f"{prefix}uuid",
                node.uuid,
                SameAs(
                    agent.uuid,
                    Says("미리 등록한 에이전트의 id", english="the id of the agent laid in advance"),
                ),
            ),
            Same(f"{prefix}capacity", node.resource_info.capacity, capacity),
            Same(f"{prefix}used", node.resource_info.used, used),
            Same(f"{prefix}free", node.resource_info.free, free),
            Same(f"{prefix}status", node.status_info.status, AgentStatus.ALIVE.name),
            Same(f"{prefix}status_changed", node.status_info.status_changed, None),
            Held(f"{prefix}first_contact", node.status_info.first_contact, written),
            Same(f"{prefix}lost_at", node.status_info.lost_at, None),
            Same(f"{prefix}schedulable", node.status_info.schedulable, True),
            Same(f"{prefix}architecture", node.system_info.architecture, ARCHITECTURE),
            Same(f"{prefix}version", node.system_info.version, VERSION),
            Same(
                f"{prefix}auto_terminate_abusing_kernel",
                node.system_info.auto_terminate_abusing_kernel,
                False,
            ),
            Same(f"{prefix}compute_plugins", node.system_info.compute_plugins, None),
            Same(f"{prefix}region", node.network_info.region, REGION),
            Same(
                f"{prefix}addr",
                node.network_info.addr,
                ADDR_TEMPLATE.format(agent_id=agent.agent_id),
            ),
            Same(f"{prefix}scaling_group", node.scaling_group, agent.group.name),
            Same(f"{prefix}permissions", node.permissions, list(self.permissions)),
        ]


@dataclass(frozen=True)
class TheAgentNode(Then[AgentsAndACaller, AgentNode]):
    """미리 등록한 에이전트가 통째로 온다."""

    started: datetime
    the_agent: int = 0
    permissions: tuple[str, ...] = (READ_ATTRIBUTE,)

    @override
    def says(self) -> str:
        return Says(
            "미리 등록한 에이전트 전체가 응답으로 옵니다",
            english="the whole agent registered in advance comes back",
        )

    @override
    def look(self, laid: AgentsAndACaller, answered: Answered[AgentNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return AgentLook(self.started, self.permissions).verdicts(
            "", node, laid.agents[self.the_agent], laid.slots
        )


@dataclass(frozen=True)
class TheAgentsComeBackInOrder(Then[AgentsAndACaller, list[AgentNode | Exception | None]]):
    """미리 등록한 에이전트가 입력 순서대로 노드로 온다.

    ``unknown`` 이면 마지막 자리에 없는 이름을 붙인다. ``denied_after`` 개까지는 읽을 수 있고,
    그 뒤의 에이전트 자리는 권한 부족 예외로 온다.
    """

    started: datetime
    permissions: tuple[str, ...] = (READ_ATTRIBUTE,)
    unknown: bool = False
    unknown_denied: bool = False
    denied_after: int | None = None

    @override
    def says(self) -> str:
        if self.unknown and self.unknown_denied:
            return Says(
                "미리 등록한 에이전트는 입력 순서대로 노드로, 없는 id 자리는 권한 부족으로 옵니다",
                english=(
                    "the agents registered in advance come back as nodes in input order and "
                    "the unknown id entry is rejected for lack of permission"
                ),
            )
        if self.unknown:
            return Says(
                "미리 등록한 에이전트는 입력 순서대로 노드로, 없는 이름 자리는 빈 값으로 옵니다",
                english=(
                    "the agents registered in advance come back as nodes in input order and "
                    "the unknown name entry as an empty value"
                ),
            )
        if self.denied_after is not None:
            return Says(
                "읽을 수 있는 에이전트는 노드로, 나머지 자리는 권한 부족으로 옵니다",
                english=(
                    "the agents the caller may read come back as nodes and the rest of the "
                    "entries are rejected for lack of permission"
                ),
            )
        return Says(
            "미리 등록한 에이전트가 입력 순서대로 노드로 옵니다",
            english="the agents registered in advance come back as nodes in input order",
        )

    @override
    def look(
        self, laid: AgentsAndACaller, answered: Answered[list[AgentNode | Exception | None]]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        laid_agents = (*laid.agents, *laid.unreadable)
        expected = len(laid_agents) + (1 if self.unknown else 0)
        verdicts: list[Verdict] = [Same("length", len(loaded), expected)]
        if len(loaded) != expected:
            return verdicts
        for i, agent in enumerate(laid_agents):
            item = loaded[i]
            if self.denied_after is not None and i >= self.denied_after:
                verdicts.append(
                    Refused(
                        NotEnoughPermission, item if isinstance(item, Exception) else None
                    )
                )
                continue
            if isinstance(item, AgentNode):
                verdicts += AgentLook(self.started, self.permissions).verdicts(
                    f"[{i}].", item, agent, laid.slots
                )
            else:
                verdicts.append(Same(f"[{i}]", type(item).__name__, "AgentNode"))
        if self.unknown:
            if self.unknown_denied:
                last = loaded[-1]
                verdicts.append(
                    Refused(
                        NotEnoughPermission, last if isinstance(last, Exception) else None
                    )
                )
            else:
                verdicts.append(Same(f"[{len(laid_agents)}]", loaded[-1], None))
        return verdicts


@dataclass(frozen=True)
class TheContainerCountsComeBack(Then[AgentsAndACaller, list[int | Exception]]):
    """에이전트마다 컨테이너 수가 입력 순서대로 온다. ``unknown`` 이면 마지막 자리는 0 이다.

    ``denied`` 이면 첫 에이전트 자리가 권한 부족 예외로 온다.
    """

    unknown: bool = False
    denied: bool = False

    @override
    def says(self) -> str:
        if self.unknown:
            return Says(
                "읽을 수 있는 에이전트의 수는 0 으로, 없는 이름 자리도 0 으로 옵니다",
                english=(
                    "the count comes back as zero for the agents the caller may read and for "
                    "the unknown name entry"
                ),
            )
        if self.denied:
            return Says(
                "읽을 수 없는 에이전트 자리는 권한 부족으로 옵니다",
                english="the entry of an agent the caller may not read is rejected for lack of permission",
            )
        return Says(
            "에이전트마다 컨테이너 수가 입력 순서대로 옵니다",
            english="the container count of each agent comes back in input order",
        )

    @override
    def look(
        self, laid: AgentsAndACaller, answered: Answered[list[int | Exception]]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        if self.denied:
            first = loaded[0] if loaded else None
            return [
                Same("length", len(loaded), 1),
                Refused(
                    NotEnoughPermission, first if isinstance(first, Exception) else None
                ),
            ]
        expected = len(laid.agents) + (1 if self.unknown else 0)
        verdicts: list[Verdict] = [Same("length", len(loaded), expected)]
        if len(loaded) != expected:
            return verdicts
        for i in range(len(laid.agents)):
            verdicts.append(Same(f"[{i}]", loaded[i], 0))
        if self.unknown:
            verdicts.append(Same(f"[{len(laid.agents)}]", loaded[-1], 0))
        return verdicts


@dataclass(frozen=True)
class TheWholeAgentPage(Then[AgentsAndACaller, AdminSearchAgentsPayload]):
    """미리 등록한 에이전트가 통째로 온다. ``picked`` 는 그중 골라질 것으로 보는 자리들이다."""

    started: datetime
    picked: tuple[int, ...]
    permissions: tuple[str, ...] = ()

    @override
    def says(self) -> str:
        return Says(
            f"미리 등록한 에이전트 {len(self.picked)}개가 통째로 옵니다",
            english=f"the {len(self.picked)} agents registered in advance come back whole",
        )

    @override
    def look(
        self, laid: AgentsAndACaller, answered: Answered[AdminSearchAgentsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        every = (*laid.agents, *laid.unreadable)
        verdicts: list[Verdict] = [
            Same("items count", len(page.items), len(self.picked)),
            Same("total_count", page.total_count, len(self.picked)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
        by_id = {node.id: node for node in page.items}
        for i, at in enumerate(self.picked):
            agent = every[at]
            node = by_id.get(agent.agent_id)
            verdicts.append(Same(f"items[{i}].present", node is not None, True))
            if node is None:
                continue
            verdicts += AgentLook(self.started, self.permissions).verdicts(
                f"items[{i}].", node, agent, laid.slots
            )
        return verdicts


@dataclass(frozen=True)
class TheAgentMoved(Then[AnAgentToMoveAndACaller, UpdateAgentResourceGroupPayload]):
    """바뀐 그룹을 담은 응답이 온다. 충돌 세션은 세지 않는다."""

    policy: str

    @override
    def says(self) -> str:
        return Says(
            "바뀐 리소스 그룹을 담은 응답이 옵니다",
            english="the answer carrying the new resource group comes back",
        )

    @override
    def look(
        self,
        laid: AnAgentToMoveAndACaller,
        answered: Answered[UpdateAgentResourceGroupPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("agent_id", payload.agent_id, laid.agent.agent_id),
            Held(
                "resource_group_id",
                payload.resource_group_id,
                SameAs(
                    laid.target.id,
                    Says(
                        "미리 만든 옮길 그룹의 id",
                        english="the id of the group laid in advance to move to",
                    ),
                ),
            ),
            Same("policy", payload.policy.value, self.policy),
            Same("conflicting_session_ids", payload.conflicting_session_ids, []),
            Same("terminating_session_ids", payload.terminating_session_ids, []),
        ]


@dataclass(frozen=True)
class TheTotalResources(Then[AgentsAndACaller, TotalResourceData]):
    """미리 등록한 에이전트가 보고한 슬롯의 합이 온다."""

    @override
    def says(self) -> str:
        return Says(
            "에이전트가 보고한 슬롯의 합이 옵니다",
            english="the sum of the slots the agents report comes back",
        )

    @override
    def look(self, laid: AgentsAndACaller, answered: Answered[TotalResourceData]) -> list[Verdict]:
        total = answered.response
        if total is None:
            return [MissingResponse(answered.raised)]
        capacity = {slot.name: str(slot.capacity * len(laid.agents)) for slot in laid.slots}
        used = {slot.name: str(slot.used * len(laid.agents)) for slot in laid.slots}
        free = {
            slot.name: str((slot.capacity - slot.used) * len(laid.agents)) for slot in laid.slots
        }
        return [
            Same("total_capacity_slots", total.total_capacity_slots.to_json(), capacity),
            Same("total_used_slots", total.total_used_slots.to_json(), used),
            Same("total_free_slots", total.total_free_slots.to_json(), free),
        ]
