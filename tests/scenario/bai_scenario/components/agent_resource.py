"""What an agent resource scenario table says besides the call.

An agent is created in its resource group, so a caller reads the slot rows it carries
through a role in that group. A table needs the caller, the agent or agents the call
names, and whether the caller holds a read on them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.agent import AgentEntityType, AgentUUID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import Given
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.system import role_named
from bai_scenario.seeds.agent.agent import SeedAgent
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_group.resource_group import SeedResourceGroup
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest


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
class SomeoneReadingAgentsIn(SeedNest[Laid[UserData]]):
    """그 리소스 그룹의 에이전트를 읽을 수 있는 사용자."""

    domain: Laid[DomainData]
    group: Laid[ResourceGroupData]

    @override
    def kind(self) -> str:
        return "리소스 그룹의 에이전트 조회 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            SeedRole(lambda g: ResourceGroupID(g.id), name_hint="agent-reader"), self.group
        )
        seed.adding(SeedPermission(entity_type=AgentEntityType(), permission=Permission.READ), role)
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
        group = await seeding.creating(SeedResourceGroup())
        agent = await seeding.creating_from(SeedAgent(), group)
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
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
        mine = await seeding.creating(SeedResourceGroup(name_hint="mine"))
        readable = await seeding.creating_from(SeedAgent(name_hint="readable"), mine)
        elsewhere = await seeding.creating(SeedResourceGroup(name_hint="elsewhere"))
        other = await seeding.creating_from(SeedAgent(name_hint="other"), elsewhere)
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneReadingAgentsIn(home, mine))
        return TwoAgentsAndACaller(
            readable=AnAgent(agent_id=readable.name, agent_uuid=seeding.made(readable)),
            other=AnAgent(agent_id=other.name, agent_uuid=seeding.made(other)),
            caller=seeding.made(caller),
        )
